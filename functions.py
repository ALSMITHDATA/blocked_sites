import re
import time
from bs4 import BeautifulSoup
import pandas as pd

from config import PER_PAGE

def has_no_results(html):
    return "No results found." in html

def get_csrf_token(html):
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.find("input", {"name": "_csrf"})
    return token_input["value"] if token_input else None

def extract_record(result):
    # Planning reference
    meta = result.select_one("p.metaInfo")
    ref = None

    if meta:
        meta_text = meta.get_text(" ", strip=True)
        match = re.search(r"Ref\.\s*No:\s*([^\s|]+)", meta_text)

        if match:
            ref = match.group(1)

    # Address
    address_element = result.select_one("p.address")
    address = None
    postcode = None

    if address_element:
        address_text = address_element.get_text(" ", strip=True)

        # UK postcode is at the end of the address
        postcode_match = re.search(
            r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})$",
            address_text,
            re.IGNORECASE
        )

        if postcode_match:
            postcode = postcode_match.group(1).upper()
            address = address_text[:postcode_match.start()].strip()
        else:
            address = address_text

    return {
        "ref": ref,
        "address": address,
        "postcode": postcode,
    }

def extract_records(html):
    soup = BeautifulSoup(html, "html.parser")

    records = []

    for result in soup.select("li.searchresult"):
        record = extract_record(result)

        if record["ref"]:
            records.append(record)

    return records


def post_page(s, base, csrf, page):
    return s.post(
        f"{base}/pagedSearchResults.do",
        data={
            "_csrf": csrf,
            "searchCriteria.page": str(page),
            "action": "page",
            "orderBy": "DateReceived",
            "orderByDirection": "Descending",
            "searchCriteria.resultsPerPage": str(PER_PAGE),
        },
        timeout=15,
    )

def get_all_pages(first_response, s, base):
    all_records = []

    if has_no_results(first_response.text):
        print("Page 1: 0 records (no results found)")
        return all_records

    # The first search response is still at 10 per page, so re-request
    # page 1 via the paging endpoint to get it at PER_PAGE.
    csrf = get_csrf_token(first_response.text)
    if not csrf:
        print("No CSRF token on first response, stopping")
        return all_records

    page = 1
    while True:
        response = post_page(s, base, csrf, page)
        response.raise_for_status()

        records = extract_records(response.text)
        print(f"Page {page}: {len(records)} records")
        if not records:
            break

        all_records.extend(records)

        if len(records) < PER_PAGE:   # last page, so skip the extra request
            break

        csrf = get_csrf_token(response.text)
        if not csrf:
            print(f"No CSRF token on page {page}, stopping")
            break

        page += 1
        time.sleep(1)

    return all_records

#GIS function for fetching polygons:

def fetch_batch(refs, session, layer_url):
    where = "REFVAL IN (" + ",".join("'" + x.replace("'", "''") + "'" for x in refs) + ")"
    resp = session.get(f"{layer_url}/query", params={
        "where": where,
        "outFields": "REFVAL,KEYVAL,DATEMODIFIED,ADDRESS,DESCRIPTION",
        "returnGeometry": "true",
        "outSR": 27700,
        "f": "json",
    }, timeout=60)
    resp.raise_for_status()
    js = resp.json()
    if "error" in js:
        raise RuntimeError(js["error"])
    if js.get("exceededTransferLimit"):
        print("Warning: batch hit the record cap, use smaller batches")
    return js.get("features", [])


#Notes on picking this up:
#The paginated query works to get some records, but the REF query was not retrieving anything.
#I'm not certain if this is because it needs to query a different mapserver layer (for example pre-merger),
#and it may take some time to find this out
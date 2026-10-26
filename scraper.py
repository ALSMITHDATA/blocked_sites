import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from config import BASE_PAYLOAD, CASE_TYPES, DEVELOPMENT_TYPES, PERIODS
from functions import get_all_pages, extract_record, extract_records

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
})

base = "https://publicaccess.buckinghamshire.gov.uk/online-applications"

form_page = s.get(f"{base}/search.do?action=advanced&searchType=Application", timeout=15)

#checks http status code, exception if error
form_page.raise_for_status()

#Pulls the csrf out of the pages
soup = BeautifulSoup(form_page.text, "html.parser")
csrf_input = soup.find("input", {"name": "_csrf"})
csrf_token = csrf_input["value"] if csrf_input else None

#Submit the search using that same session's cookies + toke
s.headers.update({
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://publicaccess.buckinghamshire.gov.uk",
    "Referer": f"{base}/search.do?action=advanced",
})

#Get the data!
all_records = []

for period_name, start_date, end_date in PERIODS:
    for case_type in CASE_TYPES:
        for development_type in DEVELOPMENT_TYPES:

            print(
                f"Searching {period_name}: "
                f"{case_type} / {development_type}"
            )

            payload = BASE_PAYLOAD.copy()

            payload.update({
                "_csrf": csrf_token,
                "searchCriteria.caseType": case_type,
                "searchCriteria.developmentType": development_type,
                "date(applicationValidatedStart)": start_date,
                "date(applicationValidatedEnd)": end_date,
            })

            r = s.post(
                f"{base}/advancedSearchResults.do?action=firstPage",
                data=payload,
                timeout=15,
            )
            r.raise_for_status()
            print("POST status:", r.status_code)
            print( "POST URL:", r.url)
            print("POST length:", len(r.text))
            print("JSESSIONID:", s.cookies.get("JSESSIONID"))
            print(r.text[:1000])

            records = get_all_pages(r, s, base)
            for rec in records:
                rec["period"] = period_name
                rec["case_type"] = case_type
                rec["development_type"] = development_type

            all_records.extend(records)

            time.sleep(1)

df = pd.DataFrame(all_records)
df = df.drop_duplicates(subset="ref")
print(f"Unique applications: {len(df)}")




#Inspection tools:
#Output from this indicates a successful search
print(len(r.text))
print(r.text[:2000])

#Digging for the actual content:
body_start = r.text.lower().find("<body")

#Kick out a text file to the local directory:
with open("response.html", "w", encoding="utf-8") as f:
    f.write(r.text)


#Minimalist test code

import requests
from bs4 import BeautifulSoup

base = "https://publicaccess.buckinghamshire.gov.uk/online-applications"
s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
})

# Step 1: load the search form fresh, get session cookie + CSRF token
form_page = s.get(f"{base}/search.do?action=advanced&searchType=Application", timeout=15)
form_page.raise_for_status()

soup = BeautifulSoup(form_page.text, "html.parser")
csrf_token = soup.find("input", {"name": "_csrf"})["value"]
print("CSRF token:", csrf_token)

# Step 2: build the minimal payload — just description + required hidden fields
payload = {
    "_csrf": csrf_token,
    "searchCriteria.description": "belt",
    "caseAddressType": "Application",
    "searchType": "Application",
}

s.headers.update({
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://publicaccess.buckinghamshire.gov.uk",
    "Referer": f"{base}/search.do?action=advanced",
})

# Step 3: submit the search
r = s.post(f"{base}/advancedSearchResults.do?action=firstPage", data=payload, timeout=15)
r.raise_for_status()

print("Status:", r.status_code, "| Length:", len(r.text))
print("No results?", "No results found." in r.text)

# Step 4: parse results if any
results_soup = BeautifulSoup(r.text, "html.parser")
items = results_soup.select("li.searchresult")
print("Records found on page 1:", len(items))
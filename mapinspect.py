import requests
import pandas as pd, time
from functions import fetch_batch

gis = "https://publicaccess.buckinghamshire.gov.uk/arcgis/rest/services/IDOXPALIVE/MapServer/9"

g = requests.Session()

g.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://publicaccess.buckinghamshire.gov.uk/online-applications/",
})

#This just retrieves a record count and is a standard search, not the GIS specific one. Drop?
g.get("https://publicaccess.buckinghamshire.gov.uk/online-applications/", timeout=15)  # cookies

r = g.get(f"{gis}/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, timeout=30)
print(r.status_code, r.text)

#Apply the fetch_batch function to aforementioned REFs
refs = df["ref"].dropna().unique().tolist()
feats = []
for i in range(0, len(refs), 100):
    feats.extend(fetch_batch(refs[i:i+100]))
    time.sleep(1)

gdf = pd.DataFrame([{**f["attributes"], "rings": f["geometry"]["rings"] if f.get("geometry") else None}
                    for f in feats])

print(len(refs), "refs searched;", len(gdf), "polygons returned")

#Writing out
with open("gis.html", "w", encoding="utf-8") as f:
    f.write(r.text)
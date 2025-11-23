import os
import requests
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY")
EIA_BASE = "https://api.eia.gov/v2"

def debug_request(path, params):
    merged = {"api_key": EIA_API_KEY, **params}
    url = f"{EIA_BASE}/{path}/data/"
    print(f"Requesting: {url}")
    print(f"Params: {json.dumps(merged, indent=2)}")
    try:
        resp = requests.get(url, params=merged, timeout=30)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error Body: {resp.text}")
            return
        
        data = resp.json()
        rows = data.get("response", {}).get("data", [])
        print(f"Rows returned: {len(rows)}")
        if rows:
            print("First row sample:")
            print(json.dumps(rows[0], indent=2))
        else:
            print("Full response:")
            print(json.dumps(data, indent=2))
            
    except Exception as e:
        print(f"Exception: {e}")

print("--- Debugging Demand (Region Data) ---")
end = datetime.now(timezone.utc)
start = end - timedelta(days=2)
debug_request(
    "electricity/rto/region-data",
    {
        "facets[respondent][]": "CISO",
        "frequency": "hourly",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5,
        "data[0]": "value",
    }
)

print("\n--- Debugging Price (Wholesale) ---")
debug_request(
    "electricity/wholesale-markets-data",
    {
        "facets[market][]": "DA",
        "facets[location][]": "TH_NP15",
        "frequency": "hourly",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5,
        "data[0]": "value",
    }
)

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz

# API Endpoint
url = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
    "start=2024-04-22T00:00:00Z&"
    "end=2024-04-24T00:00:00Z&"
    "reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

# PST timezone
pst = pytz.timezone("Asia/Manila")

# Create base EPG structure
tv = ET.Element("tv", attrib={
    "generator-info-name": "Cignal API EPG",
    "generator-info-url": "https://example.com"
})

try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
    response.raise_for_status()
    data = response.json()

    if isinstance(data.get("data"), list):
        for entry in data["data"]:
            if "airing" in entry:
                for program in entry["airing"]:
                    start_utc = datetime.strptime(program["sc_st_dt"], "%Y-%m-%dT%H:%M:%SZ")
                    end_utc = datetime.strptime(program["sc_ed_dt"], "%Y-%m-%dT%H:%M:%SZ")
                    start_pst = start_utc.replace(tzinfo=pytz.utc).astimezone(pst)
                    end_pst = end_utc.replace(tzinfo=pytz.utc).astimezone(pst)

                    title = program.get("pgm", {}).get("lod", [{}])[0].get("n", "No Title")
                    desc = program.get("pgm", {}).get("lon", [{}])[0].get("n", "No Description")

                    # Each programme without channel tag
                    prog = ET.Element("programme", {
                        "start": start_pst.strftime("%Y%m%d%H%M%S %z"),
                        "stop": end_pst.strftime("%Y%m%d%H%M%S %z"),
                        "channel": "unknown"
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc
                    tv.append(prog)
except Exception as e:
    print("Error fetching/parsing EPG data:", e)

# Write to file
tree = ET.ElementTree(tv)
xml_path = "/mnt/data/cignal_epg.xml"
tree.write(xml_path, encoding="utf-8", xml_declaration=True)
xml_path

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Headers - update these as needed
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CignalEPG/1.0; +https://yourdomain.com)",
    "Accept": "application/json",
    # "Authorization": "Bearer YOUR_AUTH_TOKEN",  # Uncomment if auth is required
}

# Time range for the EPG data
start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

EPG_URL = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    f"?start={start.isoformat()}Z"
    f"&end={end.isoformat()}Z"
    "&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

# Sample channel list - replace this with your actual list or parse from XML
channels = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975",
}

# Create XML root
tv = ET.Element("tv")

# Add channel metadata
for name, cid in channels.items():
    ch_elem = ET.SubElement(tv, "channel", id=cid)
    ET.SubElement(ch_elem, "display-name").text = name

# Fetch EPG data for each channel
for name, cid in channels.items():
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = f"{EPG_URL}&channelId={cid}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            json_data = response.json()
            for program in json_data.get("data", []):
                start_time = program["start"]
                end_time = program["end"]
                title = program.get("title", "No Title")
                desc = program.get("description", "No Description")

                prog = ET.SubElement(tv, "programme", {
                    "start": f"{start_time} +0000",
                    "stop": f"{end_time} +0000",
                    "channel": cid
                })
                ET.SubElement(prog, "title", lang="en").text = title
                ET.SubElement(prog, "desc", lang="en").text = desc

        except Exception as e:
            print(f"⚠️ Failed to parse JSON for {name}: {e}")
    else:
        print(f"❌ Failed to fetch EPG: HTTP {response.status_code}")

# Write to XML file
tree = ET.ElementTree(tv)
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ EPG file written to cignal_epg.xml")

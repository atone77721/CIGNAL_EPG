import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Replace with your actual channel ID mapping (names to UUIDs)
channels = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
}

# Time range for the EPG
start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

start_str = start.isoformat() + "Z"
end_str = end.isoformat() + "Z"

# XMLTV root element
tv = ET.Element("tv")

# To keep track of unique programmes
programmes = []

def fetch_epg(channel_name, channel_id):
    print(f"📡 Fetching EPG for channel ID: {channel_id}")
    url = f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?start={start_str}&end={end_str}&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
    response = requests.get(url)
    print(f"🔍 Status: {response.status_code}")
    print(f"🔗 URL: {url}")
    data = response.json()

    # Create <channel> element
    ch_elem = ET.SubElement(tv, "channel", id=channel_id)
    ET.SubElement(ch_elem, "display-name").text = channel_name

    epg_items = data if isinstance(data, list) else [data]
    for item in epg_items:
        if "pgm" not in item or "sc_st_dt" not in item or "sc_ed_dt" not in item:
            continue
        start = datetime.strptime(item["sc_st_dt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H%M%S") + " +0000"
        stop = datetime.strptime(item["sc_ed_dt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H%M%S") + " +0000"
        title = item["pgm"]["lod"][0]["n"] if item["pgm"].get("lod") else "Untitled"
        desc = item["pgm"]["lon"][0]["n"] if item["pgm"].get("lon") else ""

        programme = ET.Element("programme", start=start, stop=stop, channel=channel_id)
        ET.SubElement(programme, "title", lang="en").text = title
        ET.SubElement(programme, "desc", lang="en").text = desc
        programmes.append(programme)

        print(f"🔎 Sample data for {channel_name}:")
        print(item)

for name, cid in channels.items():
    fetch_epg(name, cid)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

print(f"✅ XMLTV written to 'cignal_epg.xml' with {len(programmes)} programmes and {len(channels)} channels")

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Channel list
channels = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
}

# API template
API_URL_TEMPLATE = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
    "start={start}&end={end}&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

# Create XMLTV root
tv = ET.Element("tv")

# Add channels to XML
for name, channel_id in channels.items():
    channel = ET.SubElement(tv, "channel", id=channel_id)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = name

# Time range: 1 day
start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=1)
start_str = start_time.isoformat() + "Z"
end_str = end_time.isoformat() + "Z"

# Fetch EPG for each channel
def fetch_epg(channel_name, channel_id):
    print(f"📡 Fetching EPG for {channel_name} (ID: {channel_id})")
    url = API_URL_TEMPLATE.format(start=start_str, end=end_str)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to fetch EPG: HTTP {response.status_code}")
            return

        data = response.json()
        programmes = data.get("lst", [])

        for prog in programmes:
            if prog.get("chnl_id") != channel_id:
                continue

            start = prog.get("sc_st_dt", "").replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"
            end = prog.get("sc_ed_dt", "").replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"

            lod = prog.get("pgm", {}).get("lod", [{}])[0]
            title = lod.get("n", "No Title")
            desc = lod.get("d", "No Description")

            programme = ET.SubElement(tv, "programme", start=start, stop=end, channel=channel_id)
            title_elem = ET.SubElement(programme, "title", lang="en")
            title_elem.text = title
            desc_elem = ET.SubElement(programme, "desc", lang="en")
            desc_elem.text = desc

    except requests.exceptions.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# Run fetch for all channels
for name, cid in channels.items():
    fetch_epg(name, cid)

# Output XMLTV file
tree = ET.ElementTree(tv)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ EPG file written to epg.xml")

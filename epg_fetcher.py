import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {"User-Agent": "Mozilla/5.0"}

# UTC start and end for 2-day window
start = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
end = start + timedelta(days=2)

# Generate XMLTV root
tv = ET.Element("tv", attrib={"generator-info-name": "Cignal API EPG", "generator-info-url": "https://example.com"})

def format_xml(elem, level=0):
    indent = "\n" + ("  " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            format_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

url = (
    f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
    f"start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
    f"end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
    f"reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

try:
    print("📡 Fetching EPG data from API...")
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()

    channel_map = {}  # To track added channels

    for entry in data.get("data", []):
        channel_id = entry.get("c")
        channel_name = entry.get("n", "Unknown Channel")

        if not channel_id:
            continue

        # Add channel only once
        if channel_id not in channel_map:
            ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
            ET.SubElement(ch_elem, "display-name").text = channel_name
            channel_map[channel_id] = True

        for program in entry.get("airing", []):
            start_time = program.get("sc_st_dt")
            end_time = program.get("sc_ed_dt")
            title = program.get("pgm", {}).get("lod", [{}])[0].get("n", "No Title")
            desc = program.get("pgm", {}).get("lon", [{}])[0].get("n", "No Description")

            if not start_time or not end_time:
                continue

            prog = ET.Element("programme", {
                "start": f"{start_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                "stop": f"{end_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                "channel": channel_id
            })
            ET.SubElement(prog, "title", lang="en").text = title
            ET.SubElement(prog, "desc", lang="en").text = desc
            tv.append(prog)

except Exception as e:
    print(f"❌ Failed to fetch or parse data: {e}")

# Format and save
format_xml(tv)
ET.ElementTree(tv).write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ EPG written to cignal_epg.xml")

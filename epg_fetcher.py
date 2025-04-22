import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
import urllib3
import gzip

# Disable SSL warnings (insecure workaround)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load channel map from JSON (expects a dictionary like {"Name": "ID"})
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Adjusted start and end times (1 day EPG)
start = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

# XMLTV base
epg_file = "cignal_epg.xml"
if os.path.exists(epg_file):
    tree = ET.parse(epg_file)
    tv = tree.getroot()
    print(f"✅ Loaded existing EPG file: {epg_file}")
else:
    tv = ET.Element("tv", attrib={"generator-info-name": "Cignal EPG Fetcher", "generator-info-url": "https://example.com"})
    print(f"✅ Created new EPG structure for: {epg_file}")

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

def fetch_epg(name, cid):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")

    url = (
        f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
        f"start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
        f"end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
        f"reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
    )

    programmes = []

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data.get("data"), list):
            print(f"⚠️ Unexpected format for {name}")
            return

        existing_channel = tv.find(f"./channel[@id='{cid}']")
        if existing_channel is None:
            channel = ET.SubElement(tv, "channel", {"id": cid})
            ET.SubElement(channel, "display-name").text = name

        for entry in data["data"]:
            if "airing" in entry and entry.get("channel_id") == cid:
                for program in entry["airing"]:
                    start_time = program.get("sc_st_dt")
                    end_time = program.get("sc_ed_dt")
                    pgm = program.get("pgm", {})
                    title = pgm.get("lod", [{}])[0].get("n", "No Title")
                    desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                    if not start_time or not end_time:
                        continue

                    try:
                        prog = ET.Element("programme", {
                            "start": f"{start_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                            "stop": f"{end_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                            "channel": cid
                        })
                        ET.SubElement(prog, "title", lang="en").text = title
                        ET.SubElement(prog, "desc", lang="en").text = desc
                        programmes.append((start_time, prog))
                    except Exception as e:
                        print(f"❌ Error parsing airing for {name}: {e}")

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")
        return

    programmes.sort(key=lambda x: x[0])
    for _, prog in programmes:
        tv.append(prog)

for name, cid in channels.items():
    fetch_epg(name, cid)

format_xml(tv)

# Save to XML (no update, just fetch and format)
# We don't save the XML directly in this version
# ET.ElementTree(tv).write(epg_file, encoding="utf-8", xml_declaration=True)
print(f"✅ EPG structure fetched and formatted successfully.")

# Compress to .gz
with open(epg_file, "rb") as f_in:
    with gzip.open(f"{epg_file}.gz", "wb") as f_out:
        f_out.writelines(f_in)
print(f"✅ Compressed to {epg_file}.gz")

# Optional preview (can be commented out if file is too big)
print("\n📄 Preview of EPG XML:\n" + "-" * 40)
with open(epg_file, "r", encoding="utf-8") as f:
    print(f.read()[:2000])  # Just show the first 2000 characters

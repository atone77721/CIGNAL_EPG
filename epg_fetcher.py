import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
from xml.dom import minidom

# Load channel map from JSON
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

# Helper to pretty-print and save XML
def save_pretty_xml(tree: ET.ElementTree, filename: str):
    rough_string = ET.tostring(tree.getroot(), encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

def fetch_epg(name, cid):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = (
        f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
        f"?start={start.isoformat()}Z"
        f"&end={end.isoformat()}Z"
        f"&reg=ph&dt=all&client=pldt-cignal-web"
        f"&pageNumber=1&pageSize=100"
    )

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data.get("data"), list):
            print(f"⚠️ Unexpected format for {name}")
            return

        tv = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

        # Channel element
        channel_elem = ET.SubElement(tv, "channel", {"id": cid})
        ET.SubElement(channel_elem, "display-name").text = name

        for entry in data["data"]:
            if "airing" in entry:
                for program in entry["airing"]:
                    start_time = program.get("sc_st_dt")
                    end_time = program.get("sc_ed_dt")
                    pgm = program.get("pgm", {})
                    title = pgm.get("lod", [{}])[0].get("n", "No Title")
                    desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                    if not start_time or not end_time:
                        continue

                    # Format: YYYYMMDDhhmmss
                    start_fmt = start_time.replace("-", "").replace(":", "")[:14]
                    end_fmt = end_time.replace("-", "").replace(":", "")[:14]

                    prog = ET.SubElement(tv, "programme", {
                        "start": f"{start_fmt} +0000",
                        "stop": f"{end_fmt} +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc

        # Save individual EPG file
        filename = f"epg_{name.replace(' ', '_').lower()}.xml"
        tree = ET.ElementTree(tv)
        save_pretty_xml(tree, filename)
        print(f"✅ EPG saved to {filename}")

        return tv

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")
        return None

# Master XML for all channels
tv_master = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

# Fetch and build
for name, cid in channels.items():
    channel_data = fetch_epg(name, cid)
    if channel_data is not None:
        tv_master.extend(channel_data.findall("channel"))
        tv_master.extend(channel_data.findall("programme"))

# Save the full EPG file
master_tree = ET.ElementTree(tv_master)
save_pretty_xml(master_tree, "cignal_epg.xml")
print("✅ Combined EPG file written to cignal_epg.xml")

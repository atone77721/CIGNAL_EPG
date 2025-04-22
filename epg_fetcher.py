import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os

# Load channel map from JSON
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Start and end time for EPG
start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

# Root XML element
tv = ET.Element("tv")

def format_xml(elem, level=0):
    """Pretty-print XML indentation"""
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
        f"https://cignalepg-api.aws.cignal.tv/epg/getepg?cid={cid}"
        f"&from={start.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&to={end.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&pageNumber=1&pageSize=100"
    )

    programmes = []

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data.get("data"), list):
            print(f"⚠️ Unexpected format for {name}")
            return

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

                    prog = ET.Element("programme", {
                        "start": start_time.replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000",
                        "stop": end_time.replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc
                    programmes.append((start_time, prog))

        # Sort by start time
        programmes.sort(key=lambda x: x[0])
        for _, prog in programmes:
            tv.append(prog)

        # Write to individual file
        filename = f"epg_{name.replace(' ', '_').lower()}.xml"
        tree = ET.ElementTree(ET.Element("tv", children=[prog for _, prog in programmes]))
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        print(f"✅ EPG file written to {filename}")

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")

# Loop through all channels
for name, cid in channels.items():
    ch = ET.SubElement(tv, "channel", {"id": cid})
    ET.SubElement(ch, "display-name").text = name
    fetch_epg(name, cid)

# Pretty-print and write final XML
format_xml(tv)
output_file = "cignal_epg.xml"
ET.ElementTree(tv).write(output_file, encoding="utf-8", xml_declaration=True)
print(f"✅ EPG saved to {output_file}")

# Preview the output (for GitHub Actions/logs)
print("\n📄 Preview of EPG XML:\n" + "-" * 40)
with open(output_file, "r", encoding="utf-8") as f:
    print(f.read())

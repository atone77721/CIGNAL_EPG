import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json

# Load channel map
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i
    return elem

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
            print(f"⚠️ Unexpected data format for {name}")
            return None

        tv = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

        # Channel element with multiple display-names
        channel_elem = ET.SubElement(tv, "channel", {"id": cid})
        ET.SubElement(channel_elem, "display-name").text = name
        ET.SubElement(channel_elem, "display-name").text = name.lower().replace(" ", "")
        ET.SubElement(channel_elem, "display-name").text = name.replace(" ", "_")
        ET.SubElement(channel_elem, "display-name").text = cid

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

                    # Format time for XMLTV spec
                    start_fmt = start_time.replace("-", "").replace(":", "")[:14]
                    end_fmt = end_time.replace("-", "").replace(":", "")[:14]

                    prog = ET.SubElement(tv, "programme", {
                        "start": f"{start_fmt} +0000",
                        "stop": f"{end_fmt} +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc

        # Save per-channel EPG
        filename = f"epg_{name.replace(' ', '_').lower()}.xml"
        tree = ET.ElementTree(indent(tv))
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        print(f"✅ EPG file written to {filename}")

        return tv

    except Exception as e:
        print(f"❌ Error fetching EPG for {name}: {e}")
        return None

# Combined XML
tv_master = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

for name, cid in channels.items():
    channel_data = fetch_epg(name, cid)
    if channel_data is not None:
        tv_master.extend(channel_data.findall("channel"))
        tv_master.extend(channel_data.findall("programme"))

# Write master XML
tree_master = ET.ElementTree(indent(tv_master))
tree_master.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ Combined EPG file written to cignal_epg.xml")

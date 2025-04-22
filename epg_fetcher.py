import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
from xml.dom import minidom

# Load your channel map
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

# Pretty save
def save_pretty_xml(tree: ET.ElementTree, filename: str):
    rough_string = ET.tostring(tree.getroot(), encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))

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
            return None

        tv = ET.Element("tv")

        # Channel info
        channel = ET.SubElement(tv, "channel", {"id": cid})
        ET.SubElement(channel, "display-name").text = name
        # Optional: add logo if you have URLs or files
        # ET.SubElement(channel, "icon", {"src": f"https://yourdomain.com/logos/{cid}.png"})

        for entry in data["data"]:
            for program in entry.get("airing", []):
                start_time = program.get("sc_st_dt")
                end_time = program.get("sc_ed_dt")
                pgm = program.get("pgm", {})
                title = pgm.get("lod", [{}])[0].get("n", "No Title")
                desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                if not start_time or not end_time:
                    continue

                start_fmt = start_time.replace("-", "").replace(":", "")[:14]
                end_fmt = end_time.replace("-", "").replace(":", "")[:14]

                prog = ET.SubElement(tv, "programme", {
                    "start": f"{start_fmt} +0000",
                    "stop": f"{end_fmt} +0000",
                    "channel": cid
                })
                ET.SubElement(prog, "title", lang="en").text = title
                ET.SubElement(prog, "desc", lang="en").text = desc

        return tv

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")
        return None

# Master TV node
tv_master = ET.Element("tv")

for name, cid in channels.items():
    epg_data = fetch_epg(name, cid)
    if epg_data:
        for elem in epg_data:
            tv_master.append(elem)

# Save pretty XMLTV file
tree = ET.ElementTree(tv_master)
save_pretty_xml(tree, "cignal_epg.xml")
print("✅ Saved to cignal_epg.xml")

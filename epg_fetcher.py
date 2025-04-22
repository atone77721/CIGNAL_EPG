import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

with open("cignal-map-channel.json", "r") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

tv = ET.Element("tv")

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
        if response.status_code == 200:
            json_data = response.json()
            programs = json_data.get("data", [])

            if not programs:
                print(f"⚠️ No EPG data for {name}")
                return

            for entry in programs:
                airings = entry.get("airing", [])
                for airing in airings:
                    start_time = airing.get("sc_st_dt")
                    end_time = airing.get("sc_ed_dt")
                    pgm = airing.get("pgm", {})
                    title = pgm.get("lod", [{"n": "No Title"}])[0].get("n", "No Title")
                    desc = pgm.get("lon", [{"n": "No Description"}])[0].get("n", "No Description")

                    if not start_time or not end_time:
                        print(f"❌ Missing start/end in airing for {name}")
                        continue

                    prog = ET.SubElement(tv, "programme", {
                        "start": f"{start_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                        "stop": f"{end_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc

        else:
            print(f"❌ HTTP Error {response.status_code} for {name}")
    except Exception as e:
        print(f"❌ Exception fetching EPG for {name}: {e}")

for ch in channels:
    name = ch.get("name", "Unknown")
    cid = ch.get("id", name.lower().replace(" ", "_"))

    ch_element = ET.SubElement(tv, "channel", {"id": cid})
    ET.SubElement(ch_element, "display-name").text = name
    ET.SubElement(ch_element, "display-name").text = cid  # fallback

    fetch_epg(name, cid)

# Pretty-print XML output
rough_string = ET.tostring(tv, encoding="utf-8")
reparsed = minidom.parseString(rough_string)
pretty_xml = reparsed.toprettyxml(indent="  ")

with open("cignal_epg.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print("✅ Pretty EPG saved to cignal_epg.xml")

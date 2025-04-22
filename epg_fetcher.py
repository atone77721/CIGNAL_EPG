import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os

# Load channel map from JSON
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

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

        # Create a new XML element for the channel data
        tv = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

        # Create the channel element
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

                    # Formatting the start and end times to match the expected format
                    start_time = start_time.replace("-", "").replace(":", "")[:14]
                    end_time = end_time.replace("-", "").replace(":", "")[:14]

                    prog = ET.SubElement(tv, "programme", {
                        "start": f"{start_time} +0000",
                        "stop": f"{end_time} +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc

        # Return the channel XML element to append to master XML
        return tv

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")
        return None

# Main TV element for combined XML
tv_master = ET.Element("tv", version="1.0", xmlns="http://www.xmltv.org/schema")

# Fetch and save individual EPG files, and also collect data for the master XML
for name, cid in channels.items():
    channel_data = fetch_epg(name, cid)
    if channel_data is not None:
        # Append each channel's data to the master XML
        tv_master.extend(channel_data.findall("channel"))
        tv_master.extend(channel_data.findall("programme"))

# Save the combined EPG data to the main cignal_epg.xml file
tree_master = ET.ElementTree(tv_master)

# Prettify the XML to ensure correct indentation and formatting
def pretty_print_xml(xml_element):
    rough_string = ET.tostring(xml_element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# Write the prettified XML to file
with open("cignal_epg.xml", "w", encoding="utf-8") as f:
    f.write(pretty_print_xml(tv_master))

print("✅ Combined and formatted EPG file written to cignal_epg.xml")

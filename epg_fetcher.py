import requests
import xml.etree.ElementTree as ET
import json
import os
import re
from datetime import datetime
from tqdm import tqdm

# Load channel mapping from cignal-map-channel.json
with open("cignal-map-channel.json", "r") as f:
    channels = json.load(f)

# Load optional EPG ID overrides
epg_id_map = {}
if os.path.exists("epg-id-map.json"):
    with open("epg-id-map.json", "r") as f:
        epg_id_map = json.load(f)

# Create EPG directory if it doesn't exist
os.makedirs("epg", exist_ok=True)

def sanitize_epg_id(name):
    return re.sub(r'[^a-z0-9]+', '', name.lower())

# Initialize master EPG root
tv = ET.Element("tv")

# Loop through each channel
for channel in tqdm(channels, desc="Generating EPG"):

    # Use epg_id map, else sanitize channel_number
    raw_id = channel.get("channel_number", "")
    epg_channel_id = epg_id_map.get(raw_id) or sanitize_epg_id(raw_id)

    # Make request to the EPG endpoint
    url = f"https://ott.cignal.tv/EPG/guide/{epg_channel_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to fetch EPG for {epg_channel_id} ({channel.get('channel_name')})")
        continue

    data = response.json()

    # Create XML for the channel
    channel_element = ET.Element("channel", id=epg_channel_id)
    display_name = ET.SubElement(channel_element, "display-name")
    display_name.text = channel.get("channel_name")
    tv.append(channel_element)

    # Save EPG entries per program
    for program in data.get("programs", []):
        programme = ET.Element("programme", {
            "start": datetime.fromisoformat(program["start"]).strftime("%Y%m%d%H%M%S") + " +0000",
            "stop": datetime.fromisoformat(program["end"]).strftime("%Y%m%d%H%M%S") + " +0000",
            "channel": epg_channel_id,
        })
        title = ET.SubElement(programme, "title")
        title.text = program.get("title", "No Title")
        desc = ET.SubElement(programme, "desc")
        desc.text = program.get("description", "No Description")
        tv.append(programme)

    # Save per-channel EPG
    epg_tree = ET.ElementTree(ET.Element("tv", children=[channel_element] + tv.findall(f"./programme[@channel='{epg_channel_id}']")))
    epg_tree.write(f"epg/{epg_channel_id}.xml", encoding="utf-8", xml_declaration=True)

# Save master EPG XML
tree = ET.ElementTree(tv)
tree.write("epg/cignal-epg.xml", encoding="utf-8", xml_declaration=True)

print("✅ Done generating EPGs!")

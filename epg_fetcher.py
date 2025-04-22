import json
import os
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta

# Constants
EPG_URL_TEMPLATE = "https://cignal.s3-ap-southeast-1.amazonaws.com/epg/{channel_id}.json"
CHANNEL_MAP_FILE = "cignal-map-channel.json"
OUTPUT_DIR = "xmltv"
MASTER_FILE = "xmltv.xml"

# Helpers
def fetch_epg(channel_id):
    url = EPG_URL_TEMPLATE.format(channel_id=channel_id)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        print(f"❌ Failed to fetch EPG for {channel_id}")
        return None

def pretty_print_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def build_channel_element(channel):
    elem = ET.Element("channel", id=channel["id"])
    display_name = ET.SubElement(elem, "display-name")
    display_name.text = channel["name"]
    return elem

def build_programme_element(channel_id, programme):
    start = datetime.fromisoformat(programme["start"])
    stop = datetime.fromisoformat(programme["end"])
    start_str = start.strftime("%Y%m%d%H%M%S +0000")
    stop_str = stop.strftime("%Y%m%d%H%M%S +0000")

    elem = ET.Element("programme", start=start_str, stop=stop_str, channel=channel_id)

    title = ET.SubElement(elem, "title", lang="en")
    title.text = programme.get("title", "No Title")

    desc = ET.SubElement(elem, "desc", lang="en")
    desc.text = programme.get("description", "")

    category = ET.SubElement(elem, "category", lang="en")
    category.text = programme.get("genre", "Other")

    return elem

def save_xml_file(file_path, xml_elem):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pretty_print_xml(xml_elem))

# Main script
def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(CHANNEL_MAP_FILE, "r", encoding="utf-8") as f:
        channel_map = json.load(f)

    tv_master = ET.Element("tv")

    for channel in channel_map:
        channel_id = channel["id"]
        channel_name = channel["name"]
        print(f"📡 Fetching EPG for {channel_name} (ID: {channel_id})")

        epg_data = fetch_epg(channel_id)
        if not epg_data:
            continue

        # Create root element for per-channel file
        tv = ET.Element("tv")

        # Add <channel> to both
        chan_elem = build_channel_element(channel)
        tv.append(chan_elem)
        tv_master.append(chan_elem)

        # Add <programme>s
        for prog in epg_data.get("listings", []):
            prog_elem = build_programme_element(channel_id, prog)
            tv.append(prog_elem)
            tv_master.append(prog_elem)

        # Save per-channel XMLTV
        save_xml_file(os.path.join(OUTPUT_DIR, f"{channel_id}.xml"), tv)

    # Save master XMLTV
    save_xml_file(MASTER_FILE, tv_master)

if __name__ == "__main__":
    main()

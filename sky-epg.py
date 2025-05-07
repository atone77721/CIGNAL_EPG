import requests
import datetime
import xml.etree.ElementTree as ET
import gzip
from dateutil import parser

BASE_URL = "https://skyepg.mysky.com.ph/Main/getEventsbyType"
LOGO_URL = "http://202.78.65.124/epgcms/uploads/"

def fetch_epg(counter):
    params = {"counter": counter}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def convert_time(timestamp_ms):
    # Try to parse the string date (e.g. '2025/05/07 10:00')
    try:
        dt = parser.parse(timestamp_ms)
        return dt.strftime("%Y%m%d%H%M%S +0800")
    except Exception as e:
        print(f"❌ Error parsing timestamp: {timestamp_ms} - {e}")
        raise

def create_xmltv(all_data):
    tv = ET.Element("tv")
    channel_ids = set()

    for epg_data in all_data:
        # Add channels once
        for loc in epg_data["location"]:
            if loc["id"] not in channel_ids:
                channel_ids.add(loc["id"])
                channel = ET.SubElement(tv, "channel", id=str(loc["id"]))
                display_name = ET.SubElement(channel, "display-name")
                display_name.text = loc["name"]
                logo = loc.get("userData", {}).get("logo", "")
                if logo:
                    ET.SubElement(channel, "icon", src=LOGO_URL + logo)

        # Add events
        for event in epg_data["events"]:
            start_time = convert_time(event["start"])
            end_time = convert_time(event["end"])
            programme = ET.SubElement(tv, "programme", start=start_time, stop=end_time, channel=str(event["location"]))

            title = ET.SubElement(programme, "title", lang="en")
            title.text = event.get("name", "No Title")

            if event.get("description"):
                desc = ET.SubElement(programme, "desc", lang="en")
                desc.text = event["description"]

    return ET.ElementTree(tv)

def save_xml_with_compression(xmltv_tree):
    # Save XML file normally
    xmltv_tree.write("sky_epg.xml", encoding="utf-8", xml_declaration=True)
    print("✅ EPG saved to sky_epg.xml")

    # Save compressed XML as .gz
    with gzip.open("sky_epg.xml.gz", "wb") as f:
        xmltv_tree.write(f, encoding="utf-8", xml_declaration=True)
    print("✅ EPG saved to sky_epg.xml.gz")

if __name__ == "__main__":
    try:
        all_epg_data = []
        for counter in range(3, 27, 3):  # 3h steps: 3, 6, 9, ..., 24
            print(f"Fetching EPG for next {counter} hours...")
            data = fetch_epg(counter)
            if data.get("events"):
                all_epg_data.append(data)
            else:
                print(f"⚠️ No events returned for counter {counter}")

        if not all_epg_data:
            print("❌ No EPG data collected.")
            exit(1)

        xmltv = create_xmltv(all_epg_data)
        save_xml_with_compression(xmltv)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

import requests
import datetime
import xml.etree.ElementTree as ET
import gzip
from xml.dom import minidom
from dateutil import parser

BASE_URL = "https://skyepg.mysky.com.ph/Main/getEventsbyType"
LOGO_URL = "http://202.78.65.124/epgcms/uploads/"

def fetch_epg(counter):
    params = {"counter": counter}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def convert_time(timestamp_str):
    try:
        dt = parser.parse(timestamp_str)
        return dt.strftime("%Y%m%d%H%M%S +0800")
    except Exception as e:
        print(f"❌ Error parsing timestamp: {timestamp_str} - {e}")
        raise

def create_xmltv(all_data):
    tv = ET.Element("tv")
    channel_ids = set()

    for epg_data in all_data:
        for loc in epg_data["location"]:
            if loc["id"] not in channel_ids:
                channel_ids.add(loc["id"])
                channel = ET.SubElement(tv, "channel", id=str(loc["id"]))
                display_name = ET.SubElement(channel, "display-name")
                display_name.text = loc["name"]
                logo = loc.get("userData", {}).get("logo", "")
                if logo:
                    ET.SubElement(channel, "icon", src=LOGO_URL + logo)

        for event in epg_data["events"]:
            start_time = convert_time(event["start"])
            end_time = convert_time(event["end"])
            programme = ET.SubElement(tv, "programme", start=start_time, stop=end_time, channel=str(event["location"]))

            title_text = event.get("name", "No Title")
            title = ET.SubElement(programme, "title", lang="en")
            title.text = title_text

            desc_text = event.get("description") or title_text
            desc = ET.SubElement(programme, "desc", lang="en")
            desc.text = desc_text

    return tv

def prettify_xml(elem):
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def save_xml_with_compression(tv_element):
    pretty_xml = prettify_xml(tv_element)

    with open("sky_epg.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print("✅ EPG saved to sky_epg.xml")

    with gzip.open("sky_epg.xml.gz", "wt", encoding="utf-8") as f:
        f.write(pretty_xml)
    print("✅ EPG saved to sky_epg.xml.gz")

if __name__ == "__main__":
    try:
        all_epg_data = []
        for counter in range(3, 27, 3):  # Fetch 3, 6, ..., 24 hours
            print(f"Fetching EPG for next {counter} hours...")
            data = fetch_epg(counter)
            if data.get("events"):
                all_epg_data.append(data)
            else:
                print(f"⚠️ No events returned for counter {counter}")

        if not all_epg_data:
            print("❌ No EPG data collected.")
            exit(1)

        tv_element = create_xmltv(all_epg_data)
        save_xml_with_compression(tv_element)

    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

import requests
import datetime
import xml.etree.ElementTree as ET

# EPG endpoint from the SKYcable website
BASE_URL = "https://skyepg.mysky.com.ph/Main/getEventsbyType"
LOGO_URL = "http://202.78.65.124/epgcms/uploads/"

def fetch_epg(counter=3):
    """Fetch EPG JSON data from SKYcable endpoint"""
    params = {"counter": counter}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def convert_time(timestamp_ms):
    """Convert JS timestamp (ms) to XMLTV datetime format"""
    dt = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
    return dt.strftime("%Y%m%d%H%M%S +0800")

def create_xmltv(epg_data):
    """Convert EPG JSON to XMLTV format"""
    tv = ET.Element("tv")

    # Add channels
    for loc in epg_data["location"]:
        channel = ET.SubElement(tv, "channel", id=str(loc["id"]))
        display_name = ET.SubElement(channel, "display-name")
        display_name.text = loc["name"]
        logo = loc.get("userData", {}).get("logo", "")
        if logo:
            icon = ET.SubElement(channel, "icon", src=LOGO_URL + logo)

    # Add programmes
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

if __name__ == "__main__":
    try:
        epg_data = fetch_epg(counter=3)  # You can change counter to 6, 9, etc. for future hours
        xmltv = create_xmltv(epg_data)
        xmltv.write("sky_epg.xml", encoding="utf-8", xml_declaration=True)
        print("✅ EPG saved to sky_epg.xml")
    except Exception as e:
        print(f"❌ Error: {e}")

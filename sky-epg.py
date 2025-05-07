import requests
import datetime
import xml.etree.ElementTree as ET

# EPG endpoint from the website JS
BASE_URL = "https://skyepg.mysky.com.ph/Main/getEventsbyType"
LOGO_URL = "http://202.78.65.124/epgcms/uploads/"

# You can loop over counter values for more data (3-hour blocks)
def fetch_epg(counter=3):
    params = {"counter": counter}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

# XMLTV helpers
def create_xmltv(epg_data):
    tv = ET.Element("tv")

    # Add channels
    for loc in epg_data["location"]:
        channel = ET.SubElement(tv, "channel", id=str(loc["id"]))
        display_name = ET.SubElement(channel, "display-name")
        display_name.text = loc["name"]
        if loc["userData"]["logo"]:
            icon = ET.SubElement(channel, "icon", src=LOGO_URL + loc["userData"]["logo"])

    # Add programmes
    for event in epg_data["events"]:
        start_time = convert_time(event["start"])
        end_time = convert_time(event["end"])
        programme = ET.SubElement(tv, "programme", start=start_time, stop=end_time, channel=str(event["location"]))

        title = ET.SubElement(programme, "title", lang="en")
        title.text = event.get("name", "No Title")

        if "description" in event and event["description"]:
            desc = ET.SubElement(programme, "desc", lang="en")
            desc.text = event["description"]

    return ET.ElementTree(tv)

def convert_time(timestamp_ms):
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y%m%d%H%M%S +0800")

if __name__ == "__main__":
    epg_data = fetch_epg(counter=3)  # Can increase to 6, 9, etc. for more
    xmltv = create_xmltv(epg_data)
    xmltv.write("sky_epg.xml", encoding="utf-8", xml_declaration=True)
    print("EPG saved to sky_epg.xml")

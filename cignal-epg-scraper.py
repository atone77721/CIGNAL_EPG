import pytz
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from dateutil import parser as dtparser

# Load and parse the uploaded XML file
CHANNEL_XML_FILE = 'cignalplay.com.channels.xml'
tree = ET.parse(CHANNEL_XML_FILE)
root = tree.getroot()

channel_elements = root.find('channels')

# Build list of channels from XML
channel_map = []
for ch in channel_elements.findall('channel'):
    site_id = ch.get('site_id')
    xmltv_id = ch.get('xmltv_id')
    channel_map.append({
        "site_id": site_id,
        "xmltv_id": xmltv_id
    })

# Prepare XMLTV root
tv = Element('tv')
tv.set('generator-info-name', 'CIGNAL-EPG-GENERATOR')
tv.set('generator-info-url', 'https://cignalplay.com')

def add_channel_element(channel_id, display_name):
    channel = SubElement(tv, 'channel', id=channel_id)
    SubElement(channel, 'display-name').text = display_name

def add_programme_element(channel_id, title, start, stop, desc=""):
    programme = SubElement(tv, 'programme', start=start, stop=stop, channel=channel_id)
    SubElement(programme, 'title').text = title
    SubElement(programme, 'desc').text = desc

# Current time (UTC)
utc = pytz.utc
now = datetime.now(utc)

# Fetch 7 days of EPG from the API
def fetch_epg_data_for_7_days():
    all_airings = []
    for day_offset in range(7):
        day_start = now + timedelta(days=day_offset)
        day_end = day_start + timedelta(days=1)

        start_time = day_start.strftime('%Y-%m-%dT00:00:00Z')
        end_time = day_end.strftime('%Y-%m-%dT00:00:00Z')

        url = (
            "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
            f"?start={start_time}&end={end_time}&reg=ph&dt=all&client=pldt-cignal-web"
            "&pageNumber=1&pageSize=500"
        )

        print(f"📅 Fetching day {day_offset + 1}/7: {start_time} to {end_time}")
        try:
            response = httpx.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("data"):
                all_airings.extend(data["data"])
                print(f"   ✅ {len(data['data'])} channel blocks added")
            else:
                print("   ⚠️ No EPG data found for this day.")
        except Exception as e:
            print(f"   ❌ Error fetching EPG for day {day_offset + 1}: {e}")
    return all_airings

# Fetch EPG blocks
epg_blocks = fetch_epg_data_for_7_days()

# Build quick lookup from site_id to xmltv_id
site_id_to_xmltv = {ch["site_id"]: ch["xmltv_id"] for ch in channel_map}
match_count = {ch["xmltv_id"]: 0 for ch in channel_map}

# Add all channel elements to XMLTV
for ch in channel_map:
    add_channel_element(ch["xmltv_id"], ch["xmltv_id"])

# Parse EPG blocks
for block in epg_blocks:
    for airing in block.get("airing", []):
        ch_info = airing.get("ch", {})
        site_id = ch_info.get("ex_id")

        if site_id not in site_id_to_xmltv:
            continue

        xmltv_id = site_id_to_xmltv[site_id]

        try:
            start = dtparser.parse(airing["sc_st_dt"])
            end = dtparser.parse(airing["sc_ed_dt"])
            start_str = start.strftime('%Y%m%d%H%M%S +0000')
            end_str = end.strftime('%Y%m%d%H%M%S +0000')

            title = airing["pgm"]["lod"][0]["n"]
            desc = airing["pgm"]["lon"][0]["n"] if airing["pgm"].get("lon") else ""

            add_programme_element(xmltv_id, title, start_str, end_str, desc)
            match_count[xmltv_id] += 1
        except Exception as e:
            print(f"⚠️ Error parsing programme for {xmltv_id}: {e}")

# Summary
print("\n📊 EPG Channel Match Summary:")
for ch_id, count in match_count.items():
    print(f"• {ch_id}: {count} programme(s)")

# Save the XMLTV file
tree = ElementTree(tv)
tree.write('cignal-epg.xml', encoding='utf-8', xml_declaration=True)
print("✅ EPG successfully written to cignal-epg.xml")

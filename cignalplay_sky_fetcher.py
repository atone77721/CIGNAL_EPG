import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta, timezone
import pytz
import gzip
from bs4 import BeautifulSoup

# Timezone
TIMEZONE = pytz.timezone('Asia/Manila')
USER_AGENT = {'User-Agent': 'Mozilla/5.0'}

# --- CIGNAL CONFIG ---
EPG_API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
CHANNEL_URLS = {
    "cg_hbohd": "http://www.cignalplay.com",  # Add the rest of your mappings here
}

# --- CIGNAL FUNCTIONS ---
def fetch_cignal_epg(start_offset_days=0, duration_days=2):
    start_time = (datetime.now(timezone.utc) + timedelta(days=start_offset_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = (datetime.now(timezone.utc) + timedelta(days=start_offset_days + duration_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    params = {
        "start": start_time,
        "end": end_time,
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100,
    }

    try:
        response = requests.get(EPG_API_URL, params=params, headers=USER_AGENT)
        response.raise_for_status()
        return response.json().get('data', [])
    except Exception as e:
        print(f"❌ Failed to fetch Cignal EPG: {e}")
        return []

def convert_to_manila(utc_str):
    if not utc_str: return None
    try:
        return datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    except Exception as e:
        print(f"❌ Time conversion error: {e}")
        return None

def format_epg_time(dt):
    return dt.strftime('%Y%m%d%H%M%S') + " +0800"

def build_epg_xml(epg_data):
    tv = ET.Element('tv', {'generator-info-name': 'Cignal EPG'})
    channels_created = set()

    for item in epg_data:
        for airing in item.get('airing', []):
            ch_info = airing.get('ch', {})
            channel_id = ch_info.get('cs', 'unknown')
            display_name = ch_info.get('ex_id', 'Unknown Channel')

            if channel_id not in channels_created:
                ch_el = ET.SubElement(tv, 'channel', {'id': channel_id})
                ET.SubElement(ch_el, 'display-name').text = display_name
                ET.SubElement(ch_el, 'url').text = CHANNEL_URLS.get(channel_id, "http://example.com")
                channels_created.add(channel_id)

            start = convert_to_manila(airing.get('sc_st_dt'))
            end = convert_to_manila(airing.get('sc_ed_dt'))
            if not start or not end:
                continue

            pgm_info = airing.get('pgm', {})
            title = pgm_info.get('lon', [{}])[0].get('n', 'No Title')
            desc = pgm_info.get('lod', [{}])[0].get('n', 'No Description')

            p = ET.SubElement(tv, 'programme', {
                'start': format_epg_time(start),
                'stop': format_epg_time(end),
                'channel': channel_id
            })
            ET.SubElement(p, 'title', {'lang': 'en'}).text = title
            ET.SubElement(p, 'desc', {'lang': 'en'}).text = desc

    return tv

# --- SKYCABLE FUNCTIONS ---
def load_skycable_channels(xml_path="skycable.com.channels.xml"):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return [{"site_id": ch.attrib["site_id"], "name": ch.text.strip()}
            for ch in root.findall(".//channel") if "site_id" in ch.attrib]

def fetch_sky_epg(channel_id, days=6):
    base_url = "http://www.skycable.com/channelguide.aspx?channel="
    epg_list = []

    for day in range(days):
        date = (datetime.now(TIMEZONE) + timedelta(days=day)).strftime("%m%%2F%d%%2F%Y")
        post_data = {
            "__VIEWSTATE": "index_variable_element",
            "ctl00$MainContentPlaceHolder$dlChannel": channel_id,
            "ctl00$MainContentPlaceHolder$DateTextBox": date,
            "ctl00$MainContentPlaceHolder$MaskedEditExtender5_ClientState": "",
            "ctl00$MainContentPlaceHolder$btnGo.x": "11",
            "ctl00$MainContentPlaceHolder$btnGo.y": "12"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            **USER_AGENT
        }

        try:
            response = requests.post(base_url + channel_id, data=post_data, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            shows = soup.find_all("table")  # Placeholder: Replace with precise parsing
            for _ in shows:
                epg_list.append({
                    "title": "Sample Show",
                    "desc": "Sample Description",
                    "start": datetime.now(),
                    "end": datetime.now() + timedelta(hours=1),
                    "channel_id": channel_id
                })
        except Exception as e:
            print(f"❌ SkyCable error ({channel_id}): {e}")
    
    return epg_list

def build_sky_epg_xml(channels):
    tv = ET.Element('tv', {'generator-info-name': 'SkyCable EPG'})
    for ch in channels:
        listings = fetch_sky_epg(ch["site_id"])
        ch_el = ET.SubElement(tv, 'channel', {'id': ch["site_id"]})
        ET.SubElement(ch_el, 'display-name').text = ch["name"]
        for show in listings:
            p = ET.SubElement(tv, 'programme', {
                'start': format_epg_time(show["start"]),
                'stop': format_epg_time(show["end"]),
                'channel': ch["site_id"]
            })
            ET.SubElement(p, 'title', {'lang': 'en'}).text = show["title"]
            ET.SubElement(p, 'desc', {'lang': 'en'}).text = show["desc"]
    return tv

# --- OUTPUT ---
def save_xml(tv_element, filename):
    xml_str = ET.tostring(tv_element, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    with gzip.open(filename + ".gz", "wb") as gz:
        gz.write(pretty_xml.encode("utf-8"))
    print(f"✅ Saved: {filename} & {filename}.gz")

# --- MAIN ---
def main():
    print("📡 Fetching Cignal EPG...")
    cignal_data = fetch_cignal_epg()
    if cignal_data:
        xml = build_epg_xml(cignal_data)
        save_xml(xml, "cignal_epg.xml")

    print("📡 Fetching SkyCable EPG...")
    sky_channels = load_skycable_channels("skycable.com.channels.xml")
    sky_xml = build_sky_epg_xml(sky_channels)
    save_xml(sky_xml, "sky_epg.xml")

if __name__ == "__main__":
    main()

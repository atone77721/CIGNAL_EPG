import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta, timezone
import pytz
import gzip

# Channel URL mappings
CHANNEL_URLS = {
    "tv5": "http://www.cignalplay.com",
    "cnn_hd": "http://www.cignalplay.com",
    # Add more channels as needed
}

# Updated EPG API URL
EPG_API_URL = "https://data-store-cdn.api.pldt.firstlight.ai/content/epg"
TIMEZONE = pytz.timezone('Asia/Manila')
USER_AGENT = {'User-Agent': 'Mozilla/5.0'}

def fetch_epg(start_offset_days=0, duration_days=2):
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
        print(f"❌ Failed to fetch EPG data: {e}")
        return []

def convert_to_manila(utc_str):
    if not utc_str:
        return None
    try:
        utc_time = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
        return utc_time.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    except Exception as e:
        print(f"❌ Time conversion error: {e}")
        return None

def format_epg_time(dt):
    return dt.strftime('%Y%m%d%H%M%S') + " +0800"

def build_epg_xml(epg_data):
    tv = ET.Element('tv', {'generator-info-name': 'CignalEPG', 'generator-info-url': 'http://cignalplay.com'})
    channels_created = set()

    for item in epg_data:
        airing_data = item.get('airing', [])
        for airing in airing_data:
            ch_info = airing.get('ch', {})
            channel_id = ch_info.get('cs', 'unknown')
            display_name = ch_info.get('ex_id', 'Unknown Channel')

            if channel_id not in channels_created:
                channel_el = ET.SubElement(tv, 'channel', {'id': channel_id})
                ET.SubElement(channel_el, 'display-name', {'lang': 'en'}).text = display_name
                ET.SubElement(channel_el, 'url').text = CHANNEL_URLS.get(channel_id, "http://www.cignalplay.com")
                channels_created.add(channel_id)

            start_str = airing.get('sc_st_dt')
            end_str = airing.get('sc_ed_dt')

            if not start_str or not end_str:
                continue

            start_time = convert_to_manila(start_str)
            end_time = convert_to_manila(end_str)

            if not start_time or not end_time:
                continue

            pgm_info = airing.get('pgm', {})
            title = pgm_info.get('lon', [{}])[0].get('n', 'No Title')
            description = pgm_info.get('lod', [{}])[0].get('n', 'No Description')

            programme = ET.SubElement(tv, 'programme', {
                'start': format_epg_time(start_time),
                'stop': format_epg_time(end_time),
                'channel': channel_id
            })

            ET.SubElement(programme, 'title', {'lang': 'en'}).text = title
            ET.SubElement(programme, 'desc', {'lang': 'en'}).text = description

    return tv

def save_xml(tv_element, filename='cignal_epg.xml'):
    try:
        xml_str = ET.tostring(tv_element, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        print(f"✅ XML saved to {filename}")

        gz_path = filename + ".gz"
        with gzip.open(gz_path, "wb") as gz_file:
            gz_file.write(pretty_xml.encode("utf-8"))
        print(f"✅ Gzipped XML saved to {gz_path}")

    except Exception as e:
        print(f"❌ Error saving XML: {e}")

def main():
    print("📡 Fetching EPG from updated URL...")
    epg_data = fetch_epg()

    if not epg_data:
        print("❌ No EPG data available.")
        return

    print("🛠 Building XML...")
    tv_xml = build_epg_xml(epg_data)

    print("💾 Saving XML...")
    save_xml(tv_xml)

if __name__ == "__main__":
    main()

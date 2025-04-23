import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import gzip
import os
from datetime import datetime, timedelta, timezone
import pytz

# Sample mapping from site_id to xmltv_id (add full mappings as needed)
CHANNELS = {
    "44B03994-C303-4ACE-997C-91CAC493D0FC": "Rptv",
    "68C2D95A-A2A4-4C2B-93BE-41893C61210C": "Cg Hitsnow",
    "B741DD7A-A7F8-4F8A-A549-9EF411020F9D": "Cg Hbohd",
    # Add more site_id mappings from your channel XML file here
}

def format_manila_time(dt):
    dt = dt.astimezone(pytz.timezone("Asia/Manila"))
    return dt.strftime('%Y%m%d%H%M%S +0800')

def fetch_epg(start_time, end_time):
    url = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    params = {
        "start": start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end": end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100,
    }

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to fetch EPG: {e}")
        return {}

def build_xmltv(epg_data):
    tv = ET.Element('tv')
    added_channels = set()

    for item in epg_data.get('data', []):
        for airing in item.get('airing', []):
            ch_info = airing.get('ch', {})
            channel_id = ch_info.get('cs')
            display_name = CHANNELS.get(channel_id, "Unknown")

            if channel_id and channel_id not in added_channels:
                channel_el = ET.SubElement(tv, 'channel', {'id': channel_id})
                ET.SubElement(channel_el, 'display-name', {'lang': 'en'}).text = display_name
                added_channels.add(channel_id)

            try:
                start_dt = datetime.strptime(airing.get('sc_st_dt'), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                end_dt = datetime.strptime(airing.get('sc_ed_dt'), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except Exception as e:
                print(f"⚠️ Failed to parse times for {channel_id}: {e}")
                continue

            programme = ET.SubElement(tv, 'programme', {
                'start': format_manila_time(start_dt),
                'stop': format_manila_time(end_dt),
                'channel': channel_id
            })

            title = airing.get('pgm', {}).get('lon', [{}])[0].get('n', 'No Title')
            desc = airing.get('pgm', {}).get('lod', [{}])[0].get('n', 'No Description')

            ET.SubElement(programme, 'title', {'lang': 'en'}).text = title
            ET.SubElement(programme, 'desc', {'lang': 'en'}).text = desc

    return minidom.parseString(ET.tostring(tv, encoding="utf-8")).toprettyxml(indent="  ")

def save_xml(content, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved XML to {filename}")

    with gzip.open(f"{filename}.gz", "wb") as gz:
        gz.write(content.encode("utf-8"))
    print(f"✅ Saved GZ to {filename}.gz")

def main():
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=2)
    print("📡 Fetching EPG from API...")
    epg_data = fetch_epg(now, end)

    if not epg_data:
        print("❌ No data fetched.")
        return

    print("🧩 Building XMLTV format...")
    xml_content = build_xmltv(epg_data)

    print("💾 Saving to files...")
    save_xml(xml_content, "cignalplay_epg.xml")

if __name__ == "__main__":
    main()

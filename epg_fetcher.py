import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from datetime import datetime, timedelta
import pytz
import gzip

channel_urls = {
    "cg_hbohd": "http://www.cignalplay.com",
    # Add other channel mappings as needed
}

def fetch_epg():
    now_utc = datetime.utcnow()
    start_time = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = (now_utc + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')

    url = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    params = {
        "start": start_time,
        "end": end_time,
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"❌ Error fetching or decoding JSON: {e}")
        return []

def format_manila_time(offset_hours=0):
    manila_tz = pytz.timezone('Asia/Manila')
    now = datetime.now(manila_tz) + timedelta(hours=offset_hours)
    return now.strftime('%Y%m%d%H%M%S') + " +0800"

def create_epg_xml(epg_data):
    if isinstance(epg_data, dict) and 'data' in epg_data:
        epg_data = epg_data['data']
    else:
        print("❌ Invalid EPG data format.")
        return

    tv = ET.Element('tv', {'generator-info-name': 'none', 'generator-info-url': 'none'})
    programs_by_channel = {}

    for item in epg_data:
        if 'airing' in item:
            for airing in item['airing']:
                channel_details = airing['ch']
                channel_id = channel_details.get('cs', 'unknown')
                display_name = channel_details.get('ex_id', 'Unknown Channel')

                if channel_id not in programs_by_channel:
                    programs_by_channel[channel_id] = []
                    channel = ET.SubElement(tv, 'channel', {'id': channel_id})
                    ET.SubElement(channel, 'display-name', {'lang': 'en'}).text = display_name
                    ET.SubElement(channel, 'url').text = channel_urls.get(channel_id, "http://example.com")

                for episode in airing['pgm']['lod']:
                    start = format_manila_time()
                    stop = format_manila_time(offset_hours=1)
                    title = airing['pgm']['lon'][0]['n']
                    description = airing['pgm']['lod'][0]['n']

                    programme = ET.SubElement(tv, 'programme', {
                        'start': start,
                        'stop': stop,
                        'channel': channel_id
                    })
                    ET.SubElement(programme, 'title', {'lang': 'en'}).text = title
                    ET.SubElement(programme, 'desc', {'lang': 'en'}).text = description
        else:
            print(f"⚠️ Skipping item, no 'airing': {item}")

    try:
        xml_str = ET.tostring(tv, encoding="utf-8", method="xml").decode()
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

        xml_path = "cignal_epg.xml"
        gz_path = xml_path + ".gz"

        # Save uncompressed XML
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        print(f"✅ Uncompressed XML saved to {xml_path}")

        # Save compressed XML
        with gzip.open(gz_path, "wb") as f:
            f.write(pretty_xml.encode("utf-8"))
        print(f"✅ Gzipped XML saved to {gz_path}")

    except Exception as e:
        print(f"❌ Error writing XML: {e}")

def main():
    print("📡 Fetching EPG from API...")
    epg_data = fetch_epg()

    if not epg_data:
        print("❌ No data fetched.")
    else:
        print("✅ Data fetched. Creating XML...")
        create_epg_xml(epg_data)

if __name__ == "__main__":
    main()

import requests
import xml.etree.ElementTree as ET
import datetime
import json
import os

CHANNEL_MAP_PATH = 'cignal-map-channel.json'
EPG_API_URL = 'https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg'

def load_channel_map():
    """Load the channel map JSON"""
    with open(CHANNEL_MAP_PATH, 'r') as f:
        return json.load(f)

def fetch_epg_data(start_time, end_time, page_number=1, page_size=100):
    """Fetch EPG data using the API"""
    params = {
        'start': start_time,
        'end': end_time,
        'reg': 'ph',
        'dt': 'all',
        'client': 'pldt-cignal-web',
        'pageNumber': page_number,
        'pageSize': page_size
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        response = requests.get(EPG_API_URL, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch EPG: {e}")
        return None

def create_xmltv(channel_map, start_time, end_time):
    """Create XMLTV format XML for EPG"""
    tv = ET.Element('tv')

    # Add <channel> elements
    for channel_name, channel_id in channel_map.items():
        channel = ET.SubElement(tv, 'channel', id=channel_name)
        display_name = ET.SubElement(channel, 'display-name')
        display_name.text = channel_name

    # Fetch and add <programme> elements for each channel
    page_number = 1
    while True:
        epg_data = fetch_epg_data(start_time, end_time, page_number)
        if not epg_data or 'data' not in epg_data:
            break

        for program in epg_data['data']:
            channel_name = program.get('channelName')
            if channel_name not in channel_map:
                continue  # Skip channels not in the map

            start_time = parse_time(program.get('start'))
            end_time = parse_time(program.get('end'))
            title = program.get('title', 'No Title')
            description = program.get('description', '')

            programme = ET.SubElement(tv, 'programme', {
                'start': start_time,
                'stop': end_time,
                'channel': channel_name
            })
            title_el = ET.SubElement(programme, 'title', lang="en")
            title_el.text = title
            if description:
                desc_el = ET.SubElement(programme, 'desc', lang="en")
                desc_el.text = description

        # If there are more pages, go to the next one
        page_number += 1

    return ET.ElementTree(tv)

def parse_time(time_str):
    """Parse timestamps into XMLTV-compatible format"""
    try:
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y%m%d%H%M%S +0000')

def save_xmltv(tree, output_path='cignal_epg.xml'):
    """Save the XMLTV file to disk"""
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"EPG saved to {output_path}")

if __name__ == '__main__':
    if not os.path.exists(CHANNEL_MAP_PATH):
        print(f"Missing {CHANNEL_MAP_PATH}")
        exit(1)

    channel_map = load_channel_map()

    # Define the start and end time for the EPG query
    start_time = '2024-04-27T16:00:00Z'
    end_time = '2024-04-28T16:00:00Z'

    epg_tree = create_xmltv(channel_map, start_time, end_time)
    save_xmltv(epg_tree)

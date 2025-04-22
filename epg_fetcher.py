import requests
import xml.etree.ElementTree as ET
import json
from xml.dom import minidom
import os
from datetime import datetime, timedelta
import pytz

# URLs per channel (adjust based on your actual channel URL requirements)
channel_urls = {
    "bilyonaryoch": "http://www.cignalplay.com",  # Example URL, change per actual channel
    # Add other channel mappings as needed
}

def fetch_epg():
    # Get the current time in UTC (we will adjust it to Manila Time later)
    now_utc = datetime.utcnow()

    # Format the current time and calculate the range (24 hours from now)
    start_time = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = (now_utc + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        print("Raw Response: ", response.text)  # Debugging line to check the raw response
        response.raise_for_status()
        
        try:
            return response.json()
        except ValueError as e:
            print(f"Error decoding JSON: {e}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error with the request: {e}")
        return []

def format_manila_time(offset_hours=0):
    """Generates the current time with Manila Time (UTC+8) and optional time offset in the format YYYYMMDDHHMMSS +0800"""
    manila_tz = pytz.timezone('Asia/Manila')
    now = datetime.now(manila_tz) + timedelta(hours=offset_hours)  # Apply offset if necessary (e.g., timezone)
    return now.strftime('%Y%m%d%H%M%S') + " +0800"  # Format: YYYYMMDDHHMMSS +0800 for Manila Time

def create_epg_xml(epg_data):
    if isinstance(epg_data, dict) and 'data' in epg_data:
        epg_data = epg_data['data']
    else:
        print("Error: EPG data format is incorrect.")
        return
    
    tv = ET.Element('tv', {'generator-info-name': 'none', 'generator-info-url': 'none'})
    
    # Store all programs in a dictionary
    programs_by_channel = {}

    for item in epg_data:
        if 'airing' in item:
            for airing in item['airing']:
                channel_details = airing['ch']
                channel_id = channel_details.get('cs', 'unknown')
                display_name = channel_details.get('ex_id', 'Unknown Channel')

                # Ensure the channel exists in our dictionary and create the <channel> element
                if channel_id not in programs_by_channel:
                    programs_by_channel[channel_id] = []

                    # Create the channel element with <url>
                    channel = ET.SubElement(tv, 'channel', {'id': channel_id})
                    ET.SubElement(channel, 'display-name', {'lang': 'en'}).text = display_name
                    url = channel_urls.get(channel_id, "http://example.com")  # Get URL from the map or default
                    ET.SubElement(channel, 'url').text = url

                # Add the programmes
                for episode in airing['pgm']['lod']:
                    # Generate current time for program start and stop in Manila Time
                    programme_start_formatted = format_manila_time()
                    programme_end_formatted = format_manila_time(offset_hours=1)  # End time 1 hour later for example

                    # Create the <programme> element with the formatted times
                    programme = ET.SubElement(tv, 'programme', {
                        'start': programme_start_formatted,
                        'stop': programme_end_formatted,
                        'channel': channel_id
                    })

                    title = ET.SubElement(programme, 'title', {'lang': 'en'})
                    title.text = episode.get('n', 'No Title')  # Episode title

                    # Fallback: if no description is available, use the title
                    description = ET.SubElement(programme, 'desc', {'lang': 'en'})
                    description.text = episode.get('n', 'No Description')  # Default to title if no desc

        else:
            print(f"Warning: No 'airing' found in item: {item}")
    
    # Pretty print the XML and save it to file
    try:
        xml_str = ET.tostring(tv, encoding="utf-8", method="xml").decode()
        parsed_xml = minidom.parseString(xml_str)
        
        # Debug print the XML
        print("Generated XML:")
        print(parsed_xml.toprettyxml(indent="  "))  # Print XML to console for debug
        
        # Save to file
        save_path = os.path.join(os.getcwd(), "cignal_epg.xml")
        print(f"Saving to: {save_path}")  # Debugging line to show file path
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(parsed_xml.toprettyxml(indent="  "))  # Ensure it's saved
        print(f"✅ EPG saved to {save_path}")
    except Exception as e:
        print(f"❌ Error saving XML file: {e}")

def main():
    print("📡 Fetching EPG from API...")
    epg_data = fetch_epg()

    if not epg_data:
        print("❌ No data fetched, skipping XML creation.")
    else:
        print(f"✅ Data fetched, proceeding with XML creation.")
        create_epg_xml(epg_data)

if __name__ == "__main__":
    main()

import requests
import xml.etree.ElementTree as ET
import json
from xml.dom import minidom

# URLs per channel (adjust based on your actual channel URL requirements)
channel_urls = {
    "A2z.ph": "http://www.cignalplay.com",
    "ANC.ph": "http://www.clickthecity.com",
    "ANIMALPLANET.ph": "http://www.tapdmv.com"
}

def fetch_epg():
    url = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    params = {
        "start": "2025-04-23T16:00:00Z",
        "end": "2025-04-24T16:00:00Z",
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

def format_time(date_time_str):
    # Converts datetime from '2025-04-23T16:00:00Z' to '20250423160000 -0500'
    dt = date_time_str.replace("T", "").replace("Z", "")
    return f"{dt[:8]}{dt[8:14]} -0500"  # Assuming timezone is -0500

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
                channel_id = airing['ch'].get('cs', 'unknown')
                display_name = airing['ch'].get('ex_id', 'Unknown Channel')

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
                    programme_start = airing['sc_st_dt']
                    programme_end = airing['sc_ed_dt']

                    # Create the <programme> element with the formatted times
                    programme = ET.SubElement(tv, 'programme', {
                        'start': format_time(programme_start),
                        'stop': format_time(programme_end),
                        'channel': channel_id
                    })

                    title = ET.SubElement(programme, 'title', {'lang': 'en'})
                    title.text = episode['n']  # Episode title

                    description = ET.SubElement(programme, 'desc', {'lang': 'en'})
                    description.text = episode['n']  # Episode description (assuming same as title)

        else:
            print(f"Warning: No 'airing' found in item: {item}")
    
    # Pretty print the XML and save it to file
    try:
        xml_str = ET.tostring(tv, encoding="utf-8", method="xml").decode()
        parsed_xml = minidom.parseString(xml_str)
        with open("cignal_epg.xml", "w", encoding="utf-8") as f:
            f.write(parsed_xml.toprettyxml(indent="  "))  # Add indentation for readability
        print("✅ EPG saved to cignal_epg.xml")
    except Exception as e:
        print(f"❌ Error saving XML file: {e}")

def main():
    print("📡 Fetching EPG from API...")
    epg_data = fetch_epg()

    if epg_data:
        print(f"✅ EPG fetched with {len(epg_data)} items.")
        create_epg_xml(epg_data)
    else:
        print("❌ No data found or error occurred during fetching.")

if __name__ == "__main__":
    main()

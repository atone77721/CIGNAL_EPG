import requests
import xml.etree.ElementTree as ET

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

def create_epg_xml(epg_data):
    if isinstance(epg_data, dict) and 'data' in epg_data:
        epg_data = epg_data['data']
    else:
        print("Error: EPG data format is incorrect.")
        return
    
    tv = ET.Element('tv', {'generator-info-name': 'Cignal EPG Fetcher', 'generator-info-url': 'https://example.com'})
    
    for item in epg_data:
        if 'airing' in item:
            for airing in item['airing']:
                # Debugging: Print the channel details
                channel_details = airing['ch']
                print(f"Channel details: {channel_details}")  # Debugging line
                
                channel_id = airing['ch'].get('cid', 'unknown')  # Use 'unknown' if 'cid' is missing
                display_name = airing['ch'].get('acs', 'Unknown Channel')  # Use 'Unknown Channel' if 'acs' is missing
                
                # Debugging: Print the channel_id and display_name
                print(f"Channel ID: {channel_id}, Display Name: {display_name}")  # Debugging line
                
                # Create the channel element
                channel = ET.SubElement(tv, 'channel', {'id': channel_id})
                ET.SubElement(channel, 'display-name').text = display_name
                
                # Create the programme element
                programme = ET.SubElement(tv, 'programme', {
                    'start': airing['sc_st_dt'],
                    'stop': airing['sc_ed_dt'],
                    'channel': channel_id
                })
                
                title = ET.SubElement(programme, 'title', {'lang': 'en'})
                title.text = airing['pgm']['lod'][0]['n']
                
                description = ET.SubElement(programme, 'desc', {'lang': 'en'})
                description.text = airing['pgm']['lod'][0]['n']
        else:
            print(f"Warning: No 'airing' found in item: {item}")
    
    tree = ET.ElementTree(tv)
    tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

def main():
    print("📡 Fetching EPG from API...")
    epg_data = fetch_epg()

    if epg_data:
        print(f"✅ EPG fetched with {len(epg_data)} items.")
        create_epg_xml(epg_data)
        print("✅ EPG saved to cignal_epg.xml")
    else:
        print("❌ No data found or error occurred during fetching.")

if __name__ == "__main__":
    main()

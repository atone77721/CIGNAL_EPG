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

    response = requests.get(url, params=params)
    response_data = response.json()

    if response_data.get("data"):
        return response_data["data"]
    else:
        print("No data found in the response.")
        return []

def create_epg_xml(epg_data):
    # Create the root XML element
    tv = ET.Element('tv', {'generator-info-name': 'Cignal EPG Fetcher', 'generator-info-url': 'https://example.com'})
    
    # Iterate through the EPG data to create XML entries
    for item in epg_data:
        for airing in item['airing']:
            # Create the channel element
            channel = ET.SubElement(tv, 'channel', {'id': airing['ch']['cid']})
            ET.SubElement(channel, 'display-name').text = airing['ch']['acs']
            
            # Create the programme element
            programme = ET.SubElement(tv, 'programme', {
                'start': airing['sc_st_dt'],
                'stop': airing['sc_ed_dt'],
                'channel': airing['ch']['cid']
            })
            
            title = ET.SubElement(programme, 'title', {'lang': 'en'})
            title.text = airing['pgm']['lod'][0]['n']  # Program name
            
            description = ET.SubElement(programme, 'desc', {'lang': 'en'})
            description.text = airing['pgm']['lod'][0]['n']  # Use program name as description

    # Generate the final XML string
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
        print("❌ No data found in the API response.")

if __name__ == "__main__":
    main()

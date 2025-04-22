import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Function to fetch EPG data from Cignal API
def fetch_epg(name, cid, start, end):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = (
        f"https://cignalepg-api.aws.cignal.tv/epg/getepg?cid={cid}"
        f"&from={start.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&to={end.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&pageNumber=1&pageSize=100"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

# Function to generate EPG XML
def generate_epg_xml(api_data):
    tv = ET.Element("tv")

    # Parse the API data to extract channels and events
    for channel_data in api_data.get('channels', []):
        channel_id = channel_data['id']
        channel_name = channel_data['name']
        
        channel = ET.SubElement(tv, "channel", id=channel_id)
        display_name = ET.SubElement(channel, "display-name")
        display_name.text = channel_name
        
        # Add event data to channel if available
        for event in channel_data.get('events', []):  # Assuming 'events' key for programs
            start_time = event['start']
            end_time = event['end']
            title = event['title']
            description = event.get('description', "No description available")
            
            program = ET.SubElement(tv, "programme", channel=channel_id, start=start_time, stop=end_time)
            ET.SubElement(program, "title").text = title
            ET.SubElement(program, "desc").text = description

    # Generate XML string
    tree = ET.ElementTree(tv)
    return tree

# Main function to fetch and generate EPG
def main():
    # Define date range (example: today and next day)
    start = datetime.now()
    end = start + timedelta(days=1)
    
    # Define the channels (example channels)
    channels = [
        {"name": "Bilyonaryoch", "cid": "Bilyonaryoch_cid"},
        {"name": "Rptv", "cid": "Rptv_cid"}
    ]
    
    # Fetch and process EPG for each channel
    all_epg_data = {}
    for channel in channels:
        api_data = fetch_epg(channel["name"], channel["cid"], start, end)
        if api_data:
            all_epg_data[channel["name"]] = api_data
    
    # Generate EPG XML based on fetched data
    epg_tree = generate_epg_xml(all_epg_data)
    
    # Write XML to file
    epg_tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("EPG file generated successfully.")

if __name__ == "__main__":
    main()

import requests
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET

# URL for the API
API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"

# Set the time period for the EPG data (for example, 24 hours)
start_time = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=1)

# Convert times to UTC and format them as strings
start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

# Prepare the API request parameters
params = {
    "start": start_time_str,
    "end": end_time_str,
    "reg": "ph",
    "dt": "all",
    "client": "pldt-cignal-web",
    "pageNumber": 1,
    "pageSize": 100
}

# Add headers to the request if needed (User-Agent, Authorization, etc.)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Authorization": "Bearer <your_api_key_here>"  # Replace with actual API key if needed
}

# Function to fetch EPG data
def fetch_epg():
    try:
        print("📡 Fetching EPG from API...")
        response = requests.get(API_URL, params=params, headers=headers)

        # Check if the response was successful
        if response.status_code == 200:
            data = response.json()

            # Create the root of the XML tree
            root = ET.Element("tv", {
                "generator-info-name": "Cignal EPG Fetcher",
                "generator-info-url": "https://example.com"
            })

            # Process each channel and its programs
            for channel_data in data['data']:
                for airing in channel_data['airing']:
                    # Extract channel information
                    channel = airing['ch']
                    channel_id = airing.get('cid', 'unknown')
                    channel_name = channel.get('acs', 'Unknown Channel')

                    # Create a channel element
                    channel_element = ET.SubElement(root, "channel", id=channel_id)
                    display_name = ET.SubElement(channel_element, "display-name")
                    display_name.text = channel_name

                    # Process each program for the current channel
                    program = airing['pgm']
                    start = datetime.strptime(airing['ct'], "%Y-%m-%dT%H:%M:%SZ")
                    end = start + timedelta(minutes=airing['dur'])

                    # Convert times to the local timezone (PST)
                    tz = pytz.timezone('Asia/Manila')
                    start = pytz.utc.localize(start).astimezone(tz)
                    end = pytz.utc.localize(end).astimezone(tz)

                    # Format the start and stop times in the required format
                    start_str = start.strftime("%Y%m%d%H%M%S") + " +0800"
                    end_str = end.strftime("%Y%m%d%H%M%S") + " +0800"

                    # Extract the title and description from the program
                    title = program['lod'][0]['n'] if program['lod'] else 'No Title'
                    description = program['lon'][0]['n'] if program['lon'] else 'No Description'

                    # Create a programme element
                    programme = ET.SubElement(root, "programme", start=start_str, stop=end_str, channel=channel_id)
                    title_elem = ET.SubElement(programme, "title", lang="en")
                    title_elem.text = title
                    desc_elem = ET.SubElement(programme, "desc", lang="en")
                    desc_elem.text = description

            # Create the tree and write the XML to a file
            tree = ET.ElementTree(root)
            with open("cignal_epg.xml", "wb") as f:
                tree.write(f)
            print("✅ EPG saved to cignal_epg.xml")

        else:
            print(f"❌ Failed to fetch EPG: {response.status_code} {response.text}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    fetch_epg()

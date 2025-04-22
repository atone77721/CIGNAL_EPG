import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz

# Define the timezone to convert the times to (e.g., Philippines Time)
TIMEZONE = pytz.timezone("Asia/Manila")

# API URL (replace with the correct endpoint)
API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?start=2024-04-27T16%3A00:00Z&end=2024-04-28T16%3A00:00Z&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"

# Headers (add necessary headers here)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Referer': 'https://www.cignalplay.com',  # Adding the custom header
    'Host': 'live-data-store-cdn.api.pldt.firstlight.ai',  # Optional if needed
    # Add additional headers if needed (e.g., API keys, etc.)
}

def fetch_epg():
    try:
        # Send the GET request with headers
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()  # Check for any errors in the response

        # Parse the JSON response from the API
        epg_data = response.json()

        # Create the root XML element
        root = ET.Element("tv", generator_info_name="Cignal EPG Fetcher", generator_info_url="https://example.com")

        # Dictionary to keep track of channel IDs we've already processed
        processed_channels = {}

        # Loop through the response and populate the XML
        for item in epg_data.get("data", []):
            for airing in item.get("airing", []):
                channel_id = airing.get("cid")
                program_title = airing.get("pgm", {}).get("lod", [{}])[0].get("n")
                program_desc = airing.get("pgm", {}).get("lon", [{}])[0].get("n")
                start_time_str = airing.get("ct")
                duration = airing.get("dur", 0)

                # Convert the start time to a datetime object
                start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
                start_time = start_time.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)

                # Calculate the stop time by adding the duration
                stop_time = start_time + timedelta(minutes=duration)

                # Format the times in the required XML format (YYYYMMDDHHMMSS)
                start_time_str = start_time.strftime("%Y%m%d%H%M%S")  # Convert to desired format
                stop_time_str = stop_time.strftime("%Y%m%d%H%M%S")

                # Only add a new channel if we haven't added it before
                if channel_id not in processed_channels:
                    channel = ET.SubElement(root, "channel", id=channel_id)
                    ET.SubElement(channel, "display-name").text = channel_id  # Set a display name for simplicity
                    processed_channels[channel_id] = True

                # Create XML elements for each program
                programme = ET.SubElement(root, "programme", start=f"{start_time_str} +0800", stop=f"{stop_time_str} +0800", channel=channel_id)
                ET.SubElement(programme, "title", lang="en").text = program_title
                ET.SubElement(programme, "desc", lang="en").text = program_desc

        # Generate the XML string
        xml_data = ET.tostring(root, encoding="utf-8", method="xml").decode()

        # Save the XML to a file
        with open("cignal_epg.xml", "w", encoding="utf-8") as f:
            f.write(xml_data)

        print("✅ EPG saved to cignal_epg.xml")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch EPG: {e}")

if __name__ == "__main__":
    fetch_epg()

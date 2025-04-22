import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Load channel map from the provided JSON
with open("cignal-map-channel.json", "r") as f:
    channel_map = json.load(f)

# Build headers to mimic a legit request
headers = {
    "Origin": "https://cignalplay.com",
    "Referer": "https://cignalplay.com/",
    "User-Agent": "Mozilla/5.0",
}

# Define the time range (from today 16:00 UTC to tomorrow 16:00 UTC)
start_time = datetime.now(timezone.utc).replace(hour=16, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=1)

# Build API URL
api_url = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    f"?start={start_time.isoformat()}&end={end_time.isoformat()}"
    "&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

print("📡 Fetching EPG from API...")

# Fetch data from the API
try:
    response = requests.get(api_url, headers=headers, verify=False)
    response.raise_for_status()
    epg_data = response.json().get("data", [])
except Exception as e:
    print(f"❌ Failed to fetch EPG: {e}")
    exit(1)

# Create the XML root element
root = ET.Element("tv", attrib={
    "generator-info-name": "Cignal EPG Fetcher",
    "generator-info-url": "https://example.com"
})

# Track added channels
processed_channels = {}

# Process each entry in the EPG data
for item in epg_data:
    airing = item.get("airing", [])[0] if item.get("airing") else None
    if not airing:
        continue

    # Extract the channel info
    channel_id = airing.get("cid")
    channel_name = airing.get("ch", {}).get("acs", channel_id)

    # Map the channel name to the channel ID
    mapped_channel_id = channel_map.get(channel_name)

    if not mapped_channel_id:
        print(f"❌ Channel '{channel_name}' not found in channel map.")
        continue

    # Add the channel to the XML only once
    if mapped_channel_id not in processed_channels:
        channel_elem = ET.SubElement(root, "channel", id=mapped_channel_id)
        ET.SubElement(channel_elem, "display-name").text = channel_name
        processed_channels[mapped_channel_id] = True

    # Get program start and end times
    start_str = airing.get("id", "").split("-")[-1].replace("T", "").replace("Z", "").replace(":", "")
    start_dt = datetime.strptime(start_str, "%Y%m%d%H%M%S")
    end_dt = start_dt + timedelta(minutes=airing.get("dur", 30))

    # Format the times in XMLTV format
    start_xml = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
    end_xml = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"

    # Get program title and description
    program_title = airing.get("pgm", {}).get("lod", [{}])[0].get("n", "No Title")
    program_desc = airing.get("pgm", {}).get("lon", [{}])[0].get("n", "No Description")

    # Add the programme to the XML
    programme_elem = ET.SubElement(root, "programme", attrib={
        "start": start_xml,
        "stop": end_xml,
        "channel": mapped_channel_id
    })
    ET.SubElement(programme_elem, "title", lang="en").text = program_title
    ET.SubElement(programme_elem, "desc", lang="en").text = program_desc

# Output the XML to file
tree = ET.ElementTree(root)
ET.indent(tree, space="  ", level=0)  # Python 3.9+ indent formatting
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

print("✅ EPG saved to cignal_epg.xml")

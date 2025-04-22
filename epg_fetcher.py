import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import os

# Debug: Show where the file will be saved
print("📁 Saving to directory:", os.getcwd())

# Headers to mimic a legit browser
headers = {
    "Origin": "https://cignalplay.com",
    "Referer": "https://cignalplay.com/",
    "User-Agent": "Mozilla/5.0",
}

# Define EPG range from today 16:00 UTC to tomorrow 16:00 UTC
start_time = datetime.now(timezone.utc).replace(hour=16, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=1)

# Build API URL
api_url = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    f"?start={start_time.isoformat()}&end={end_time.isoformat()}"
    "&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

print("📡 Fetching EPG from API...")
try:
    response = requests.get(api_url, headers=headers, verify=False)
    response.raise_for_status()
    json_data = response.json()
except Exception as e:
    print(f"❌ Failed to fetch EPG: {e}")
    exit(1)

# Create XMLTV root
root = ET.Element("tv", attrib={
    "generator-info-name": "Cignal EPG Fetcher",
    "generator-info-url": "https://example.com"
})

# Track processed channels
processed_channels = {}

# Track how many programmes added
program_count = 0

# Loop through all EPG entries
for item in json_data.get("data", []):
    for airing in item.get("airing", []):
        channel_id = airing.get("cid")
        channel_name = airing.get("ch", {}).get("acs", channel_id)

        # Add channel only once
        if channel_id not in processed_channels:
            channel_elem = ET.SubElement(root, "channel", id=channel_id)
            ET.SubElement(channel_elem, "display-name").text = channel_name
            processed_channels[channel_id] = True

        # Parse start time from ID
        start_str = airing.get("id", "").split("-")[-1].replace("T", "").replace("Z", "").replace(":", "")
        try:
            start_dt = datetime.strptime(start_str, "%Y%m%d%H%M%S")
        except:
            continue

        end_dt = start_dt + timedelta(minutes=airing.get("dur", 30))

        # Format time in XMLTV format
        start_xml = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        end_xml = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"

        # Get program title and description
        program_title = airing.get("pgm", {}).get("lod", [{}])[0].get("n", "No Title")
        program_desc = airing.get("pgm", {}).get("lon", [{}])[0].get("n", "No Description")

        # Add programme element
        programme_elem = ET.SubElement(root, "programme", attrib={
            "start": start_xml,
            "stop": end_xml,
            "channel": channel_id
        })
        ET.SubElement(programme_elem, "title", lang="en").text = program_title
        ET.SubElement(programme_elem, "desc", lang="en").text = program_desc
        program_count += 1

# Save to XML file
try:
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
    print(f"✅ EPG saved to cignal_epg.xml with {program_count} programme(s).")
except Exception as e:
    print(f"❌ Failed to save XML: {e}")

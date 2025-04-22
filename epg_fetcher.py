import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Load the channel map from cignal-map-channel.json
with open("cignal-map-channel.json", "r") as f:
    channel_map = json.load(f)

# Sample EPG data (replace this with actual data scraping or fetching)
# Here, we're assuming the EPG data is fetched from a local source or scraped earlier
epg_data = [
    {
        "channel_name": "Bilyonaryoch",
        "start_time": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + " +0800",  # current time in XMLTV format
        "end_time": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y%m%d%H%M%S") + " +0800",  # 1 hour later
        "title": "Billionaire's Show",
        "description": "The richest and most powerful individuals."
    },
    {
        "channel_name": "Rptv",
        "start_time": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y%m%d%H%M%S") + " +0800",  # current time + 1 hour
        "end_time": (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0800",  # 2 hours later
        "title": "Rptv Live",
        "description": "Live broadcast of news and events."
    }
    # Add more data as needed
]

# Create the XML root structure
root = ET.Element("tv", attrib={
    "generator-info-name": "Cignal EPG Fetcher",
    "generator-info-url": "https://example.com"
})

# Track added channels
processed_channels = {}

# Loop through the EPG data (this should be your actual scraping logic)
for epg in epg_data:
    channel_name = epg.get("channel_name")
    start_time = epg.get("start_time")
    end_time = epg.get("end_time")
    title = epg.get("title")
    description = epg.get("description")
    
    # Get the channel ID from the map
    channel_id = channel_map.get(channel_name)

    if channel_id:
        # Add channel to XML if not already processed
        if channel_id not in processed_channels:
            channel_elem = ET.SubElement(root, "channel", id=channel_id)
            ET.SubElement(channel_elem, "display-name").text = channel_name
            processed_channels[channel_id] = True

        # Add program information to XML
        programme_elem = ET.SubElement(root, "programme", attrib={
            "start": start_time,
            "stop": end_time,
            "channel": channel_id
        })
        ET.SubElement(programme_elem, "title", lang="en").text = title
        ET.SubElement(programme_elem, "desc", lang="en").text = description
    else:
        print(f"Channel {channel_name} not found in channel map.")

# Output XML to file
tree = ET.ElementTree(root)
ET.indent(tree, space="  ", level=0)  # Python 3.9+
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

print("✅ EPG saved to cignal_epg.xml")

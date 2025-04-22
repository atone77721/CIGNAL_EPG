import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Build headers to mimic a legit request
headers = {
    "Origin": "https://cignalplay.com",
    "Referer": "https://cignalplay.com/",
    "User-Agent": "Mozilla/5.0",
}

# Define the time range (today 00:00 UTC to 24 hours later)
start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=1)

# API URL with updated time window
api_url = (
    "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
    f"?start={start_time.isoformat()}&end={end_time.isoformat()}"
    "&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=10"
)

print("📡 Fetching EPG from API...")
try:
    response = requests.get(api_url, headers=headers, verify=False)
    response.raise_for_status()
    json_data = response.json()

    # Check if there's data in the response
    if not json_data.get("data"):
        print("❌ No data found in the API response.")
        exit(1)

    # Create root XML structure
    root = ET.Element("tv", attrib={
        "generator-info-name": "Cignal EPG Fetcher",
        "generator-info-url": "https://example.com"
    })

    # Track added channels
    processed_channels = {}

    # Loop through the data
    for item in json_data.get("data", []):
        airing = item.get("airing", [])[0] if item.get("airing") else None
        if not airing:
            continue

        channel_id = airing.get("cid")
        channel_name = airing.get("ch", {}).get("acs", channel_id)

        # Add channel only once
        if channel_id not in processed_channels:
            channel_elem = ET.SubElement(root, "channel", id=channel_id)
            ET.SubElement(channel_elem, "display-name").text = channel_name
            processed_channels[channel_id] = True

        # Program info
        start_str = airing.get("id", "").split("-")[-1].replace("T", "").replace("Z", "").replace(":", "")
        start_dt = datetime.strptime(start_str, "%Y%m%d%H%M%S")
        end_dt = start_dt + timedelta(minutes=airing.get("dur", 30))

        # Format time in XMLTV format
        start_xml = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        end_xml = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"

        # Title and description
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

    # Output XML to file (pretty printed)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)  # Python 3.9+
    tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

    print("✅ EPG saved to cignal_epg.xml")

except Exception as e:
    print(f"❌ Failed to fetch EPG: {e}")
    exit(1)

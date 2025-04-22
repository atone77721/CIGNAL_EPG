import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import urllib3

# Disable SSL warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_epg():
    print("📡 Fetching EPG from API...")
    url = "https://live-data-store-cdn.api.pldt.firstlight.ai/epgs/cignal/airing/grid?limit=1000"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch EPG: {e}")
        return

    data = response.json()
    epg_data = data.get("data", [])

    if not epg_data:
        print("⚠️ No EPG data found.")
        return

    root = ET.Element("tv", attrib={
        "generator-info-name": "Cignal API EPG",
        "generator-info-url": "https://example.com"
    })

    channels_added = set()

    for item in epg_data:
        channel_info = item.get("channel", {})
        channel_name = channel_info.get("name", "Unknown Channel")
        channel_id = channel_info.get("id", "unknown")

        if channel_id not in channels_added:
            channel_elem = ET.SubElement(root, "channel", id=channel_id)
            ET.SubElement(channel_elem, "display-name").text = channel_name
            channels_added.add(channel_id)

        start_time_utc = datetime.fromisoformat(item.get("start")).replace(tzinfo=pytz.UTC)
        end_time_utc = datetime.fromisoformat(item.get("end")).replace(tzinfo=pytz.UTC)

        pst = pytz.timezone("Asia/Manila")
        start_time = start_time_utc.astimezone(pst).strftime("%Y%m%d%H%M%S %z")
        end_time = end_time_utc.astimezone(pst).strftime("%Y%m%d%H%M%S %z")

        programme_elem = ET.SubElement(root, "programme", {
            "start": start_time,
            "stop": end_time,
            "channel": channel_id
        })

        title = item.get("title", "No Title")
        desc = item.get("description", title)
        ET.SubElement(programme_elem, "title", lang="en").text = title
        ET.SubElement(programme_elem, "desc", lang="en").text = desc

    tree = ET.ElementTree(root)
    output_file = "cignal_epg.xml"
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    print(f"✅ EPG saved to {output_file}")

if __name__ == "__main__":
    fetch_epg()

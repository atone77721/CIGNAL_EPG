import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import json
import os

# Define time zone for Philippine Standard Time (PST)
PST = pytz.timezone('Asia/Manila')

# Adjusted start and end times for the new API query format (1 day window)
start = datetime.now(PST).replace(hour=16, minute=0, second=0, microsecond=0)  # Start time today at 16:00 PST
end = start + timedelta(days=1)  # 1 day window

# API URL
api_url = f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"

# Prepare headers
headers = {
    "User-Agent": "Mozilla/5.0"
}

# Initialize the XML structure
tv = ET.Element("tv", attrib={"generator-info-name": "Cignal EPG Fetcher", "generator-info-url": "https://example.com"})

# Function to fetch and parse EPG data
def fetch_epg():
    print("📡 Fetching EPG from API...")

    try:
        response = requests.get(api_url, headers=headers, verify=False)  # Disable SSL warnings for now
        response.raise_for_status()
        data = response.json()

        if not isinstance(data.get("data"), list):
            print("⚠️ No valid data found.")
            return

        # Parse each program in the response data
        for entry in data["data"]:
            if "airing" in entry:
                for program in entry["airing"]:
                    start_time = program.get("sc_st_dt")
                    end_time = program.get("sc_ed_dt")
                    pgm = program.get("pgm", {})
                    title = pgm.get("lod", [{}])[0].get("n", "No Title")
                    desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                    if not start_time or not end_time:
                        continue

                    # Convert start and end times to the correct format for XMLTV
                    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")  # Assuming this format
                    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
                    start_time = start_time.astimezone(PST).strftime("%Y%m%d%H%M%S +0800")
                    end_time = end_time.astimezone(PST).strftime("%Y%m%d%H%M%S +0800")

                    # Create XML structure for each program
                    programme = ET.Element("programme", {
                        "start": start_time,
                        "stop": end_time,
                        "channel": "unknown"  # We can replace "unknown" with channel data if available
                    })
                    ET.SubElement(programme, "title", lang="en").text = title
                    ET.SubElement(programme, "desc", lang="en").text = desc
                    tv.append(programme)

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch EPG: {e}")

# Call the function to fetch and populate the XML
fetch_epg()

# Save the XML to a file
tree = ET.ElementTree(tv)
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)

print("✅ EPG saved to cignal_epg.xml")

# Optionally, you can print the XML for preview
print("\n📄 Preview of EPG XML:\n" + "-" * 40)
with open("cignal_epg.xml", "r", encoding="utf-8") as f:
    print(f.read())

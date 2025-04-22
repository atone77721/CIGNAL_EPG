import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
import json
import os
import shutil
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load channel map
with open("cignal-map-channel.json") as f:
    channels = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Setup time window
start = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
end = start + timedelta(days=2)

# EPG file
epg_file = "cignal_epg.xml"

# Create new TV root
tv = ET.Element("tv", attrib={
    "generator-info-name": "Cignal EPG Fetcher",
    "generator-info-url": "https://example.com"
})

def fetch_epg(name, cid):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    
    url = (
        f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
        f"start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
        f"end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
        f"reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
    )

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        # Filter only matching channel
        entries = [entry for entry in data.get("data", []) if entry.get("chn", {}).get("id") == cid]

        if not entries:
            print(f"⚠️ No EPG data found for {name}")
            return

        # Add <channel> block
        channel = ET.SubElement(tv, "channel", {"id": cid})
        ET.SubElement(channel, "display-name").text = name

        for entry in entries:
            for program in entry.get("airing", []):
                start_time = program.get("sc_st_dt")
                end_time = program.get("sc_ed_dt")
                pgm = program.get("pgm", {})
                title = pgm.get("lod", [{}])[0].get("n", "No Title")
                desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                if not start_time or not end_time:
                    continue

                # Format times
                start_fmt = start_time.replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"
                end_fmt = end_time.replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"

                prog = ET.Element("programme", {
                    "start": start_fmt,
                    "stop": end_fmt,
                    "channel": cid
                })
                ET.SubElement(prog, "title", lang="en").text = title
                ET.SubElement(prog, "desc", lang="en").text = desc
                tv.append(prog)

    except Exception as e:
        print(f"❌ Error fetching/parsing EPG for {name}: {e}")

# Fetch EPG for all channels
for name, cid in channels.items():
    fetch_epg(name, cid)

# Backup existing file
if os.path.exists(epg_file):
    shutil.copy2(epg_file, epg_file + ".bak")
    print(f"🗂️ Backup saved as {epg_file}.bak")

# Save and format output
rough_string = ET.tostring(tv, encoding="utf-8")
reparsed = minidom.parseString(rough_string)
with open(epg_file, "w", encoding="utf-8") as f:
    f.write(reparsed.toprettyxml(indent="  "))

print(f"✅ EPG written to {epg_file}")

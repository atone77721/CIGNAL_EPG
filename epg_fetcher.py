import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import gzip
import urllib3
import logging

# ========== CONFIG ==========
CHANNEL_MAP_FILE = "cignal-map-channel.json"
EPG_OUTPUT_FILE = "cignal_epg.xml"
EPG_COMPRESSED_FILE = f"{EPG_OUTPUT_FILE}.gz"
LOG_FILE = "cignal_epg.log"
TIMEZONE_OFFSET = "+0000"  # change if needed
DAYS_TO_FETCH = 1

# ========== SETUP ==========
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode='w')
    ]
)

# Load channel map
with open(CHANNEL_MAP_FILE, "r", encoding="utf-8") as f:
    channels = json.load(f)

# Set time range dynamically
start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
end = start + timedelta(days=DAYS_TO_FETCH)

tv = ET.Element("tv", attrib={"generator-info-name": "Cignal EPG Fetcher", "generator-info-url": "https://example.com"})

headers = {
    "User-Agent": "Mozilla/5.0"
}

def format_xml(elem, level=0):
    indent = "\n" + ("  " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            format_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

def fetch_epg(name, cid):
    logging.info(f"📡 Fetching EPG for {name} (ID: {cid})")

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

        if not isinstance(data.get("data"), list):
            logging.warning(f"⚠️ Unexpected format for {name}")
            return

        channel_data = [entry for entry in data["data"] if str(entry.get("channel_id", "")).strip() == cid]

        if not channel_data:
            logging.warning(f"⚠️ No matching EPG data for {name} (ID: {cid})")
            return

        # Create <channel> element
        if tv.find(f"./channel[@id='{cid}']") is None:
            channel_elem = ET.SubElement(tv, "channel", {"id": cid})
            ET.SubElement(channel_elem, "display-name").text = name

        for entry in channel_data:
            for program in entry.get("airing", []):
                start_time = program.get("sc_st_dt")
                end_time = program.get("sc_ed_dt")
                pgm = program.get("pgm", {})
                title = pgm.get("lod", [{}])[0].get("n", "No Title")
                desc = pgm.get("lon", [{}])[0].get("n", "No Description")
                category = pgm.get("gn", [{}])[0].get("n", None)  # genre name, optional

                if not start_time or not end_time:
                    continue

                prog_elem = ET.Element("programme", {
                    "start": start_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '') + f" {TIMEZONE_OFFSET}",
                    "stop": end_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '') + f" {TIMEZONE_OFFSET}",
                    "channel": cid
                })
                ET.SubElement(prog_elem, "title", lang="en").text = title
                ET.SubElement(prog_elem, "desc", lang="en").text = desc
                if category:
                    ET.SubElement(prog_elem, "category", lang="en").text = category
                tv.append(prog_elem)

    except Exception as e:
        logging.error(f"❌ Error for {name} (ID: {cid}): {e}")

# Main fetch loop
for name, cid in channels.items():
    fetch_epg(name, str(cid))

format_xml(tv)

# Save to XML
ET.ElementTree(tv).write(EPG_OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
logging.info(f"✅ EPG saved to {EPG_OUTPUT_FILE}")

# Compress to GZ
with open(EPG_OUTPUT_FILE, "rb") as f_in, gzip.open(EPG_COMPRESSED_FILE, "wb") as f_out:
    f_out.writelines(f_in)
logging.info(f"✅ Compressed to {EPG_COMPRESSED_FILE}")

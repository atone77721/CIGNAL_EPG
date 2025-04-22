import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import os

API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/epgs/cignal/airing/grid?limit=1000"
OUTPUT_XML = "cignal_epg.xml"

pst = pytz.timezone("Asia/Manila")

def fetch_epg():
    print("📡 Fetching EPG from API...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Origin": "https://cignal.tv",
        "Referer": "https://cignal.tv/",
    }

    try:
        response = requests.get(API_URL, headers=headers, verify=False, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch EPG: {e}")
        return


    tv = ET.Element("tv", {
        "generator-info-name": "Cignal API EPG",
        "generator-info-url": "https://example.com"
    })

    channels_added = set()

    if isinstance(data.get("data"), list):
        for entry in data["data"]:
            channel = entry.get("channel", {})
            channel_id = channel.get("id", "unknown")
            channel_name = channel.get("name", "Unknown Channel")

            # Skip invalid
            if not channel_id or channel_id == "unknown":
                continue

            # Add channel tag once
            if channel_id not in channels_added:
                ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
                ET.SubElement(ch_elem, "display-name").text = channel_name
                channels_added.add(channel_id)

            for prog in entry.get("airing", []):
                st = prog.get("sc_st_dt")
                et = prog.get("sc_ed_dt")
                pgm = prog.get("pgm", {})
                title = pgm.get("lod", [{}])[0].get("n", "No Title")
                desc = pgm.get("lon", [{}])[0].get("n", title)

                if not st or not et:
                    continue

                try:
                    start_obj = datetime.strptime(st, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pst)
                    end_obj = datetime.strptime(et, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pst)
                except Exception:
                    continue

                prog_elem = ET.Element("programme", {
                    "start": start_obj.strftime('%Y%m%d%H%M%S') + " +0800",
                    "stop": end_obj.strftime('%Y%m%d%H%M%S') + " +0800",
                    "channel": channel_id
                })
                ET.SubElement(prog_elem, "title", lang="en").text = title
                ET.SubElement(prog_elem, "desc", lang="en").text = desc
                tv.append(prog_elem)

    # Write XML to file
    tree = ET.ElementTree(tv)
    if os.path.exists(OUTPUT_XML):
        os.rename(OUTPUT_XML, OUTPUT_XML + ".bak")
        print("🗂️ Backup saved as cignal_epg.xml.bak")

    tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)
    print("✅ EPG saved to cignal_epg.xml")

if __name__ == "__main__":
    fetch_epg()

import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

channels = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
}

BASE_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end_date = start_date + timedelta(days=1)

def fetch_epg(channel_name, channel_id):
    print(f"📡 Fetching EPG for channel ID: {channel_id}")

    params = {
        "start": start_date.isoformat() + "Z",
        "end": end_date.isoformat() + "Z",
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100
    }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    print(f"🔍 Status: {response.status_code}")
    print(f"🔗 URL: {response.url}")

    if response.status_code != 200:
        print(f"❌ Failed to fetch EPG for {channel_name} (Status {response.status_code})")
        print(f"🔴 Response body: {response.text}")
        return []

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON: {e}")
        print(f"🔴 Raw response: {response.text}")
        return []

    programmes = data if isinstance(data, list) else [data]
    print(f"🔎 Sample data for {channel_name}:\n{json.dumps(programmes[0], indent=2) if programmes else 'No data'}")

    return programmes

def build_xmltv(epg_data):
    tv = ET.Element("tv")

    for channel_name, channel_id in channels.items():
        channel_elem = ET.SubElement(tv, "channel", id=channel_id)
        display_name = ET.SubElement(channel_elem, "display-name")
        display_name.text = channel_name

        programmes = fetch_epg(channel_name, channel_id)

        for prog in programmes:
            start = prog.get("sc_st_dt", "").replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"
            end = prog.get("sc_ed_dt", "").replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " +0000"
            title = prog.get("pgm", {}).get("lod", [{}])[0].get("n", "Unknown")

            prog_elem = ET.SubElement(tv, "programme", start=start, stop=end, channel=channel_id)
            title_elem = ET.SubElement(prog_elem, "title", lang="en")
            title_elem.text = title

    tree = ET.ElementTree(tv)
    tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
    print(f"✅ XMLTV written to 'cignal_epg.xml'")

if __name__ == "__main__":
    build_xmltv(channels)

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

channels = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

tv = ET.Element("tv")

def fetch_epg(name, cid):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = (
        f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
        f"?start={start.isoformat()}Z"
        f"&end={end.isoformat()}Z"
        f"&channelId={cid}"
        f"&reg=ph&dt=all&client=pldt-cignal-web"
        f"&pageNumber=1&pageSize=100"
    )

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            data = json_data.get("data", [])

            if not data:
                print(f"⚠️ No EPG data returned for {name}")
                return

            for program in data:
                try:
                    start_time = program["start"]
                    end_time = program["end"]
                    title = program.get("title", "No Title")
                    desc = program.get("description", "No Description")

                    prog = ET.SubElement(tv, "programme", {
                        "start": f"{start_time} +0000",
                        "stop": f"{end_time} +0000",
                        "channel": cid
                    })
                    ET.SubElement(prog, "title", lang="en").text = title
                    ET.SubElement(prog, "desc", lang="en").text = desc
                except KeyError as e:
                    print(f"❌ Missing expected key {e} in program data for {name}")
        else:
            print(f"❌ Failed to fetch EPG for {name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error during request for {name}: {e}")

for name, cid in channels.items():
    ET.SubElement(tv, "channel", {"id": cid})
    ET.SubElement(tv.find(f"./channel[@id='{cid}']"), "display-name").text = name
    fetch_epg(name, cid)

tree = ET.ElementTree(tv)
tree.write("cignal_epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ EPG file written to cignal_epg.xml")

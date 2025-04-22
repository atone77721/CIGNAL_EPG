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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://cignalplay.com",
    "Referer": "https://cignalplay.com"
}

start_date = datetime.utcnow()
end_date = start_date + timedelta(days=1)

start = start_date.strftime('%Y-%m-%dT00:00:00Z')
end = end_date.strftime('%Y-%m-%dT00:00:00Z')

root = ET.Element("tv")

for name, cid in channels.items():
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?start={start}&end={end}&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            channel_elem = ET.SubElement(root, "channel", id=cid)
            ET.SubElement(channel_elem, "display-name").text = name

            for program in data.get("programs", []):
                start_time = program["start"]
                end_time = program["end"]
                title = program.get("title", "No Title")
                desc = program.get("description", "No Description")

                prog_elem = ET.SubElement(root, "programme", start=start_time + " +0000", stop=end_time + " +0000", channel=cid)
                ET.SubElement(prog_elem, "title", lang="en").text = title
                ET.SubElement(prog_elem, "desc", lang="en").text = desc
        else:
            print(f"❌ Failed to fetch EPG: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

# Write to file
tree = ET.ElementTree(root)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
print("✅ EPG file written to epg.xml")

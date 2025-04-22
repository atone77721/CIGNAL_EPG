import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz

# XMLTV root
tv = ET.Element("tv", attrib={
    "generator-info-name": "Cignal API EPG",
    "generator-info-url": "https://example.com"
})

# Time range for EPG: now to +2 days (PST)
pst = pytz.timezone("Asia/Manila")
start_pst = datetime.now(pst).replace(minute=0, second=0, microsecond=0)
end_pst = start_pst + timedelta(days=2)
start_utc = start_pst.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
end_utc = end_pst.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# API endpoint
url = (
    f"https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg?"
    f"start={start_utc}&end={end_utc}&reg=ph&dt=all&client=pldt-cignal-web&pageNumber=1&pageSize=100"
)

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("📡 Fetching data from Cignal API...")
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if isinstance(data.get("data"), list):
        for entry in data["data"]:
            channel_id = entry.get("channel_id", "unknown")
            channel_name = entry.get("channel_name", "Unknown Channel")

            # Add channel to XML if not already present
            ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
            ET.SubElement(ch_elem, "display-name").text = channel_name

            if "airing" in entry:
                for prog in entry["airing"]:
                    st = prog.get("sc_st_dt")
                    et = prog.get("sc_ed_dt")
                    pgm = prog.get("pgm", {})
                    title = pgm.get("lod", [{}])[0].get("n", "No Title")
                    desc = pgm.get("lon", [{}])[0].get("n", "No Description")

                    if not st or not et:
                        continue

                    # Convert UTC to PST time
                    start_obj = datetime.strptime(st, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pst)
                    end_obj = datetime.strptime(et, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pst)

                    start_fmt = start_obj.strftime('%Y%m%d%H%M%S') + " +0800"
                    end_fmt = end_obj.strftime('%Y%m%d%H%M%S') + " +0800"

                    prog_elem = ET.Element("programme", {
                        "start": start_fmt,
                        "stop": end_fmt,
                        "channel": channel_id
                    })
                    ET.SubElement(prog_elem, "title", lang="en").text = title
                    ET.SubElement(prog_elem, "desc", lang="en").text = desc
                    tv.append(prog_elem)
    else:
        print("⚠️ No valid 'data' field in API response.")

except Exception as e:
    print(f"❌ Error fetching EPG: {e}")

# Format output XML
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

format_xml(tv)

# Save to file
output_file = "cignal_epg.xml"
ET.ElementTree(tv).write(output_file, encoding="utf-8", xml_declaration=True)
print(f"✅ EPG saved to {output_file}")

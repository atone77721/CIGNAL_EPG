import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"

HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://cignalplay.com/",
    "Origin": "https://cignalplay.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*"
}

CHANNELS = {
    "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
    "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
    "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
    "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
    "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
}

def fetch_epg(channel_id, start, end):
    params = {
        "start": start + "Z",
        "end": end + "Z",
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100
    }
    print(f"📡 Fetching EPG for channel ID: {channel_id}")
    response = requests.get(API_URL, headers=HEADERS, params=params)
    print("🔍 Status:", response.status_code)
    print("🔗 URL:", response.url)
    if response.status_code != 200:
        print("❌ Error response:", response.text)
        return {}
    return response.json()

def build_combined_xmltv(epg_data_list, output="cignal_epg.xml"):
    root = ET.Element("tv")
    total_programs = 0

    # Add <channel> entries
    for name, site_id in CHANNELS.items():
        ch = ET.SubElement(root, "channel", {"id": site_id})
        name_tag = ET.SubElement(ch, "display-name")
        name_tag.text = name

    # Add <programme> entries
    for channel_epg in epg_data_list:
        for block in channel_epg.get("data", []):
            for item in block.get("airing", []):
                if not item.get("sc_st_dt") or not item.get("sc_ed_dt"):
                    continue

                prog = ET.SubElement(root, "programme", {
                    "start": item["sc_st_dt"] + " +0000",
                    "stop": item["sc_ed_dt"] + " +0000",
                    "channel": item.get("cid", "unknown")
                })

                # Extract title
                title_text = "No Title"
                if isinstance(item.get("lon"), list):
                    for i in item["lon"]:
                        if isinstance(i, dict) and i.get("n"):
                            title_text = i["n"]
                            break

                # Extract description
                desc_text = "No Description"
                if isinstance(item.get("lod"), list):
                    for i in item["lod"]:
                        if isinstance(i, dict) and i.get("n"):
                            desc_text = i["n"]
                            break

                title = ET.SubElement(prog, "title", {"lang": "en"})
                title.text = title_text
                desc = ET.SubElement(prog, "desc", {"lang": "en"})
                desc.text = desc_text
                total_programs += 1

    # Pretty print and write to file
    rough_string = ET.tostring(root, encoding="utf-8")
    pretty_xml = minidom.parseString(rough_string).toprettyxml(indent="  ")
    pretty_xml = "\n".join([line for line in pretty_xml.split("\n") if line.strip()])  # remove empty lines

    with open(output, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"✅ XMLTV written to '{output}' with {total_programs} programmes and {len(CHANNELS)} channels")

if __name__ == "__main__":
    today = datetime.datetime.utcnow()
    end_date = today + datetime.timedelta(days=1)
    start = today.strftime("%Y-%m-%dT00:00:00")
    end = end_date.strftime("%Y-%m-%dT00:00:00")

    all_epg_data = []

    for name, cid in CHANNELS.items():
        try:
            epg_data = fetch_epg(cid, start, end)
            if epg_data.get("data"):
                # 🔎 Print one sample item for inspection
                print(f"🔎 Sample data for {name}:")
                for block in epg_data["data"]:
                    for item in block.get("airing", []):
                        print(json.dumps(item, indent=2))
                        break
                    break

                all_epg_data.append(epg_data)
            else:
                print(f"⚠️ No results found for {name}")
        except Exception as e:
            print(f"❌ Failed to fetch EPG for {name}: {e}")

    if all_epg_data and any(d.get("data") for d in all_epg_data):
        build_combined_xmltv(all_epg_data)
    else:
        print("⚠️ No EPG data retrieved — check channel IDs, API response, or date range.")

import requests
import datetime
import xml.etree.ElementTree as ET

API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"

HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://cignalplay.com/",
    "Origin": "https://cignalplay.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*"
}

# Example CHANNELS dictionary – replace or expand as needed
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
    else:
        data = response.json()
        print("📦 Sample Result:", str(data)[:400])
        return data
    response.raise_for_status()
    return {}

def build_combined_xmltv(epg_data_list, output="cignal_epg.xml"):
    root = ET.Element("tv")
    total_programs = 0

    for channel_epg in epg_data_list:
        for block in channel_epg.get("data", []):
            for item in block.get("airing", []):
                prog = ET.SubElement(root, "programme", {
                    "start": item.get("sc_st_dt", "") + " +0000",
                    "stop": item.get("sc_ed_dt", "") + " +0000",
                    "channel": item.get("cid", "unknown")
                })
                title = ET.SubElement(prog, "title", {"lang": "en"})
                title.text = item.get("lon", [{}])[0].get("n", "No Title")
                desc = ET.SubElement(prog, "desc", {"lang": "en"})
                desc.text = item.get("lod", [{}])[0].get("n", "No Description")
                total_programs += 1

    tree = ET.ElementTree(root)
    tree.write(output, encoding="utf-8", xml_declaration=True)
    print(f"✅ EPG XML written to '{output}' with {total_programs} programmes")

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
                all_epg_data.append(epg_data)
            else:
                print(f"⚠️ No results found for {name}")
        except Exception as e:
            print(f"❌ Failed to fetch EPG for {name}: {e}")

    if all_epg_data and any(d.get("data") for d in all_epg_data):
        build_combined_xmltv(all_epg_data)
    else:
        print("⚠️ No EPG data retrieved — check channel IDs, API response, or date range.")

import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta, timezone
import pytz
import gzip

# Mapping of channel URLs
CHANNEL_URLS = {
    {
  "bilyonaryoch": "http://www.cignalplay.com",
  "rptv": "http://www.cignalplay.com",
  "truefmtv": "http://www.cignalplay.com",
  "cg_hitsnow": "http://www.cignalplay.com",
  "cg_hbohd": "http://www.cignalplay.com",
  "tvup_prd": "http://www.cignalplay.com",
  "tvmaria_prd": "http://www.cignalplay.com",
  "cg_hbofam": "http://www.cignalplay.com",
  "cg_cinemax": "http://www.cignalplay.com",
  "lotusmacau_prd": "http://www.cignalplay.com",
  "cg_hbosign": "http://www.cignalplay.com",
  "cg_hbohits": "http://www.cignalplay.com",
  "cg_tvnmovie": "http://www.cignalplay.com",
  "cg_dreamworktag": "http://www.cignalplay.com",
  "cg_tvnpre": "http://www.cignalplay.com",
  "cg_tagalogmovie": "http://www.cignalplay.com",
  "globaltrekker": "http://www.cignalplay.com",
  "cgtnenglish": "http://www.cignalplay.com",
  "cgnl_nba": "http://www.cignalplay.com",
  "cg_mptv": "http://www.cignalplay.com",
  "cartoon_net_hd": "http://www.cignalplay.com",
  "cnn_hd": "http://www.cignalplay.com",
  "a2z": "http://www.cignalplay.com",
  "dreamworks_hd": "http://www.cignalplay.com",
  "animal_planet": "http://www.cignalplay.com",
  "spotv_hd": "http://www.cignalplay.com",
  "nbn4": "http://www.cignalplay.com",
  "cg_ps_hd1": "http://www.cignalplay.com",
  "blueant_extreme": "http://www.cignalplay.com",
  "tap_sports": "http://www.cignalplay.com",
  "bbcearth_hd": "http://www.cignalplay.com",
  "onesportsplus_hd": "http://www.cignalplay.com",
  "spotv_hd2": "http://www.cignalplay.com",
  "rock_entertainment": "http://www.cignalplay.com",
  "discovery": "http://www.cignalplay.com",
  "cctv4": "http://www.cignalplay.com",
  "pbarush_hd": "http://www.cignalplay.com",
  "arirang": "http://www.cignalplay.com",
  "kbs_world": "http://www.cignalplay.com",
  "onenews_hd": "http://www.cignalplay.com",
  "kix_hd": "http://www.cignalplay.com",
  "lifetime": "http://www.cignalplay.com",
  "bbcworld_news": "http://www.cignalplay.com",
  "hgtv_hd": "http://www.cignalplay.com",
  "uaap_varsity": "http://www.cignalplay.com",
  "travel_channel": "http://www.cignalplay.com",
  "premier_tennishd": "http://www.cignalplay.com",
  "pbo": "http://www.cignalplay.com",
  "hits_hd": "http://www.cignalplay.com",
  "aljazeera": "http://www.cignalplay.com",
  "oneph": "http://www.cignalplay.com",
  "foodnetwork_hd": "http://www.cignalplay.com",
  "depedchannel": "http://www.cignalplay.com",
  "tv5": "http://www.cignalplay.com",
  "history_hd": "http://www.cignalplay.com",
  "fashiontv_hd": "http://www.cignalplay.com",
  "viva": "http://www.cignalplay.com",
  "bloomberg": "http://www.cignalplay.com",
  "nhk_japan": "http://www.cignalplay.com",
  "asianfoodnetwork": "http://www.cignalplay.com",
  "onesports": "http://www.cignalplay.com",
  "nickjr": "http://www.cignalplay.com",
  "warnertv_hd": "http://www.cignalplay.com",
  "animax": "http://www.cignalplay.com",
  "ibc13": "http://www.cignalplay.com",
  "cgtn": "http://www.cignalplay.com",
  "axn": "http://www.cignalplay.com",
  "tapmovies_hd": "http://www.cignalplay.com",
  "taptv": "http://www.cignalplay.com",
  "moonbug_kids": "http://www.cignalplay.com",
  "tapactionflix_hd": "http://www.cignalplay.com",
  "france24": "http://www.cignalplay.com",
  "abc_australia": "http://www.cignalplay.com",
  "hits_movies": "http://www.cignalplay.com",
  "channelnews_asia": "http://www.cignalplay.com",
  "thrill": "http://www.cignalplay.com",
  "crime_investigation": "http://www.cignalplay.com",
  "tech_storm": "http://www.cignalplay.com",
  "buko": "http://www.cignalplay.com",
  "knowledge_channel": "http://www.cignalplay.com",
  "tv5_monde": "http://www.cignalplay.com",
  "nickelodeon": "http://www.cignalplay.com",
  "sari_sari": "http://www.cignalplay.com"
}

    # Add more mappings as needed
}

EPG_API_URL = "https://live-data-store-cdn.api.pldt.firstlight.ai/content/epg"
TIMEZONE = pytz.timezone('Asia/Manila')
USER_AGENT = {'User-Agent': 'Mozilla/5.0'}

def fetch_epg(start_offset_days=0, duration_days=2):
    start_time = (datetime.now(timezone.utc) + timedelta(days=start_offset_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = (datetime.now(timezone.utc) + timedelta(days=start_offset_days + duration_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    params = {
        "start": start_time,
        "end": end_time,
        "reg": "ph",
        "dt": "all",
        "client": "pldt-cignal-web",
        "pageNumber": 1,
        "pageSize": 100,
    }

    try:
        response = requests.get(EPG_API_URL, params=params, headers=USER_AGENT)
        response.raise_for_status()
        return response.json().get('data', [])
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"❌ Failed to fetch EPG data: {e}")
        return []

def convert_to_manila(utc_str):
    if not utc_str:
        return None
    try:
        utc_time = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
        return utc_time.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    except Exception as e:
        print(f"❌ Time conversion error for value '{utc_str}': {e}")
        return None

def format_epg_time(dt):
    return dt.strftime('%Y%m%d%H%M%S') + " +0800"

def build_epg_xml(epg_data):
    tv = ET.Element('tv', {'generator-info-name': 'FHS', 'generator-info-url': 'http://example.com'})
    channels_created = set()

    for item in epg_data:
        airing_data = item.get('airing', [])
        for airing in airing_data:
            ch_info = airing.get('ch', {})
            channel_id = ch_info.get('cs', 'unknown')
            display_name = ch_info.get('ex_id', 'Unknown Channel')

            if channel_id not in channels_created:
                channel_el = ET.SubElement(tv, 'channel', {'id': channel_id})
                ET.SubElement(channel_el, 'display-name', {'lang': 'en'}).text = display_name
                ET.SubElement(channel_el, 'url').text = CHANNEL_URLS.get(channel_id, "http://example.com")
                channels_created.add(channel_id)

            # ✅ Use schedule start/end fields
            start_str = airing.get('sc_st_dt')
            end_str = airing.get('sc_ed_dt')

            if not start_str or not end_str:
                print(f"⚠️ Skipping airing with missing schedule times: {airing}")
                continue

            start_time = convert_to_manila(start_str)
            end_time = convert_to_manila(end_str)

            if not start_time or not end_time:
                continue

            # Title & Description
            pgm_info = airing.get('pgm', {})
            title = pgm_info.get('lon', [{}])[0].get('n', 'No Title')
            description = pgm_info.get('lod', [{}])[0].get('n', 'No Description')

            programme = ET.SubElement(tv, 'programme', {
                'start': format_epg_time(start_time),
                'stop': format_epg_time(end_time),
                'channel': channel_id
            })
            ET.SubElement(programme, 'title', {'lang': 'en'}).text = title
            ET.SubElement(programme, 'desc', {'lang': 'en'}).text = description

    return tv

def save_xml(tv_element, filename='cignal_epg.xml'):
    try:
        xml_str = ET.tostring(tv_element, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        print(f"✅ XML saved to {filename}")

        gz_path = filename + ".gz"
        with gzip.open(gz_path, "wb") as gz_file:
            gz_file.write(pretty_xml.encode("utf-8"))
        print(f"✅ Gzipped XML saved to {gz_path}")

    except Exception as e:
        print(f"❌ Error saving XML: {e}")

def main():
    print("📡 Fetching EPG...")
    epg_data = fetch_epg()
    
    if not epg_data:
        print("❌ No EPG data available.")
        return

    print("🛠 Building XML...")
    tv_xml = build_epg_xml(epg_data)

    print("💾 Saving to file...")
    save_xml(tv_xml)

if __name__ == "__main__":
    main()

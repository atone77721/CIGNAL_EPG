import os
import json
from datetime import datetime

EPG_DIR = "./epg"
os.makedirs(EPG_DIR, exist_ok=True)

def parse_programs(epg_json):
    try:
        programs = []
        for program in epg_json["data"]:
            for airing in program.get("airing", []):
                try:
                    title = airing["pgm"]["lod"][0]["n"]
                    start_time = airing["sc_st_dt"]
                    end_time = airing["sc_ed_dt"]
                    programs.append({
                        "title": title,
                        "start": start_time,
                        "end": end_time
                    })
                except KeyError as e:
                    print(f"⚠️ Missing expected key in airing: {e}")
        return programs
    except Exception as e:
        print(f"⚠️ Error parsing programs: {e}")
        return []

def load_epg(channel_id):
    file_path = os.path.join(EPG_DIR, f"{channel_id}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading EPG file {file_path}: {e}")
        return None

def main():
    for file_name in os.listdir(EPG_DIR):
        if file_name.endswith(".json"):
            channel_id = file_name.replace(".json", "")
            print(f"\n📡 Fetching EPG for {channel_id} (ID: {channel_id})")

            epg_json = load_epg(channel_id)
            if epg_json:
                print(f"📦 Raw JSON for {channel_id}:")
                print(json.dumps(epg_json.get("data", [])[:1], indent=2))  # Print sample for brevity

                programs = parse_programs(epg_json)
                print(f"▶️ Program data: {programs[:3]}")  # Print sample

                if not programs:
                    print(f"⚠️ Failed to parse JSON for {channel_id}: Missing or malformed 'airing' data")
            else:
                print(f"⚠️ No JSON data found for {channel_id}")

if __name__ == "__main__":
    main()

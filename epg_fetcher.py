import requests
 import xml.etree.ElementTree as ET
 from datetime import datetime, timedelta
 import json
 import os
 
 channels = {
     "Rptv": "44B03994-C303-4ACE-997C-91CAC493D0FC",
     "Cg Hitsnow": "68C2D95A-A2A4-4C2B-93BE-41893C61210C",
     "Cg Hbohd": "B741DD7A-A7F8-4F8A-A549-9EF411020F9D",
     "Tvup Prd": "C0B38DBD-BE4F-4044-9D85-D827D8DC64C4",
     "Tvmaria Prd": "2C55AD7F-3589-48DA-BEC4-005200215975"
 }
 # Load channel map from JSON
 with open("cignal-map-channel.json") as f:
     channels = json.load(f)
 
 headers = {
     "User-Agent": "Mozilla/5.0",
 @@ -18,24 +16,6 @@
 start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
 end = start + timedelta(days=1)
 
 tv = ET.Element("tv")
 
 def format_xml(elem, level=0):
     """Pretty-print XML indentation"""
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
     print(f"📡 Fetching EPG for {name} (ID: {cid})")
     url = (
 @@ -46,59 +26,48 @@ def fetch_epg(name, cid):
         f"&pageNumber=1&pageSize=100"
     )
 
     programmes = []
 
     try:
         response = requests.get(url, headers=headers)
         if response.status_code == 200:
             data = response.json()
             programs = data.get("data", [])
         response.raise_for_status()
         data = response.json()
 
         if not isinstance(data.get("data"), list):
             print(f"⚠️ Unexpected format for {name}")
             return
 
         tv = ET.Element("tv")
         ET.SubElement(tv, "channel", {"id": cid})
         ET.SubElement(tv.find(f"./channel[@id='{cid}']"), "display-name").text = name
 
             for program in programs:
                 airings = program.get("airing", [])
                 for airing in airings:
                     if airing.get("cid") != cid:
         for entry in data["data"]:
             if "airing" in entry:
                 for program in entry["airing"]:
                     start_time = program.get("sc_st_dt")
                     end_time = program.get("sc_ed_dt")
                     pgm = program.get("pgm", {})
                     title = pgm.get("lod", [{}])[0].get("n", "No Title")
                     desc = pgm.get("lon", [{}])[0].get("n", "No Description")
 
                     if not start_time or not end_time:
                         continue
 
                     try:
                         start_time = airing["sc_st_dt"]
                         end_time = airing["sc_ed_dt"]
                         title = airing.get("pgm", {}).get("lod", [{}])[0].get("n", "No Title")
                         desc = airing.get("pgm", {}).get("lon", [{}])[0].get("n", "No Description")
                     prog = ET.SubElement(tv, "programme", {
                         "start": f"{start_time.replace('-', '').replace(':', '')} +0000",
                         "stop": f"{end_time.replace('-', '').replace(':', '')} +0000",
                         "channel": cid
                     })
                     ET.SubElement(prog, "title", lang="en").text = title
                     ET.SubElement(prog, "desc", lang="en").text = desc
 
                         prog = ET.Element("programme", {
                             "start": f"{start_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                             "stop": f"{end_time.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')} +0000",
                             "channel": cid
                         })
                         ET.SubElement(prog, "title", lang="en").text = title
                         ET.SubElement(prog, "desc", lang="en").text = desc
                         programmes.append((start_time, prog))
                     except Exception as e:
                         print(f"❌ Error parsing airing for {name}: {e}")
         else:
             print(f"❌ HTTP Error {response.status_code} for {name}")
     except Exception as e:
         print(f"❌ Request error for {name}: {e}")
         # Write to individual XML file
         filename = f"epg_{name.replace(' ', '_').lower()}.xml"
         tree = ET.ElementTree(tv)
         tree.write(filename, encoding="utf-8", xml_declaration=True)
         print(f"✅ EPG file written to {filename}")
 
     # Sort by start time
     programmes.sort(key=lambda x: x[0])
     for _, prog in programmes:
         tv.append(prog)
     except Exception as e:
         print(f"❌ Error fetching/parsing EPG for {name}: {e}")
 
 # Add channel info and fetch EPGs
 # Loop through all channels
 for name, cid in channels.items():
     ch = ET.SubElement(tv, "channel", {"id": cid})
     ET.SubElement(ch, "display-name").text = name
     fetch_epg(name, cid)
 
 # Pretty-print and write XML
 format_xml(tv)
 output_file = "cignal_epg.xml"
 ET.ElementTree(tv).write(output_file, encoding="utf-8", xml_declaration=True)
 print(f"✅ EPG saved to {output_file}")
 
 # Preview the output (for GitHub Actions/logs)
 print("\n📄 Preview of EPG XML:\n" + "-" * 40)
 with open(output_file, "r", encoding="utf-8") as f:
     print(f.read())

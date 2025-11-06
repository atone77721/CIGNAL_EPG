import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import xml.etree.ElementTree as ET

# ──────────────────────────────
# 🛰️ SCRAPER
# ──────────────────────────────
async def scrape_tv5_schedule():
    url = "https://www.tv5.com.ph/schedule"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("🌐 Loading TV5 schedule page...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("div.tab-data div.grid", timeout=20000)
        except Exception as e:
            print("⚠️ Warning:", e)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    epg_data = {}

    # Loop through each day grid
    for grid in soup.select("div.tab-data div.grid"):
        classes = grid.get("class", [])
        day_name = next((c for c in classes if c != "grid"), None)
        if not day_name:
            continue

        shows = []
        for box in grid.select("div.box"):
            time = box.select_one(".time p")
            title = box.select_one(".title")
            desc = box.select_one(".desc")
            image = box.select_one(".image")
            img_url = None
            if image and image.has_attr("style"):
                match = re.search(r'url\(["\']?(.*?)["\']?\)', image["style"])
                if match:
                    img_url = match.group(1)
            shows.append({
                "time": time.get_text(strip=True) if time else "",
                "title": title.get_text(strip=True) if title else "",
                "desc": desc.get_text(strip=True) if desc else "",
                "image": img_url
            })
        epg_data[day_name] = shows

    total_programs = sum(len(v) for v in epg_data.values())
    print(f"✅ Found {total_programs} total programs across all days")
    return epg_data


# ──────────────────────────────
# 🧩 XMLTV GENERATOR (with gap filling)
# ──────────────────────────────
def generate_xmltv(epg_data, output_file="tv5.xml"):
    import xml.etree.ElementTree as ET
    from datetime import datetime, timedelta

    tv = ET.Element("tv")
    channel_id = "tv5.ph"

    ch = ET.SubElement(tv, "channel", id=channel_id)
    ET.SubElement(ch, "display-name").text = "TV5"
    ET.SubElement(ch, "icon", src="https://www.tv5.com.ph/assets/images/tv5-new-logo.png")

    today = datetime.now()
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

    for i, day in enumerate(days):
        shows = epg_data.get(day, [])
        if not shows:
            continue

        date_offset = timedelta(days=(i - today.weekday()) % 7)
        day_date = today + date_offset

        parsed = []
        for s in shows:
            if not s["time"]:
                continue
            for fmt in ("%I:%M %p", "%I %p"):
                try:
                    t = datetime.strptime(s["time"], fmt)
                    parsed.append({**s, "start": day_date.replace(hour=t.hour, minute=t.minute)})
                    break
                except ValueError:
                    continue

        parsed.sort(key=lambda x: x["start"])
        for idx, s in enumerate(parsed):
            start = s["start"]
            stop = parsed[idx + 1]["start"] if idx + 1 < len(parsed) else start + timedelta(hours=1)

            prog = ET.SubElement(tv, "programme", {
                "start": start.strftime("%Y%m%d%H%M%S +0800"),
                "stop": stop.strftime("%Y%m%d%H%M%S +0800"),
                "channel": channel_id
            })
            ET.SubElement(prog, "title", lang="en").text = s["title"]
            if s.get("desc"): ET.SubElement(prog, "desc", lang="en").text = s["desc"]
            if s.get("image"): ET.SubElement(prog, "icon", src=s["image"])

            # --- insert filler for gaps ---
            if idx + 1 < len(parsed) and stop < parsed[idx + 1]["start"]:
                filler = ET.SubElement(tv, "programme", {
                    "start": stop.strftime("%Y%m%d%H%M%S +0800"),
                    "stop": parsed[idx + 1]["start"].strftime("%Y%m%d%H%M%S +0800"),
                    "channel": channel_id
                })
                ET.SubElement(filler, "title", lang="en").text = "No Program Scheduled"

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"📺 XMLTV saved: {output_file} (blank intervals filled)")

# ──────────────────────────────
# 🚀 MAIN
# ──────────────────────────────
if __name__ == "__main__":
    epg = asyncio.run(scrape_tv5_schedule())
    generate_xmltv(epg)

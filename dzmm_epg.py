import datetime
import xml.etree.ElementTree as ET

CHANNEL_ID = "DZMM.TeleRadyo.ph"
CHANNEL_NAME = "DZMM Radyo Patrol 630 / TeleRadyo Serbisyo"
CHANNEL_ICON = "https://upload.wikimedia.org/wikipedia/en/9/9a/DZMM_Teleradyo_logo_2023.png"
OUTPUT_FILE = "dzmm.xml"

schedule = {
    "monday": [
        ("04:00", "05:00", "Radyo Patrol Balita Alas-Kwatro"),
        ("05:00", "06:00", "Ronda Pasada"),
        ("06:00", "07:00", "Gising Pilipinas"),
        ("07:00", "07:30", "Radyo Patrol Balita Alas-Siyete"),
        ("07:30", "08:00", "Gising Pilipinas"),
        ("08:00", "09:00", "Tandem ng Bayan"),
        ("09:00", "10:00", "Balitapatan"),
        ("10:00", "11:00", "Kabayan"),
        ("11:00", "12:00", "Nagseserbisyo, Niña at Migs"),
        ("12:00", "12:30", "Headline Ngayon"),
        ("12:30", "13:00", "Maalaala Mo Kaya sa DZMM"),
        ("13:00", "14:00", "Hello Attorney"),
        ("14:00", "15:00", "Aksyon Ngayon"),
        ("15:00", "16:00", "Ako 'To si Tyang Amy"),
        ("16:00", "16:30", "Headline sa Hapon"),
        ("16:30", "17:30", "ATM: Anong Take Mo?"),
        ("17:30", "18:30", "DZMM Radyo Patrol 630: Arangkada Balita / DZMM TeleRadyo: Isyu Spotted"),
        ("18:30", "20:00", "TV Patrol sa DZMM"),
        ("20:00", "21:00", "Spot Report"),
        ("21:00", "22:00", "Alam Na This!"),
        ("22:00", "24:00", "Love Konek"),
    ],
    "tuesday": "same",
    "wednesday": "same",
    "thursday": "same",
    "friday": "same",
    "saturday": [
        ("04:00", "06:00", "Yan Tayo"),
        ("06:00", "07:00", "Ano'ng Ganap?"),
        ("07:00", "07:15", "Radyo Patrol Balita Alas-Siyete Weekend"),
        ("07:15", "08:00", "Ano'ng Ganap?"),
        ("08:00", "09:00", "Balita AnteMano"),
        ("09:00", "10:00", "Iwas Sakit, Iwas Gastos"),
        ("10:00", "11:00", "Win Today"),
        ("11:00", "12:00", "Serbisyong DSWD For Every Juan"),
        ("12:00", "13:30", "Ligtas Dapat"),
        ("13:30", "15:00", "Kwatro Alas"),
        ("15:00", "16:00", "Safe Space"),
        ("16:00", "17:15", "Pasado Serbisyo"),
        ("17:15", "18:15", "TV Patrol Weekend sa DZMM"),
        ("18:15", "20:00", "Story Outlook"),
        ("20:00", "22:00", "Feel Kita"),
        ("22:00", "24:00", "K-Paps Playlist"),
    ],
    "sunday": [
        ("00:00", "04:00", "Private Talks"),
        ("04:00", "06:00", "Sunny Side Up"),
        ("06:00", "07:00", "Ano'ng Ganap?"),
        ("07:00", "07:15", "Radyo Patrol Balita Alas-Siyete Weekend"),
        ("07:15", "08:00", "Ano'ng Ganap?"),
        ("08:00", "09:30", "Aprub Yan!"),
        ("09:30", "11:00", "Panalong Diskarte"),
        ("11:00", "12:00", "Wow Sikat"),
        ("12:00", "13:30", "Bongga Ka Jhai!"),
        ("13:30", "15:30", "Konek Ka D'yan"),
        ("15:30", "17:30", "Travel ni Ahwel"),
        ("17:30", "18:15", "TV Patrol Weekend sa DZMM"),
        ("18:15", "19:30", "Story Outlook"),
        ("19:30", "20:30", "GBU: God Bless You"),
        ("20:30", "22:00", "K-Paps Playlist"),
        ("22:00", "24:00", "Rosary Hour"),
    ],
}

# replicate weekday schedule
for d in ["tuesday", "wednesday", "thursday", "friday"]:
    schedule[d] = schedule["monday"]

def parse_time_safe(time_str, base_date):
    """Handle '24:00' as next day midnight."""
    if time_str == "24:00":
        return datetime.datetime.combine(base_date.date() + datetime.timedelta(days=1), datetime.time(0, 0))
    return datetime.datetime.combine(base_date.date(), datetime.time.fromisoformat(time_str))

def xmltv_time(dt):
    return dt.strftime("%Y%m%d%H%M%S +0800")

def generate_xmltv():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    monday = now - datetime.timedelta(days=now.weekday())
    root = ET.Element("tv")

    # Channel info
    ch = ET.SubElement(root, "channel", id=CHANNEL_ID)
    ET.SubElement(ch, "display-name").text = CHANNEL_NAME
    ET.SubElement(ch, "icon", src=CHANNEL_ICON)

    for i, (day, programs) in enumerate(schedule.items()):
        base_date = monday + datetime.timedelta(days=i)
        for start, end, title in programs:
            start_dt = parse_time_safe(start, base_date)
            end_dt = parse_time_safe(end, base_date)
            prog = ET.SubElement(root, "programme", {
                "start": xmltv_time(start_dt),
                "stop": xmltv_time(end_dt),
                "channel": CHANNEL_ID
            })
            ET.SubElement(prog, "title", lang="tl").text = title

    ET.ElementTree(root).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ EPG generated successfully → {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_xmltv()

import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

CHANNEL_ID = "DZMM"
CHANNEL_NAME = "DZMM Radyo Patrol 630"

WEEKDAY_SCHEDULE = [
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
    ("15:00", "16:00", "Ako ‘To si Tyang Amy"),
    ("16:00", "16:30", "Headline sa Hapon"),
    ("16:30", "17:30", "ATM: Anong Take Mo?"),
    ("17:30", "18:30", "Arangkada Balita / Isyu Spotted"),
    ("18:30", "20:00", "TV Patrol sa DZMM"),
    ("20:00", "21:00", "Spot Report"),
    ("21:00", "22:00", "Alam Na This!"),
    ("22:00", "24:00", "Love Konek"),
]

SATURDAY_SCHEDULE = [
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
]

SUNDAY_SCHEDULE = [
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
]


def generate_xmltv():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())  # start of current week

    tv = ET.Element("tv")
    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    ET.SubElement(channel, "display-name").text = CHANNEL_NAME

    for i in range(7):
        current_day = monday + datetime.timedelta(days=i)
        weekday = current_day.weekday()

        if weekday < 5:
            schedule = WEEKDAY_SCHEDULE
        elif weekday == 5:
            schedule = SATURDAY_SCHEDULE
        else:
            schedule = SUNDAY_SCHEDULE

        for start, end, title in schedule:
            try:
                start_time = datetime.time.fromisoformat(start)
                if end == "24:00":
                    end_dt = datetime.datetime.combine(current_day + datetime.timedelta(days=1), datetime.time(0, 0))
                else:
                    end_time = datetime.time.fromisoformat(end)
                    end_dt = datetime.datetime.combine(current_day, end_time)
                start_dt = datetime.datetime.combine(current_day, start_time)

                prog = ET.SubElement(tv, "programme", {
                    "start": start_dt.strftime("%Y%m%d%H%M%S +0800"),
                    "stop": end_dt.strftime("%Y%m%d%H%M%S +0800"),
                    "channel": CHANNEL_ID
                })
                ET.SubElement(prog, "title").text = title
            except ValueError:
                print(f"Skipping invalid time format: {start} - {end}")

    # Pretty print XML output
    rough_string = ET.tostring(tv, "utf-8")
    reparsed = xml.dom.minidom.parseString(rough_string)
    with open("dzmm.xml", "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))


if __name__ == "__main__":
    generate_xmltv()

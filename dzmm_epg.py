import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

CHANNEL_ID = "DZMM"
CHANNEL_NAME = "DZMM Radyo Patrol 630"

# ---------------------------
# EPG SYNOPSIS DICTIONARY
# ---------------------------
EPG_DESC = {
    "Radyo Patrol Balita Alas-Kwatro": "Pinakabagong balita at live reports mula sa Radyo Patrol para simulan ang araw nang may tamang impormasyon.",
    "Ronda Pasada": "Balitang kalsada, trapiko, transportasyon, at public service para sa mga motorista at commuters.",
    "Gising Pilipinas": "Balitang pambansa, komentaryo, at morning updates para ihanda ka sa buong araw.",
    "Radyo Patrol Balita Alas-Siyete": "Maikling roundup ng top stories at breaking news sa unang bahagi ng umaga.",
    "Tandem ng Bayan": "Talakayan ng mainit na isyu ng araw kasama ang ekspertong opinyon at live reports.",
    "Balitapatan": "Malalimang public affairs at news analysis kasama ang mga pangunahing balita ng umaga.",
    "Kabayan": "Balita, public service, at komentaryo sa mga isyung may direktang epekto sa mga Pilipino.",
    "Nagseserbisyo, Niña at Migs": "Serbisyong publiko at talakayang tumutugon sa pang-araw-araw na pangangailangan ng mamamayan.",
    "Headline Ngayon": "Pang-araw na major headlines at breaking developments sa loob at labas ng bansa.",
    "Maalaala Mo Kaya sa DZMM": "Mga kuwento ng buhay at inspirasyon batay sa totoong karanasan.",
    "Hello Attorney": "Legal advice at paliwanag tungkol sa karapatan, batas, at mga isyung legal ng publiko.",
    "Aksyon Ngayon": "On-air public service, reklamo, at agarang aksyon para sa mga suliranin ng mga mamamayan.",
    "Ako ‘To si Tyang Amy": "Talk program tungkol sa lifestyle, pamilya, kabuhayan, at personal na pag-unlad.",
    "Headline sa Hapon": "Panghapon na newscast na may updated headlines at sitwasyon ng araw.",
    "ATM: Anong Take Mo?": "Interactive talk-show kung saan ibinabahagi ng publiko ang opinyon nila sa trending issues.",
    "Arangkada Balita / Isyu Spotted": "Pinagsamang balita at pagbusisi sa mga isyung dapat bantayan.",
    "TV Patrol sa DZMM": "Simulcast ng TV Patrol na naghahatid ng pambansang balita, special reports at breaking news.",
    "Spot Report": "Pagbabantay sa mga insidente, aksyon, at kaganapang pang-komunidad.",
    "Alam Na This!": "Entertainment news, lifestyle trends, at kuwento ng showbiz personalities.",
    "Love Konek": "Romantic advice, relationship stories, at heart-to-heart talk para sa mga nakikinig sa gabi.",

    # Saturday
    "Yan Tayo": "Weekend news, talk, at public service na sumasalo sa unang bahagi ng Sabado.",
    "Ano'ng Ganap?": "Entertainment, lifestyle, at trending happenings sa bansa.",
    "Radyo Patrol Balita Alas-Siyete Weekend": "Maikling weekend newscast na may top-of-the-morning headlines.",
    "Balita AnteMano": "Maagang balitaan at take sa mga isyung umiinit sa komunidad.",
    "Iwas Sakit, Iwas Gastos": "Praktikal na health tips at payo para sa pangangalaga ng kalusugan.",
    "Win Today": "Inspirational stories, success mindset, at personal development advice.",
    "Serbisyong DSWD For Every Juan": "Information at public service mula sa DSWD tungkol sa programang pang-komunidad.",
    "Ligtas Dapat": "Safety awareness, emergency tips, at public safety discussions.",
    "Kwatro Alas": "Talk program tungkol sa mainit na isyung panlipunan at pang-komunidad.",
    "Safe Space": "Friendly discussions on mental wellness, relationships, and personal issues.",
    "Pasado Serbisyo": "On-air assistance at solusyon para sa concerns ng publiko.",
    "TV Patrol Weekend sa DZMM": "Weekend simulcast ng pangunahing newscast ng ABS-CBN.",
    "Story Outlook": "Feature stories, human interest segments, at inspirational narratives.",
    "Feel Kita": "Feel-good music, stories, at talk to lighten up your weekend night.",
    "K-Paps Playlist": "Non-stop K-pop hits at fan-updates para sa K-culture fans.",

    # Sunday
    "Private Talks": "Late-night intimate conversations tungkol sa personal stories at real-life experiences.",
    "Sunny Side Up": "Light morning news, features, at good-vibes stories para sa iyong Sunday start.",
    "Aprub Yan!": "Discussion on practical tips, approved solutions, at ideas para sa pamilya at kabuhayan.",
    "Panalong Diskarte": "Tips, life hacks, at livelihood strategies para mapaunlad ang pamumuhay.",
    "Wow Sikat": "Features at kuwento ng sikat na personalities at trending achievers.",
    "Bongga Ka Jhai!": "Fun talk show na may music, chika, at engaging weekend stories.",
    "Konek Ka D'yan": "Interactive program sa social issues, relationships, at community concerns.",
    "Travel ni Ahwel": "Travel stories, tips, destinations, at budget-friendly adventures.",
    "GBU: God Bless You": "Faith-based reflections at inspirational messages.",
    "Rosary Hour": "Prayer hour featuring the Holy Rosary and spiritual reflections."
}

# ---------------------------
# SCHEDULES (unchanged)
# ---------------------------
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

SATURDAY_SCHEDULE = [...]
SUNDAY_SCHEDULE = [...]

# ---------------------------
# XMLTV GENERATOR
# ---------------------------
def generate_xmltv():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())

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
                start_dt = datetime.datetime.combine(current_day, start_time)

                if end == "24:00":
                    end_dt = datetime.datetime.combine(
                        current_day + datetime.timedelta(days=1),
                        datetime.time(0, 0)
                    )
                else:
                    end_time = datetime.time.fromisoformat(end)
                    end_dt = datetime.datetime.combine(current_day, end_time)

                prog = ET.SubElement(tv, "programme", {
                    "start": start_dt.strftime("%Y%m%d%H%M%S +0800"),
                    "stop": end_dt.strftime("%Y%m%d%H%M%S +0800"),
                    "channel": CHANNEL_ID
                })

                ET.SubElement(prog, "title").text = title

                # Add EPG description
                desc = EPG_DESC.get(title, "Walang available na description.")
                ET.SubElement(prog, "desc").text = desc

            except ValueError:
                print(f"Skipping invalid time format: {start} - {end}")

    # Pretty XML formatting
    rough = ET.tostring(tv, "utf-8")
    pretty = xml.dom.minidom.parseString(rough)
    with open("dzmm.xml", "w", encoding="utf-8") as f:
        f.write(pretty.toprettyxml(indent="  "))


if __name__ == "__main__":
    generate_xmltv()

import re
import urllib.request
from collections import OrderedDict

# ============================================================
# Deutsche IPTV-Liste
# ============================================================
#
# Quellen:
#   - Deutschland
#   - Niedersachsen
#   - Hamburg
#   - Schleswig-Holstein
#   - Mecklenburg-Vorpommern
#
# Ziel:
#   - Top 50 gezielt priorisieren
#   - keine Musik
#   - kein Shopping
#   - keine Erotik
#   - keine ausländischen Sender mit deutschem Ton
#   - keine technischen HD/SD-Doppelungen
#   - regionale Sender aus Niedersachsen bevorzugen
#
# ============================================================

SOURCES = [
    ("Germany", "https://iptv-org.github.io/iptv/countries/de.m3u"),
    ("Niedersachsen", "https://iptv-org.github.io/iptv/subdivisions/de-ni.m3u"),
    ("Hamburg", "https://iptv-org.github.io/iptv/subdivisions/de-hh.m3u"),
    ("Schleswig-Holstein", "https://iptv-org.github.io/iptv/subdivisions/de-sh.m3u"),
    ("Mecklenburg-Vorpommern", "https://iptv-org.github.io/iptv/subdivisions/de-mv.m3u"),
]

OUTPUT = "deutsch.m3u"


# ============================================================
# TOP 50
#
# Die Reihenfolge hier bestimmt die Reihenfolge in der M3U.
# Nur echte Sendernamen / gezielte Namensvarianten verwenden.
# ============================================================

TOP_PRIORITY = [

    # --------------------------------------------------------
    # Öffentlich-rechtlich
    # --------------------------------------------------------

    "Das Erste",
    "ZDF",
    "3sat",
    "ARTE",
    "Phoenix",
    "ZDFneo",
    "ZDFinfo",
    "One",
    "tagesschau24",
    "ARD-alpha",
    "DW",

    # --------------------------------------------------------
    # Niedersachsen / Norddeutschland
    # --------------------------------------------------------

    "NDR Niedersachsen",
    "RTL Nord Niedersachsen & Bremen",
    "Radio Bremen TV",
    "Hamburg 1",
    "17:30 SAT.1 Regional Hamburg & Schleswig-Holstein",

    # --------------------------------------------------------
    # Andere Dritte Programme
    # jeweils nur EIN Sender / Hauptfeed
    # --------------------------------------------------------

    "WDR Köln",
    "BR Fernsehen",
    "hr-fernsehen",
    "MDR Sachsen",
    "MDR Sachsen-Anhalt",
    "MDR Thüringen",
    "rbb",
    "SWR",
    "SR Fernsehen",

    # --------------------------------------------------------
    # Private
    # --------------------------------------------------------

    "RTL",
    "RTLZWEI",
    "ProSieben",
    "SAT.1",
    "VOX",
    "Kabel Eins",
    "kabel eins Doku",
    "NITRO",
    "VOXup",
    "sixx",
    "ProSieben MAXX",
    "SAT.1 Gold",
    "TELE 5",
    "DMAX",

    # --------------------------------------------------------
    # Nachrichten
    # --------------------------------------------------------

    "WELT",
    "ntv",
    "Euronews",
    "N24 Doku",

    # --------------------------------------------------------
    # Religion
    # --------------------------------------------------------

    "Bibel TV",
    "K-TV",
    "EWTN",
    "ERF 1",
]


# ============================================================
# AUSGESCHLOSSENE SENDER / BEGRIFFE
# ============================================================

EXCLUDE_KEYWORDS = [

    # Shopping
    "shopping",
    "teleshopping",
    "home shopping",
    "qvc",
    "hse",
    "1-2-3 tv",
    "123 tv",

    # Erotik
    "erotik",
    "xxx",
    "adult",
    "porn",

    # Musik
    "music",
    "musik",
    "deluxe music",
    "schlager",

    # Ausländische / nicht gewünschte Varianten
    "zee one",
    "zee tv",
    "one adria",
]


# ============================================================
# KINDER
#
# KiKA wird NICHT gelöscht.
# Er darf weiter unten in der Gesamtliste erscheinen,
# steht aber nicht in den Top 50.
# ============================================================


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def download(url):
    print("Lade:", url)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def parse_m3u(text):
    """
    Liest EXTINF + URL Paare.
    """

    lines = text.splitlines()
    entries = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if line.startswith("#EXTINF:"):

            info = line
            url = ""

            if i + 1 < len(lines):
                url = lines[i + 1].strip()

            if url and not url.startswith("#"):

                match = re.search(
                    r",(.+)$",
                    info
                )

                if match:
                    name = match.group(1).strip()
                else:
                    name = ""

                entries.append({
                    "info": info,
                    "name": name,
                    "url": url,
                })

            i += 2

        else:
            i += 1

    return entries


def normalize_name(name):
    """
    Vereinheitlicht Sendernamen für Vergleiche.
    """

    name = name.lower()

    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        name
    )

    return " ".join(name.split())


def is_excluded(name):
    """
    Entfernt unerwünschte Sender.
    """

    normalized = normalize_name(name)

    for keyword in EXCLUDE_KEYWORDS:

        if normalize_name(keyword) in normalized:
            return True

    return False


def is_one_germany(name):
    """
    ONE darf nur der deutsche ARD-Sender sein.

    Dadurch werden z.B.
      ONE Adria
      One TV
      andere One-Kanäle
    nicht fälschlich als ONE erkannt.
    """

    normalized = normalize_name(name)

    return normalized in [
        "one",
        "one germany",
        "one deutschland",
        "one ard",
    ]


def is_dw_germany(name):
    """
    Deutsche Welle: nur der deutsche Feed.
    """

    normalized = normalize_name(name)

    return normalized in [
        "dw",
        "deutsche welle",
        "dw deutsch",
        "deutsche welle deutsch",
    ]


def priority_index(name):
    """
    Gibt die Position in TOP_PRIORITY zurück.

    - 0 = höchste Priorität
    - 9999 = nicht Top 50
    """

    normalized = normalize_name(name)

    for index, wanted in enumerate(TOP_PRIORITY):

        wanted_normalized = normalize_name(wanted)

        # ONE speziell behandeln
        if wanted == "One":

            if is_one_germany(name):
                return index

            continue

        # DW speziell behandeln
        if wanted == "DW":

            if is_dw_germany(name):
                return index

            continue

        # Exakte Übereinstimmung bevorzugen
        if normalized == wanted_normalized:
            return index

    return 9999


def category(name):
    """
    Vergibt eine sinnvolle Gruppe für Kodi.
    """

    normalized = normalize_name(name)

    # Öffentlich-rechtlich
    public = [
        "das erste",
        "zdf",
        "3sat",
        "arte",
        "phoenix",
        "zdfneo",
        "zdfinfo",
        "one",
        "tagesschau24",
        "ard alpha",
        "dw",
        "deutsche welle",
    ]

    for keyword in public:

        if normalize_name(keyword) in normalized:
            return "01 Öffentlich-Rechtlich"

    # Niedersachsen / Norden
    north = [
        "ndr niedersachsen",
        "rtl nord niedersachsen",
        "radio bremen",
        "hamburg 1",
        "sat 1 regional",
    ]

    for keyword in north:

        if normalize_name(keyword) in normalized:
            return "02 Niedersachsen & Norddeutschland"

    # Dritte
    third = [
        "wdr",
        "br fernsehen",
        "hr fernsehen",
        "mdr",
        "rbb",
        "swr",
        "sr fernsehen",
    ]

    for keyword in third:

        if normalize_name(keyword) in normalized:
            return "03 Dritte Programme"

    # Nachrichten
    news = [
        "welt",
        "ntv",
        "euronews",
        "n24 doku",
    ]

    for keyword in news:

        if normalize_name(keyword) in normalized:
            return "05 Nachrichten"

    # Religion
    religion = [
        "bibel tv",
        "k tv",
        "ewtn",
        "erf",
    ]

    for keyword in religion:

        if normalize_name(keyword) in normalized:
            return "09 Religion"

    # Kinder
    children = [
        "kika",
        "super rtl",
        "nickelodeon",
    ]

    for keyword in children:

        if normalize_name(keyword) in normalized:
            return "08 Kinder"

    # Doku
    documentary = [
        "kabel eins doku",
        "dmax",
        "n24 doku",
        "dokument",
        "discovery",
        "history",
        "wissen",
    ]

    for keyword in documentary:

        if normalize_name(keyword) in normalized:
            return "06 Dokumentation & Wissen"

    # Sport
    sports = [
        "sport",
        "eurosport",
        "tennis",
        "fussball",
    ]

    for keyword in sports:

        if normalize_name(keyword) in normalized:
            return "10 Sport"

    # Private
    private = [
        "rtl",
        "rtlzwei",
        "pro sieben",
        "sat 1",
        "vox",
        "kabel eins",
        "nitro",
        "voxup",
        "sixx",
        "pro sieben maxx",
        "sat 1 gold",
        "tele 5",
    ]

    for keyword in private:

        if normalize_name(keyword) in normalized:
            return "04 Private"

    return "11 Weitere deutsche Sender"


def clean_info(info, name, group):
    """
    Behält vorhandene M3U-Attribute,
    entfernt group-title und setzt unsere Gruppe.
    """

    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

    info = re.sub(
        r'\s+tvg-group="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

    # alten Sendernamen entfernen
    info_without_name = re.sub(
        r",.*$",
        "",
        info
    )

    return (
        f'{info_without_name} '
        f'group-title="{group}",'
        f'{name}'
    )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    all_entries = []

    # --------------------------------------------------------
    # Quellen laden
    # --------------------------------------------------------

    for source_name, url in SOURCES:

        try:

            text = download(url)

            entries = parse_m3u(text)

            print(
                f"{source_name}: "
                f"{len(entries)} Einträge"
            )

            all_entries.extend(entries)

        except Exception as error:

            print(
                f"FEHLER bei {source_name}: "
                f"{error}"
            )

    print()
    print(
        "Insgesamt geladen:",
        len(all_entries)
    )

    # --------------------------------------------------------
    # Filtern
    # --------------------------------------------------------

    filtered = []

    for entry in all_entries:

        name = entry["name"]
        url = entry["url"]

        if not name or not url:
            continue

        if is_excluded(name):
            continue

        filtered.append(entry)

    print(
        "Nach Ausschlüssen:",
        len(filtered)
    )

    # --------------------------------------------------------
    # Echte Dubletten entfernen
    #
    # Sendername + URL
    #
    # Dadurch verschwinden identische Wiederholungen.
    # --------------------------------------------------------

    unique = OrderedDict()

    for entry in filtered:

        name = entry["name"]
        url = entry["url"]

        key = (
            normalize_name(name),
            url
        )

        if key not in unique:
            unique[key] = entry

    entries = list(unique.values())

    # --------------------------------------------------------
    # Sendernamen zusammenfassen
    #
    # Gleicher Sender mit mehreren technischen Feeds:
    # bevorzugt wird der erste brauchbare Feed.
    # --------------------------------------------------------

    sender_unique = OrderedDict()

    for entry in entries:

        name = entry["name"]
        normalized = normalize_name(name)

        if normalized not in sender_unique:

            sender_unique[normalized] = entry

        else:

            existing = sender_unique[normalized]

            # HD bevorzugen, wenn der neue Eintrag HD
            # und der bestehende nicht HD ist.
            if (
                "hd" in normalized
                and "hd" not in normalize_name(
                    existing["name"]
                )
            ):
                sender_unique[normalized] = entry

    entries = list(sender_unique.values())

    # --------------------------------------------------------
    # Prioritäten / Kategorien
    # --------------------------------------------------------

    for entry in entries:

        entry["priority"] = priority_index(
            entry["name"]
        )

        entry["category"] = category(
            entry["name"]
        )

    # --------------------------------------------------------
    # Sortierung
    #
    # 1. Top-Priorität
    # 2. Kategorie
    # 3. Alphabetisch
    # --------------------------------------------------------

    category_order = {
        "01 Öffentlich-Rechtlich": 1,
        "02 Niedersachsen & Norddeutschland": 2,
        "03 Dritte Programme": 3,
        "04 Private": 4,
        "05 Nachrichten": 5,
        "06 Dokumentation & Wissen": 6,
        "07 Unterhaltung": 7,
        "08 Kinder": 8,
        "09 Religion": 9,
        "10 Sport": 10,
        "11 Weitere deutsche Sender": 11,
    }

    entries.sort(
        key=lambda entry: (
            entry["priority"],
            category_order.get(
                entry["category"],
                99
            ),
            normalize_name(
                entry["name"]
            ),
        )
    )

    # --------------------------------------------------------
    # M3U erzeugen
    # --------------------------------------------------------

    output = [
        "#EXTM3U",
        "",
        "# ==================================================",
        "# Deutsche TV-Liste",
        "# Automatisch erzeugt aus IPTV-org",
        "# Musik / Shopping / Erotik ausgeschlossen",
        "# ==================================================",
        "",
    ]

    current_category = None

    for entry in entries:

        group = entry["category"]

        if group != current_category:

            output.append("")
            output.append(
                f"# ===== {group} ====="
            )
            output.append("")

            current_category = group

        info = clean_info(
            entry["info"],
            entry["name"],
            group
        )

        output.append(info)
        output.append(entry["url"])

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(output)
            + "\n"
        )

    # --------------------------------------------------------
    # Statistik
    # --------------------------------------------------------

    top50 = [
        entry
        for entry in entries
        if entry["priority"] < 9999
    ]

    print()
    print("==========================================")
    print("FERTIG")
    print("==========================================")

    print(
        "Gesamt:",
        len(entries),
        "Sender"
    )

    print(
        "Top-Priorität gefunden:",
        len(top50)
    )

    print()
    print("TOP-PRIORITÄT:")

    for number, entry in enumerate(
        top50,
        start=1
    ):

        print(
            f"{number:02d}. "
            f"{entry['name']}"
        )

    print()
    print("==========================================")
    print(
        "Datei:",
        OUTPUT
    )
    print("==========================================")


if __name__ == "__main__":
    main()

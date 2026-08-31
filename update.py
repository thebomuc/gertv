import re
import urllib.request
from collections import OrderedDict

# ============================================================
# Quellen
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
# TOP-PRIORITÄT
#
# Diese Sender stehen immer oben, sofern sie aktuell
# in den Quellen vorhanden sind.
# ============================================================

TOP_PRIORITY = [
    # --------------------------------------------------------
    # 01 Öffentlich-Rechtlich
    # --------------------------------------------------------
    "Das Erste",
    "ZDF",
    "3sat",
    "ARTE",
    "Phoenix",
    "ZDFneo",
    "ZDFinfo",
    "ONE",
    "tagesschau24",
    "ARD-alpha",
    "Deutsche Welle",

    # --------------------------------------------------------
    # 02 Niedersachsen / Norddeutschland
    # --------------------------------------------------------
    "NDR Niedersachsen",
    "NDR Hamburg",
    "NDR Schleswig-Holstein",
    "NDR Mecklenburg-Vorpommern",
    "Radio Bremen TV",
    "Hamburg 1",
    "RTL Nord Niedersachsen & Bremen",
    "17:30 SAT.1 Regional Hamburg & Schleswig-Holstein",

    # --------------------------------------------------------
    # 03 Dritte Programme
    # --------------------------------------------------------
    "WDR",
    "MDR Sachsen",
    "MDR Sachsen-Anhalt",
    "MDR Thüringen",
    "rbb",
    "hr-fernsehen",
    "BR Fernsehen",
    "SR Fernsehen",
    "SWR",

    # --------------------------------------------------------
    # 04 Private
    # --------------------------------------------------------
    "RTL",
    "RTLZWEI",
    "ProSieben",
    "SAT.1",
    "VOX",
    "Kabel Eins",
    "Kabel Eins Doku",
    "NITRO",
    "VOXup",
    "sixx",
    "ProSieben MAXX",
    "SAT.1 Gold",
    "TELE 5",
    "DMAX",
    "TLC",

    # --------------------------------------------------------
    # 05 Nachrichten
    # --------------------------------------------------------
    "WELT",
    "ntv",
    "Euronews",

    # --------------------------------------------------------
    # 06 Religion
    # --------------------------------------------------------
    "Bibel TV",
    "K-TV",
    "EWTN",
    "ERF 1",
]

# ============================================================
# Kategorien
# ============================================================

CATEGORY_KEYWORDS = OrderedDict([
    ("01 Öffentlich-Rechtlich", [
        "Das Erste", "ZDF", "3sat", "ARTE", "arte",
        "Phoenix", "ZDFneo", "ZDFinfo", "ONE",
        "tagesschau", "ARD-alpha", "Deutsche Welle", "DW Deutsch"
    ]),

    ("02 Niedersachsen & Norddeutschland", [
        "NDR", "Radio Bremen", "Hamburg 1",
        "RTL Nord", "SAT.1 Regional",
        "Schleswig-Holstein", "Niedersachsen",
        "Mecklenburg-Vorpommern",
        "Hamburg"
    ]),

    ("03 Dritte Programme", [
        "WDR", "MDR", "rbb", "HR", "hr-",
        "BR Fernsehen", "BR24", "SWR", "SR Fernsehen"
    ]),

    ("04 Private", [
        "RTL", "RTLZWEI", "ProSieben", "SAT.1",
        "VOX", "Kabel Eins", "NITRO", "VOXup",
        "sixx", "ProSieben MAXX", "SAT.1 Gold",
        "TELE 5", "TLC", "COMEDY CENTRAL",
        "Nickelodeon", "SUPER RTL"
    ]),

    ("05 Nachrichten", [
        "WELT", "ntv", "N24", "Euronews",
        "Bloomberg", "Nachrichten"
    ]),

    ("06 Dokumentation & Wissen", [
        "Kabel Eins Doku", "DMAX", "Dokument",
        "Discovery", "History", "Wissen",
        "Science", "National Geographic"
    ]),

    ("07 Unterhaltung / Serien / Filme", [
        "Comedy", "Film", "Movie", "Serie",
        "Entertainment", "Warner", "AXN"
    ]),

    ("08 Kinder", [
        "KiKA", "KIKA", "SUPER RTL", "Nickelodeon"
    ]),

    ("09 Religion", [
        "Bibel TV", "K-TV", "EWTN", "ERF",
        "Kirche", "Christian", "Gospel"
    ]),

    ("10 Sport", [
        "Sport", "Sport1", "Eurosport",
        "Tennis", "Football", "Fußball"
    ]),

    ("11 Regional / Lokal", [
        "Lokal", "Regional", "TV", "Stadt",
        "Kiel", "Hannover", "Braunschweig",
        "Oldenburg", "Osnabrück", "Bremen",
        "Hamburg"
    ]),

    # Musik wird absichtlich ganz hinten einsortiert.
    # Sie wird NICHT entfernt, damit später bei Bedarf
    # weitere Sender verfügbar bleiben.
    ("12 Musik / Sonstige", [
        "Music", "Musik", "Deluxe", "Schlager"
    ]),
])

# ============================================================
# Ausschlüsse
# ============================================================

EXCLUDE_KEYWORDS = [
    "Shopping",
    "Shop",
    "Teleshopping",
    "Home Shopping",
    "QVC",
    "HSE",
    "Erotik",
    "XXX",
    "Adult",
    "Porn",
]

# Musik komplett aus der persönlichen Liste entfernen.
# Wenn du sie später doch willst: False setzen.
REMOVE_MUSIC = True

# ============================================================
# Hilfsfunktionen
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
        return response.read().decode("utf-8", errors="replace")


def parse_m3u(text):
    """
    Liest EXTINF + URL Paare aus einer M3U.
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

                match = re.search(r",(.+)$", info)

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
    Vereinheitlicht Namen für Vergleiche.
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

    name = re.sub(r"[^a-z0-9]+", " ", name)

    return " ".join(name.split())


def is_excluded(name):
    name_lower = name.lower()

    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in name_lower:
            return True

    if REMOVE_MUSIC:
        music_words = [
            "music",
            "musik",
            "deluxe music",
            "schlager deluxe",
        ]

        for keyword in music_words:
            if keyword in name_lower:
                return True

    return False


def get_category(name):
    name_lower = name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in name_lower:
                return category

    return "11 Regional / Lokal"


def find_priority(name):
    normalized = normalize_name(name)

    for number, wanted in enumerate(TOP_PRIORITY):

        wanted_normalized = normalize_name(wanted)

        if normalized == wanted_normalized:
            return number

        if wanted_normalized in normalized:
            return number

    return 9999


def clean_info(info, name, category):
    """
    Entfernt das alte group-title und setzt unser eigenes.
    """

    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info
    )

    info = re.sub(
        r'\s+tvg-group="[^"]*"',
        "",
        info
    )

    info_without_name = re.sub(
        r",.*$",
        "",
        info
    )

    return (
        f'{info_without_name} '
        f'group-title="{category}",{name}'
    )


# ============================================================
# Hauptprogramm
# ============================================================

def main():

    all_entries = []

    # --------------------------------------------------------
    # Alle Quellen laden
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
        f"Insgesamt geladen: "
        f"{len(all_entries)} Einträge"
    )

    # --------------------------------------------------------
    # Duplikate entfernen
    # --------------------------------------------------------

    unique = OrderedDict()

    for entry in all_entries:

        name = entry["name"]
        url = entry["url"]

        if not name or not url:
            continue

        if is_excluded(name):
            continue

        key = normalize_name(name)

        # Wenn derselbe Sender bereits existiert,
        # behalten wir den ersten Eintrag.
        if key not in unique:
            unique[key] = entry

    entries = list(unique.values())

    print(
        f"Nach Bereinigung: "
        f"{len(entries)} Sender"
    )

    # --------------------------------------------------------
    # Kategorien vergeben
    # --------------------------------------------------------

    for entry in entries:

        entry["category"] = get_category(
            entry["name"]
        )

        entry["priority"] = find_priority(
            entry["name"]
        )

    # --------------------------------------------------------
    # Sortierung
    #
    # 1. Top-Priorität
    # 2. Kategorie
    # 3. alphabetisch
    # --------------------------------------------------------

    category_order = {
        category: number
        for number, category
        in enumerate(CATEGORY_KEYWORDS.keys())
    }

    entries.sort(
        key=lambda entry: (
            entry["priority"],
            category_order.get(
                entry["category"],
                999
            ),
            normalize_name(entry["name"]),
        )
    )

    # --------------------------------------------------------
    # M3U schreiben
    # --------------------------------------------------------

    output = [
        "#EXTM3U",
        "",
        "# ===============================================",
        "# Deutsche TV-Liste",
        "# Automatisch aktualisiert über IPTV-org",
        "# ===============================================",
        "",
    ]

    current_category = None

    for entry in entries:

        category = entry["category"]

        if category != current_category:

            output.append("")
            output.append(
                f"# ===== {category} ====="
            )
            output.append("")

            current_category = category

        info = clean_info(
            entry["info"],
            entry["name"],
            category
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

    print()
    print("====================================")
    print("FERTIG")
    print("====================================")
    print(
        f"Sender in deutsch.m3u: "
        f"{len(entries)}"
    )

    print()
    print("Kategorien:")

    counts = {}

    for entry in entries:

        category = entry["category"]

        counts[category] = (
            counts.get(category, 0) + 1
        )

    for category, count in counts.items():

        print(
            f"  {category}: {count}"
        )

    print()
    print("Top-Priorität:")

    for entry in entries:

        if entry["priority"] < 9999:

            print(
                f"  {entry['priority'] + 1:02d}. "
                f"{entry['name']}"
            )


if __name__ == "__main__":
    main()

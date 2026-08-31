import re
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - persönliche deutsche M3U
# ============================================================
#
# Gruppen:
#
# 01 Regional
# 02 Öffentlich-Rechtlich
# 03 Dritte Programme
# 04 Private
# 05 Nachrichten
# 06 Dokumentation & Wissen
# 07 Kinder
# 08 Religion
# 09 Sport
# 10 Weitere deutsche Sender
#
# Quelle:
# IPTV-org
#
# https://iptv-org.github.io/iptv/
# ============================================================


OUTPUT = "deutsch.m3u"


# ============================================================
# QUELLEN
# ============================================================

SOURCES = [
    ("Deutschland", "https://iptv-org.github.io/iptv/countries/de.m3u"),

    # Regionen
    ("Niedersachsen", "https://iptv-org.github.io/iptv/subdivisions/de-ni.m3u"),
    ("Hamburg", "https://iptv-org.github.io/iptv/subdivisions/de-hh.m3u"),
    ("Schleswig-Holstein", "https://iptv-org.github.io/iptv/subdivisions/de-sh.m3u"),
    ("Mecklenburg-Vorpommern", "https://iptv-org.github.io/iptv/subdivisions/de-mv.m3u"),
]


# ============================================================
# REGIONALE QUELLEN
# ============================================================

REGIONAL_SOURCES = {
    "Niedersachsen",
    "Hamburg",
    "Schleswig-Holstein",
    "Mecklenburg-Vorpommern",
}


# ============================================================
# FESTE KATEGORIEN
# ============================================================

REGIONAL_IDS = {
    "NDRNiedersachsen.de",
    "RTLNordNiedersachsenBremen.de",
    "RadioBremenTV.de",
    "Hamburg1.de",
    "1730SAT1REGIONALHamburgSchleswigHolstein.de",
}


PUBLIC_IDS = {
    "DasErste.de",
    "ZDF.de",
    "3sat.de",
    "Arte.de",
    "Phoenix.de",
    "ZDFneo.de",
    "ZDFinfo.de",
    "One.de",
    "Tagesschau24.de",
    "ARDAlpha.de",
    "DeutscheWelle.de",
    "KiKA.de",
}


THIRD_PROGRAM_IDS = {
    "WDRKoeln.de",
    "BRFernsehen.de",
    "HRFernsehen.de",
    "MDRSachsen.de",
    "MDRSachsenAnhalt.de",
    "MDRThueringen.de",
    "RBB.de",
    "SWR.de",
    "SRFernsehen.de",
}


PRIVATE_IDS = {
    "RTL.de",
    "RTLZWEI.de",
    "ProSieben.de",
    "SAT1.de",
    "VOX.de",
    "KabelEins.de",
    "KabelEinsDoku.de",
    "NITRO.de",
    "VOXup.de",
    "sixx.de",
    "ProSiebenMAXX.de",
    "SAT1Gold.de",
    "TELE5.de",
    "DMAX.de",
}


NEWS_IDS = {
    "Welt.de",
    "N-TV.de",
    "EuronewsDeutsch.de",
    "N24Doku.de",
}


DOCUMENTARY_IDS = {
    "KabelEinsDoku.de",
    "DMAX.de",
    "N24Doku.de",
}


RELIGION_IDS = {
    "BibelTV.de",
    "K-TV.de",
    "EWTN.de",
    "ERF1.de",
}


# ============================================================
# AUSGESCHLOSSENE TVG-IDS
# ============================================================

EXCLUDE_IDS = {
    "OneAdria.hr",
    "ZeeOne.de",
}


# ============================================================
# AUSGESCHLOSSENE NAMEN
# ============================================================

EXCLUDE_NAME_WORDS = [
    "shopping",
    "teleshopping",
    "home shopping",
    "qvc",
    "hse",
    "1-2-3 tv",
    "123 tv",

    "erotik",
    "xxx",
    "adult",
    "porn",

    "music",
    "musik",
    "deluxe music",
    "schlager",
]


# ============================================================
# DOWNLOAD
# ============================================================

def download(url):

    print("Lade:", url)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        return response.read().decode(
            "utf-8",
            errors="replace"
        )


# ============================================================
# ATTRIBUTE AUS EXTINF LESEN
# ============================================================

def get_attribute(info, attribute):

    pattern = rf'{re.escape(attribute)}="([^"]*)"'

    match = re.search(
        pattern,
        info,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# M3U PARSER
# ============================================================

def parse_m3u(text, source_name):

    lines = text.splitlines()

    entries = []

    for i, line in enumerate(lines):

        line = line.strip()

        if not line.startswith("#EXTINF:"):
            continue

        if i + 1 >= len(lines):
            continue

        url = lines[i + 1].strip()

        if not url or url.startswith("#"):
            continue

        # Sendername nach dem letzten Komma
        match = re.search(
            r",(.+)$",
            line
        )

        name = (
            match.group(1).strip()
            if match
            else ""
        )

        entry = {
            "info": line,
            "name": name,
            "tvg_id": get_attribute(line, "tvg-id"),
            "tvg_name": get_attribute(line, "tvg-name"),
            "language": get_attribute(line, "tvg-language"),
            "country": get_attribute(line, "tvg-country"),
            "logo": get_attribute(line, "tvg-logo"),
            "source": source_name,
            "url": url,
        }

        entries.append(entry)

    return entries


# ============================================================
# NORMALISIERUNG
# ============================================================

def normalize(value):

    value = value.lower()

    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(value.split())


# ============================================================
# AUSSCHLÜSSE
# ============================================================

def excluded(entry):

    tvg_id = entry["tvg_id"]

    if tvg_id in EXCLUDE_IDS:
        return True

    combined = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    for word in EXCLUDE_NAME_WORDS:

        if normalize(word) in combined:
            return True

    return False


# ============================================================
# KATEGORIE
# ============================================================

def get_category(entry):

    tvg_id = entry["tvg_id"]
    name = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    source = entry["source"]

    # --------------------------------------------------------
    # 01 REGIONAL
    # --------------------------------------------------------

    if tvg_id in REGIONAL_IDS:
        return "01 Regional"

    if source in REGIONAL_SOURCES:

        regional_words = [
            "regional",
            "ndr niedersachsen",
            "ndr hamburg",
            "hamburg",
            "schleswig holstein",
            "mecklenburg",
            "vorpommern",
            "bremen",
            "nord",
        ]

        if any(
            word in name
            for word in regional_words
        ):
            return "01 Regional"


    # --------------------------------------------------------
    # 08 RELIGION
    # --------------------------------------------------------

    if tvg_id in RELIGION_IDS:
        return "08 Religion"


    # --------------------------------------------------------
    # 05 NACHRICHTEN
    # --------------------------------------------------------

    if tvg_id in NEWS_IDS:
        return "05 Nachrichten"

    news_words = [
        "nachrichten",
        "news",
        "welt",
        "n-tv",
        "ntv",
        "euronews",
    ]

    if any(
        word in name
        for word in news_words
    ):
        return "05 Nachrichten"


    # --------------------------------------------------------
    # 06 DOKUMENTATION
    # --------------------------------------------------------

    if tvg_id in DOCUMENTARY_IDS:
        return "06 Dokumentation & Wissen"

    documentary_words = [
        "doku",
        "dokumentation",
        "documentary",
        "wissen",
        "history",
        "science",
    ]

    if any(
        word in name
        for word in documentary_words
    ):
        return "06 Dokumentation & Wissen"


    # --------------------------------------------------------
    # 07 KINDER
    # --------------------------------------------------------

    if tvg_id == "KiKA.de":
        return "07 Kinder"

    children_words = [
        "kika",
        "kinder",
        "kids",
        "junior",
    ]

    if any(
        word in name
        for word in children_words
    ):
        return "07 Kinder"


    # --------------------------------------------------------
    # 09 SPORT
    # --------------------------------------------------------

    if "sport" in name:
        return "09 Sport"


    # --------------------------------------------------------
    # 01 ÖFFENTLICH-RECHTLICH
    # --------------------------------------------------------

    if tvg_id in PUBLIC_IDS:
        return "02 Öffentlich-Rechtlich"


    # --------------------------------------------------------
    # 03 DRITTE PROGRAMME
    # --------------------------------------------------------

    if tvg_id in THIRD_PROGRAM_IDS:
        return "03 Dritte Programme"


    # --------------------------------------------------------
    # 04 PRIVATE
    # --------------------------------------------------------

    if tvg_id in PRIVATE_IDS:
        return "04 Private"


    # --------------------------------------------------------
    # 10 WEITERE
    # --------------------------------------------------------

    return "10 Weitere deutsche Sender"


# ============================================================
# HD-PRIORITÄT
# ============================================================

def is_hd(entry):

    name = normalize(
        entry["name"]
    )

    tvg_name = normalize(
        entry["tvg_name"]
    )

    return (
        "hd" in name
        or "hd" in tvg_name
    )


# ============================================================
# DEDUPLIZIERUNG
# ============================================================

def deduplicate(entries):

    by_id = OrderedDict()

    for entry in entries:

        tvg_id = entry["tvg_id"]

        # Ohne ID können wir nicht sauber deduplizieren.
        if not tvg_id:
            continue

        if tvg_id not in by_id:

            by_id[tvg_id] = entry
            continue

        existing = by_id[tvg_id]

        # HD-Version bevorzugen
        if is_hd(entry) and not is_hd(existing):
            by_id[tvg_id] = entry

    return list(
        by_id.values()
    )


# ============================================================
# EXTINF BEREINIGEN
# ============================================================

def clean_info(entry, category):

    info = entry["info"]

    # Altes group-title entfernen
    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

    # Alten Namen nach Komma entfernen
    info = re.sub(
        r",.*$",
        "",
        info
    )

    return (
        f'{info} '
        f'group-title="{category}",'
        f'{entry["name"]}'
    )


# ============================================================
# SORTIERUNG
# ============================================================

CATEGORY_ORDER = {
    "01 Regional": 1,
    "02 Öffentlich-Rechtlich": 2,
    "03 Dritte Programme": 3,
    "04 Private": 4,
    "05 Nachrichten": 5,
    "06 Dokumentation & Wissen": 6,
    "07 Kinder": 7,
    "08 Religion": 8,
    "09 Sport": 9,
    "10 Weitere deutsche Sender": 10,
}


def sort_entries(entries):

    entries.sort(
        key=lambda entry: (
            CATEGORY_ORDER.get(
                entry["category"],
                99
            ),
            normalize(
                entry["name"]
            ),
        )
    )

    return entries


# ============================================================
# M3U SCHREIBEN
# ============================================================

def write_m3u(entries):

    output = [
        "#EXTM3U",
        "",
        "# ==================================================",
        "# GER TV - Deutsche TV-Liste",
        "# Automatisch aktualisiert",
        "# Quelle: IPTV-org",
        "#",
        "# Regional",
        "# Öffentlich-Rechtlich",
        "# Dritte Programme",
        "# Private",
        "# Nachrichten",
        "# Dokumentation & Wissen",
        "# Kinder",
        "# Religion",
        "# Sport",
        "# Weitere deutsche Sender",
        "# ==================================================",
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

        output.append(
            clean_info(
                entry,
                category
            )
        )

        output.append(
            entry["url"]
        )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(output)
            + "\n"
        )


# ============================================================
# STATISTIK
# ============================================================

def print_statistics(entries):

    print()
    print("==========================================")
    print("KATEGORIEN")
    print("==========================================")

    counts = {}

    for entry in entries:

        category = entry["category"]

        counts[category] = (
            counts.get(category, 0)
            + 1
        )

    for category in CATEGORY_ORDER:

        print(
            f"{category}: "
            f"{counts.get(category, 0)}"
        )

    print()
    print("Gesamt:", len(entries))


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    all_entries = []

    print()
    print("==========================================")
    print("GER TV")
    print("==========================================")
    print()

    # --------------------------------------------------------
    # Quellen laden
    # --------------------------------------------------------

    for source_name, url in SOURCES:

        try:

            text = download(url)

            entries = parse_m3u(
                text,
                source_name
            )

            print(
                f"{source_name}: "
                f"{len(entries)} Einträge"
            )

            all_entries.extend(
                entries
            )

        except Exception as error:

            print(
                f"FEHLER bei "
                f"{source_name}: "
                f"{error}"
            )

    print()
    print(
        "Insgesamt geladen:",
        len(all_entries)
    )


    # --------------------------------------------------------
    # Ausschlüsse
    # --------------------------------------------------------

    filtered = [
        entry
        for entry in all_entries
        if not excluded(entry)
    ]

    print(
        "Nach Ausschlüssen:",
        len(filtered)
    )


    # --------------------------------------------------------
    # Nur deutsche Sender
    # --------------------------------------------------------

    german = []

    for entry in filtered:

        country = normalize(
            entry["country"]
        )

        language = normalize(
            entry["language"]
        )

        tvg_id = entry["tvg_id"]

        is_german = (
            "de" in country.split()
            or "germany" in country
            or "deutsch" in language
            or tvg_id.endswith(".de")
        )

        if is_german:

            german.append(entry)


    # --------------------------------------------------------
    # Falls tvg-country bei der Quelle fehlt
    # --------------------------------------------------------

    if len(german) < 20:

        print(
            "Warnung: "
            "zu wenige deutsche Sender "
            "über Metadaten erkannt."
        )

        print(
            "Verwende gefilterte Liste."
        )

        german = filtered


    print(
        "Deutsche Sender:",
        len(german)
    )


    # --------------------------------------------------------
    # Deduplizieren
    # --------------------------------------------------------

    entries = deduplicate(
        german
    )

    print(
        "Nach Deduplizierung:",
        len(entries)
    )


    # --------------------------------------------------------
    # Kategorien
    # --------------------------------------------------------

    for entry in entries:

        entry["category"] = get_category(
            entry
        )


    # --------------------------------------------------------
    # Sortieren
    # --------------------------------------------------------

    entries = sort_entries(
        entries
    )


    # --------------------------------------------------------
    # M3U schreiben
    # --------------------------------------------------------

    write_m3u(
        entries
    )


    # --------------------------------------------------------
    # Statistik
    # --------------------------------------------------------

    print_statistics(
        entries
    )


    # --------------------------------------------------------
    # Fertig
    # --------------------------------------------------------

    print()
    print("==========================================")
    print("FERTIG")
    print("==========================================")
    print()
    print(
        "Datei:",
        OUTPUT
    )
    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()

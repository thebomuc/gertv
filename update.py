import re
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - DEUTSCHE M3U
# ============================================================
#
# FESTE REIHENFOLGE VORNE:
#
# 01  Das Erste
# 02  ZDF
# 03  NDR Niedersachsen
# 04  3sat
# 05  arte
# 06  Phoenix
# 07  ZDFneo
# 08  ZDFinfo
# 09  One
# 10  Tagesschau24
# 11  ARD alpha
# 12  KiKA
#
# Danach:
#
# Regional
# Dritte Programme
# Private
# Nachrichten
# Dokumentation
# Kinder
# Religion
# Sport
# Weitere
#
# ============================================================


OUTPUT = "deutsch.m3u"


# ============================================================
# QUELLEN
# ============================================================

SOURCES = [

    (
        "Deutschland",
        "https://iptv-org.github.io/iptv/countries/de.m3u"
    ),

    (
        "Niedersachsen",
        "https://iptv-org.github.io/iptv/subdivisions/de-ni.m3u"
    ),

    (
        "Hamburg",
        "https://iptv-org.github.io/iptv/subdivisions/de-hh.m3u"
    ),

    (
        "Schleswig-Holstein",
        "https://iptv-org.github.io/iptv/subdivisions/de-sh.m3u"
    ),

    (
        "Mecklenburg-Vorpommern",
        "https://iptv-org.github.io/iptv/subdivisions/de-mv.m3u"
    ),
]


# ============================================================
# FESTE STARTREIHENFOLGE
#
# Genau diese Sender kommen zuerst.
# Die Reihenfolge hier ist die Reihenfolge
# in der M3U.
# ============================================================

FIXED_ORDER = [

    "DasErste.de",
    "ZDF.de",
    "NDRNiedersachsen.de",
    "3sat.de",
    "Arte.de",

    "Phoenix.de",
    "ZDFneo.de",
    "ZDFinfo.de",
    "One.de",
    "Tagesschau24.de",
    "ARDAlpha.de",
    "KiKA.de",

]


# ============================================================
# REGIONALE SENDER
# ============================================================

REGIONAL_IDS = {

    "NDRNiedersachsen.de",

    "RTLNordNiedersachsenBremen.de",

    "RadioBremenTV.de",

    "Hamburg1.de",

    "1730SAT1REGIONALHamburgSchleswigHolstein.de",

}


# ============================================================
# DRITTE PROGRAMME
# ============================================================

THIRD_IDS = {

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


# ============================================================
# PRIVATE
# ============================================================

PRIVATE_IDS = {

    "RTL.de",

    "RTLZWEI.de",

    "ProSieben.de",

    "SAT1.de",

    "VOX.de",

    "KabelEins.de",

    "NITRO.de",

    "VOXup.de",

    "sixx.de",

    "ProSiebenMAXX.de",

    "SAT1Gold.de",

    "TELE5.de",

}


# ============================================================
# NACHRICHTEN
# ============================================================

NEWS_IDS = {

    "Welt.de",

    "N-TV.de",

    "EuronewsDeutsch.de",

}


# ============================================================
# DOKUMENTATION
# ============================================================

DOCU_IDS = {

    "KabelEinsDoku.de",

    "DMAX.de",

    "N24Doku.de",

}


# ============================================================
# RELIGION
# ============================================================

RELIGION_IDS = {

    "BibelTV.de",

    "K-TV.de",

    "EWTN.de",

    "ERF1.de",

}


# ============================================================
# AUSSCHLÜSSE
# ============================================================

EXCLUDE_IDS = {

    "OneAdria.hr",

    "ZeeOne.de",

}


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
# ATTRIBUTE AUS EXTINF
# ============================================================

def get_attribute(info, attribute):

    match = re.search(

        rf'{re.escape(attribute)}="([^"]*)"', 

        info,

        re.IGNORECASE

    )

    if match:

        return match.group(1).strip()

    return ""


# ============================================================
# M3U PARSER
# ============================================================

def parse_m3u(text, source):

    lines = text.splitlines()

    entries = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith("#EXTINF:"):

            i += 1

            continue

        if i + 1 >= len(lines):

            break

        url = lines[i + 1].strip()

        if not url or url.startswith("#"):

            i += 2
            continue

        match = re.search(
            r",(.+)$",
            line
        )

        name = (

            match.group(1).strip()

            if match

            else ""

        )

        entries.append({

            "info": line,

            "name": name,

            "tvg_id": get_attribute(
                line,
                "tvg-id"
            ),

            "tvg_name": get_attribute(
                line,
                "tvg-name"
            ),

            "language": get_attribute(
                line,
                "tvg-language"
            ),

            "country": get_attribute(
                line,
                "tvg-country"
            ),

            "source": source,

            "url": url,

        })

        i += 2

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

        value = value.replace(
            old,
            new
        )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(
        value.split()
    )


# ============================================================
# AUSSCHLUSS
# ============================================================

def excluded(entry):

    if entry["tvg_id"] in EXCLUDE_IDS:

        return True

    text = normalize(

        entry["name"]
        + " "
        + entry["tvg_name"]

    )

    for word in EXCLUDE_NAME_WORDS:

        if normalize(word) in text:

            return True

    return False


# ============================================================
# HD ERKENNUNG
# ============================================================

def is_hd(entry):

    text = normalize(

        entry["name"]
        + " "
        + entry["tvg_name"]

    )

    return "hd" in text.split()


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


    # --------------------------------------------------------
    # FESTE STARTSENDER
    # --------------------------------------------------------

    if tvg_id in FIXED_ORDER:

        return "00 Hauptsender"


    # --------------------------------------------------------
    # REGIONAL
    # --------------------------------------------------------

    if tvg_id in REGIONAL_IDS:

        return "01 Regional"


    # --------------------------------------------------------
    # DRITTE
    # --------------------------------------------------------

    if tvg_id in THIRD_IDS:

        return "02 Dritte Programme"


    # --------------------------------------------------------
    # PRIVATE
    # --------------------------------------------------------

    if tvg_id in PRIVATE_IDS:

        return "03 Private"


    # --------------------------------------------------------
    # NACHRICHTEN
    # --------------------------------------------------------

    if tvg_id in NEWS_IDS:

        return "04 Nachrichten"


    # --------------------------------------------------------
    # DOKU
    # --------------------------------------------------------

    if tvg_id in DOCU_IDS:

        return "05 Dokumentation & Wissen"


    # --------------------------------------------------------
    # KINDER
    # --------------------------------------------------------

    if tvg_id == "KiKA.de":

        return "06 Kinder"


    if any(
        word in name
        for word in [
            "kinder",
            "kids",
            "junior"
        ]
    ):

        return "06 Kinder"


    # --------------------------------------------------------
    # RELIGION
    # --------------------------------------------------------

    if tvg_id in RELIGION_IDS:

        return "07 Religion"


    # --------------------------------------------------------
    # SPORT
    # --------------------------------------------------------

    if "sport" in name:

        return "08 Sport"


    # --------------------------------------------------------
    # WEITERE
    # --------------------------------------------------------

    return "09 Weitere deutsche Sender"


# ============================================================
# DEDUPLIZIERUNG
# ============================================================

def deduplicate(entries):

    result = OrderedDict()

    for entry in entries:

        tvg_id = entry["tvg_id"]

        if not tvg_id:

            continue


        if tvg_id not in result:

            result[tvg_id] = entry

            continue


        existing = result[tvg_id]


        # HD bevorzugen

        if (
            is_hd(entry)
            and not is_hd(existing)
        ):

            result[tvg_id] = entry


    return list(
        result.values()
    )


# ============================================================
# INFO BEREINIGEN
# ============================================================

def clean_info(entry, category):

    info = entry["info"]


    # group-title entfernen

    info = re.sub(

        r'\s+group-title="[^"]*"',

        "",

        info,

        flags=re.IGNORECASE

    )


    # Sendername entfernen

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

    "00 Hauptsender": 0,

    "01 Regional": 1,

    "02 Dritte Programme": 2,

    "03 Private": 3,

    "04 Nachrichten": 4,

    "05 Dokumentation & Wissen": 5,

    "06 Kinder": 6,

    "07 Religion": 7,

    "08 Sport": 8,

    "09 Weitere deutsche Sender": 9,

}


def sort_entries(entries):

    fixed = []

    rest = []


    # --------------------------------------------------------
    # Zuerst feste Sender
    # --------------------------------------------------------

    by_id = {

        entry["tvg_id"]: entry

        for entry in entries

    }


    for tvg_id in FIXED_ORDER:

        if tvg_id in by_id:

            fixed.append(
                by_id[tvg_id]
            )


    # --------------------------------------------------------
    # Alles andere
    # --------------------------------------------------------

    fixed_ids = set(
        FIXED_ORDER
    )


    for entry in entries:

        if entry["tvg_id"] not in fixed_ids:

            rest.append(entry)


    # --------------------------------------------------------
    # Rest nach Kategorie
    # --------------------------------------------------------

    rest.sort(

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


    return fixed + rest


# ============================================================
# M3U SCHREIBEN
# ============================================================

def write_m3u(entries):

    output = [

        "#EXTM3U",

        "",

        "# ==================================================",

        "# GER TV",

        "# Deutsche TV-Liste",

        "#",

        "# Feste Hauptsender zuerst",

        "# Regional",

        "# Dritte Programme",

        "# Private",

        "# Nachrichten",

        "# Dokumentation",

        "# Kinder",

        "# Religion",

        "# Sport",

        "# Weitere",

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

def statistics(entries):

    print()

    print(
        "=========================================="
    )

    print(
        "ERGEBNIS"
    )

    print(
        "=========================================="
    )


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

    print(
        "Gesamt:",
        len(entries)
    )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    all_entries = []


    print()

    print(
        "=========================================="
    )

    print(
        "GER TV - M3U GENERATOR"
    )

    print(
        "=========================================="
    )

    print()


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    for source, url in SOURCES:

        try:

            text = download(url)

            entries = parse_m3u(
                text,
                source
            )

            print(

                f"{source}: "
                f"{len(entries)} Sender"

            )

            all_entries.extend(
                entries
            )


        except Exception as error:

            print()

            print(
                f"FEHLER bei {source}:"
            )

            print(error)


    print()

    print(
        "Geladene Einträge:",
        len(all_entries)
    )


    # --------------------------------------------------------
    # AUSSCHLÜSSE
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
    # DEDUP
    # --------------------------------------------------------

    entries = deduplicate(
        filtered
    )


    print(

        "Nach Deduplizierung:",

        len(entries)

    )


    # --------------------------------------------------------
    # KATEGORIE
    # --------------------------------------------------------

    for entry in entries:

        entry["category"] = get_category(
            entry
        )


    # --------------------------------------------------------
    # SORTIEREN
    # --------------------------------------------------------

    entries = sort_entries(
        entries
    )


    # --------------------------------------------------------
    # SCHREIBEN
    # --------------------------------------------------------

    write_m3u(
        entries
    )


    # --------------------------------------------------------
    # STATISTIK
    # --------------------------------------------------------

    statistics(
        entries
    )


    # --------------------------------------------------------
    # DIE ERSTEN SENDER AUSGEBEN
    # --------------------------------------------------------

    print()

    print(
        "=========================================="
    )

    print(
        "ERSTE SENDER"
    )

    print(
        "=========================================="
    )


    for number, entry in enumerate(
        entries[:30],
        start=1
    ):

        print(

            f"{number:02d}. "
            f"{entry['name']} "
            f"[{entry['tvg_id']}]"

        )


    print()

    print(
        "=========================================="
    )

    print(
        "FERTIG"
    )

    print(
        "=========================================="
    )

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

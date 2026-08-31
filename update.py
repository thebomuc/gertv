import re
import os
import shutil
import tempfile
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - ROBUSTE TÄGLICHE M3U
# ============================================================
#
# Ziel:
#
#   01 Das Erste
#   02 ZDF
#   03 NDR Niedersachsen
#   04 3sat
#   05 arte
#   06 Phoenix
#   07 ZDFneo
#   08 ZDFinfo
#   09 ONE
#   10 Tagesschau24
#   11 ARD alpha
#   12 KiKA
#
# Danach:
#
#   Regional
#   Dritte Programme
#   Private
#   Nachrichten
#   Dokumentation
#   Kinder
#   Religion
#   Sport
#   Weitere
#
# Eigenschaften:
#
#   - täglicher Lauf geeignet
#   - aktuelle IPTV-org Playlists
#   - tvg-id bevorzugt
#   - Namens-Fallback
#   - HD bevorzugt
#   - doppelte Sender entfernt
#   - unerwünschte Sender entfernt
#   - keine leere M3U bei Fehler
#   - alte funktionierende M3U bleibt erhalten
#
# ============================================================


OUTPUT = "deutsch.m3u"

# Temporäre Datei beim Schreiben
TEMP_OUTPUT = OUTPUT + ".tmp"

# Backup der letzten funktionierenden Version
BACKUP_OUTPUT = OUTPUT + ".bak"


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
# FESTE HAUPTREIHENFOLGE
#
# Jede Position enthält:
#
#   Anzeigename
#   mögliche tvg-ids
#   mögliche Namensvarianten
#
# Dadurch funktioniert die Liste auch dann weiter,
# wenn IPTV-org einen Namen bzw. eine ID ändert.
# ============================================================

MAIN_CHANNELS = [

    (
        "Das Erste",
        [
            "DasErste.de",
        ],
        [
            "das erste",
            "ard",
        ],
    ),

    (
        "ZDF",
        [
            "ZDF.de",
        ],
        [
            "zdf",
        ],
    ),

    (
        "NDR Niedersachsen",
        [
            "NDRNiedersachsen.de",
        ],
        [
            "ndr niedersachsen",
            "ndr fs niedersachsen",
        ],
    ),

    (
        "3sat",
        [
            "3sat.de",
        ],
        [
            "3sat",
        ],
    ),

    (
        "arte",
        [
            "Arte.de",
        ],
        [
            "arte",
        ],
    ),

    (
        "Phoenix",
        [
            "Phoenix.de",
        ],
        [
            "phoenix",
        ],
    ),

    (
        "ZDFneo",
        [
            "ZDFneo.de",
        ],
        [
            "zdfneo",
        ],
    ),

    (
        "ZDFinfo",
        [
            "ZDFinfo.de",
        ],
        [
            "zdfinfo",
        ],
    ),

    (
        "ONE",
        [
            "One.de",
        ],
        [
            "one",
        ],
    ),

    (
        "Tagesschau24",
        [
            "Tagesschau24.de",
        ],
        [
            "tagesschau24",
        ],
    ),

    (
        "ARD alpha",
        [
            "ARDAlpha.de",
        ],
        [
            "ard alpha",
            "alpha",
        ],
    ),

    (
        "KiKA",
        [
            "KiKA.de",
        ],
        [
            "kika",
        ],
    ),

]


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


NEWS_IDS = {
    "Welt.de",
    "N-TV.de",
    "EuronewsDeutsch.de",
    "N24Doku.de",
}


DOCU_IDS = {
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
# KATEGORIENREIHENFOLGE
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


# ============================================================
# DOWNLOAD
# ============================================================

def download(url):

    request = urllib.request.Request(

        url,

        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/120 Safari/537.36"
            )
        }

    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        data = response.read()

    if not data:

        raise RuntimeError(
            "Leere Antwort"
        )

    return data.decode(
        "utf-8",
        errors="replace"
    )


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
# EXTINF ATTRIBUTE
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


        entry = {

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

        }


        entries.append(
            entry
        )


        i += 2


    return entries


# ============================================================
# AUSSCHLUSS
# ============================================================

def excluded(entry):

    tvg_id = entry["tvg_id"]


    if tvg_id in EXCLUDE_IDS:

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
# HD
# ============================================================

def is_hd(entry):

    text = normalize(

        entry["name"]
        + " "
        + entry["tvg_name"]

    )

    return "hd" in text.split()


# ============================================================
# DEUTSCHER SENDER?
# ============================================================

def is_german(entry):

    country = normalize(
        entry["country"]
    )

    language = normalize(
        entry["language"]
    )

    tvg_id = entry["tvg_id"].lower()


    if "germany" in country:
        return True


    if "deutsch" in language:
        return True


    if tvg_id.endswith(".de"):
        return True


    if country == "de":
        return True


    return False


# ============================================================
# HAUPTSENDER ERKENNEN
# ============================================================

def matches_main_channel(entry, channel):

    display_name, ids, names = channel

    tvg_id = entry["tvg_id"]

    normalized_name = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )


    # --------------------------------------------------------
    # 1. Exakte ID
    # --------------------------------------------------------

    if tvg_id in ids:

        return True


    # --------------------------------------------------------
    # 2. Name
    # --------------------------------------------------------

    for name in names:

        normalized_target = normalize(
            name
        )


        if normalized_target in normalized_name:

            return True


    return False


# ============================================================
# HAUPTSENDER FINDEN
# ============================================================

def find_main_channels(entries):

    result = []

    used_ids = set()


    for channel in MAIN_CHANNELS:

        found = None


        for entry in entries:

            if entry["tvg_id"] in used_ids:

                continue


            if matches_main_channel(
                entry,
                channel
            ):

                if found is None:

                    found = entry

                else:

                    # HD-Version bevorzugen

                    if (
                        is_hd(entry)
                        and not is_hd(found)
                    ):

                        found = entry


        if found:

            found["category"] = (
                "00 Hauptsender"
            )

            result.append(
                found
            )

            used_ids.add(
                found["tvg_id"]
            )


    return result, used_ids


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


    # Hauptsender werden separat behandelt
    for channel in MAIN_CHANNELS:

        if matches_main_channel(
            entry,
            channel
        ):

            return "00 Hauptsender"


    # --------------------------------------------------------
    # Regional
    # --------------------------------------------------------

    if tvg_id in REGIONAL_IDS:

        return "01 Regional"


    regional_words = [

        "regional",
        "ndr niedersachsen",
        "hamburg 1",
        "radio bremen",
        "rtl nord",
        "sat 1 regional",
        "schleswig holstein",
        "mecklenburg vorpommern",

    ]


    if any(
        word in name
        for word in regional_words
    ):

        return "01 Regional"


    # --------------------------------------------------------
    # Dritte
    # --------------------------------------------------------

    if tvg_id in THIRD_IDS:

        return "02 Dritte Programme"


    # --------------------------------------------------------
    # Private
    # --------------------------------------------------------

    if tvg_id in PRIVATE_IDS:

        return "03 Private"


    # --------------------------------------------------------
    # Nachrichten
    # --------------------------------------------------------

    if tvg_id in NEWS_IDS:

        return "04 Nachrichten"


    if any(
        word in name
        for word in [
            "nachrichten",
            "news",
            "n-tv",
            "ntv",
            "euronews",
        ]
    ):

        return "04 Nachrichten"


    # --------------------------------------------------------
    # Dokumentation
    # --------------------------------------------------------

    if tvg_id in DOCU_IDS:

        return "05 Dokumentation & Wissen"


    if any(
        word in name
        for word in [
            "doku",
            "dokumentation",
            "documentary",
            "wissen",
            "history",
            "science",
        ]
    ):

        return "05 Dokumentation & Wissen"


    # --------------------------------------------------------
    # Kinder
    # --------------------------------------------------------

    if any(
        word in name
        for word in [
            "kika",
            "kinder",
            "kids",
            "junior",
        ]
    ):

        return "06 Kinder"


    # --------------------------------------------------------
    # Religion
    # --------------------------------------------------------

    if tvg_id in RELIGION_IDS:

        return "07 Religion"


    if any(
        word in name
        for word in [
            "bibel",
            "k-tv",
            "ewtn",
            "erf",
        ]
    ):

        return "07 Religion"


    # --------------------------------------------------------
    # Sport
    # --------------------------------------------------------

    if "sport" in name:

        return "08 Sport"


    # --------------------------------------------------------
    # Rest
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


        # HD gewinnt

        if (
            is_hd(entry)
            and not is_hd(existing)
        ):

            result[tvg_id] = entry


    return list(
        result.values()
    )


# ============================================================
# SORTIEREN
# ============================================================

def sort_entries(entries):

    fixed, used_ids = find_main_channels(
        entries
    )


    rest = [

        entry

        for entry in entries

        if entry["tvg_id"] not in used_ids

    ]


    # Kategorien bestimmen

    for entry in rest:

        entry["category"] = get_category(
            entry
        )


    # Rest sortieren

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


    # GANZ WICHTIG:
    #
    # fixed kommt IMMER zuerst.
    #
    return fixed + rest


# ============================================================
# EXTINF AUFRÄUMEN
# ============================================================

def clean_info(entry):

    info = entry["info"]


    # group-title entfernen

    info = re.sub(

        r'\s+group-title="[^"]*"',

        "",

        info,

        flags=re.IGNORECASE

    )


    # Sendername hinter Komma entfernen

    info = re.sub(
        r",.*$",
        "",
        info
    )


    return (

        f'{info} '
        f'group-title="{entry["category"]}",'
        f'{entry["name"]}'

    )


# ============================================================
# M3U ERZEUGEN
# ============================================================

def build_m3u(entries):

    output = [

        "#EXTM3U",

        "",

        "# ==================================================",

        "# GER TV - Deutsche TV-Liste",

        "# Automatisch aktualisiert",

        "# Quelle: IPTV-org",

        "#",

        "# Hauptsender zuerst",

        "# Regional",

        "# Dritte Programme",

        "# Private",

        "# Nachrichten",

        "# Dokumentation & Wissen",

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
            clean_info(entry)
        )

        output.append(
            entry["url"]
        )


    return "\n".join(
        output
    ) + "\n"


# ============================================================
# SICHER SCHREIBEN
# ============================================================

def safe_write(content):

    # --------------------------------------------------------
    # Temporär schreiben
    # --------------------------------------------------------

    with open(
        TEMP_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            content
        )


    # --------------------------------------------------------
    # Sicherheitsprüfung
    # --------------------------------------------------------

    with open(
        TEMP_OUTPUT,
        "r",
        encoding="utf-8"
    ) as file:

        check = file.read()


    extinf_count = check.count(
        "#EXTINF:"
    )


    url_count = len([
        line
        for line in check.splitlines()
        if (
            line.startswith("http://")
            or line.startswith("https://")
        )
    ])


    if extinf_count < 10:

        os.remove(
            TEMP_OUTPUT
        )

        raise RuntimeError(

            "Sicherheitsprüfung fehlgeschlagen: "
            f"nur {extinf_count} Sender gefunden."

        )


    if url_count < 10:

        os.remove(
            TEMP_OUTPUT
        )

        raise RuntimeError(

            "Sicherheitsprüfung fehlgeschlagen: "
            f"nur {url_count} URLs gefunden."

        )


    # --------------------------------------------------------
    # Bestehende Datei sichern
    # --------------------------------------------------------

    if os.path.exists(OUTPUT):

        shutil.copy2(
            OUTPUT,
            BACKUP_OUTPUT
        )


    # --------------------------------------------------------
    # Neue Datei atomar übernehmen
    # --------------------------------------------------------

    os.replace(
        TEMP_OUTPUT,
        OUTPUT
    )


# ============================================================
# STATISTIK
# ============================================================

def print_statistics(entries):

    counts = {}


    for entry in entries:

        category = entry["category"]

        counts[category] = (

            counts.get(
                category,
                0
            )
            + 1

        )


    print()
    print("==========================================")
    print("ERGEBNIS")
    print("==========================================")


    print(
        "Gesamt:",
        len(entries)
    )


    print()


    for category in CATEGORY_ORDER:

        print(

            f"{category}: "
            f"{counts.get(category, 0)}"

        )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    print()
    print("==========================================")
    print("GER TV - TÄGLICHER UPDATE")
    print("==========================================")
    print()


    all_entries = []


    # ========================================================
    # QUELLEN
    # ========================================================

    successful_sources = 0


    for source, url in SOURCES:

        try:

            print(
                f"Lade {source} ..."
            )


            text = download(
                url
            )


            entries = parse_m3u(
                text,
                source
            )


            if not entries:

                raise RuntimeError(
                    "Keine M3U-Einträge gefunden"
                )


            print(

                f"  OK: "
                f"{len(entries)} Sender"

            )


            all_entries.extend(
                entries
            )


            successful_sources += 1


        except Exception as error:

            print(

                f"  FEHLER: "
                f"{error}"

            )


    # ========================================================
    # QUELLENPRÜFUNG
    # ========================================================

    if successful_sources == 0:

        raise RuntimeError(

            "Keine einzige Quelle konnte "
            "geladen werden. "
            "Bestehende M3U bleibt erhalten."

        )


    if len(all_entries) < 20:

        raise RuntimeError(

            "Zu wenige Sender geladen: "
            f"{len(all_entries)}. "
            "Bestehende M3U bleibt erhalten."

        )


    print()
    print(
        "Geladen:",
        len(all_entries)
    )


    # ========================================================
    # AUSSCHLÜSSE
    # ========================================================

    filtered = [

        entry

        for entry in all_entries

        if not excluded(entry)

    ]


    print(

        "Nach Ausschlüssen:",
        len(filtered)

    )


    # ========================================================
    # DEUTSCHLAND FILTERN
    #
    # Wichtig:
    # Hauptsender dürfen auch ohne country-Metadaten
    # erkannt werden.
    # ========================================================

    german = []


    for entry in filtered:

        if is_german(entry):

            german.append(entry)

            continue


        # Hauptsender trotzdem zulassen

        for channel in MAIN_CHANNELS:

            if matches_main_channel(
                entry,
                channel
            ):

                german.append(entry)

                break


    # Falls Metadaten bei IPTV-org fehlen:
    # nicht alles wegwerfen.

    if len(german) < 20:

        print(
            "Warnung: "
            "wenige deutsche Sender über "
            "Metadaten erkannt."
        )

        print(
            "Verwende gefilterte Liste."
        )

        german = filtered


    print(
        "Deutsche Sender:",
        len(german)
    )


    # ========================================================
    # DEDUP
    # ========================================================

    entries = deduplicate(
        german
    )


    print(
        "Nach Deduplizierung:",
        len(entries)
    )


    # ========================================================
    # SORTIERUNG
    # ========================================================

    entries = sort_entries(
        entries
    )


    # ========================================================
    # HAUPTSENDER PRÜFEN
    # ========================================================

    print()
    print("==========================================")
    print("HAUPTSENDER")
    print("==========================================")


    main_found, _ = find_main_channels(
        entries
    )


    found_ids = {
        entry["tvg_id"]
        for entry in main_found
    }


    for number, channel in enumerate(
        MAIN_CHANNELS,
        start=1
    ):

        display_name, ids, names = channel


        found = None


        for entry in main_found:

            if matches_main_channel(
                entry,
                channel
            ):

                found = entry
                break


        if found:

            print(

                f"{number:02d}. "
                f"OK  {display_name} "
                f"-> {found['name']} "
                f"[{found['tvg_id']}]"

            )

        else:

            print(

                f"{number:02d}. "
                f"FEHLT  {display_name}"

            )


    # ========================================================
    # M3U BAUEN
    # ========================================================

    content = build_m3u(
        entries
    )


    # ========================================================
    # SICHER SCHREIBEN
    # ========================================================

    safe_write(
        content
    )


    # ========================================================
    # STATISTIK
    # ========================================================

    print_statistics(
        entries
    )


    # ========================================================
    # ERSTE 20 SENDER
    # ========================================================

    print()
    print("==========================================")
    print("ERSTE SENDER")
    print("==========================================")


    for number, entry in enumerate(
        entries[:20],
        start=1
    ):

        print(

            f"{number:02d}. "
            f"{entry['name']} "
            f"[{entry['tvg_id']}]"

        )


    # ========================================================
    # FERTIG
    # ========================================================

    print()
    print("==========================================")
    print("FERTIG")
    print("==========================================")

    print(
        "Datei:",
        OUTPUT
    )

    print(
        "Backup:",
        BACKUP_OUTPUT
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print()
        print("==========================================")
        print("UPDATE FEHLGESCHLAGEN")
        print("==========================================")

        print(
            error
        )

        print()

        print(
            "Die vorhandene deutsch.m3u "
            "wurde NICHT überschrieben."
        )

        print()

        # Exit-Code != 0 für Cron / Scriptüberwachung

        raise SystemExit(1)

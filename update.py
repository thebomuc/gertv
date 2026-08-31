import re
import os
import shutil
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - update.py
# ============================================================
#
# Priorität:
#
#   Deine feste Senderreihenfolge
#   +
#   dynamische Prioritäten für weitere bekannte Sender
#   +
#   Kategorien für den restlichen Bestand
#
# Wichtig:
#
#   - Sender werden NICHT künstlich erzeugt.
#   - Ist ein Sender nicht verfügbar, erscheint er nicht.
#   - Taucht ein Sender später wieder auf, wird er automatisch
#     an seiner vorgesehenen Position einsortiert.
#   - Geo-blocked wird NICHT ausgeschlossen.
#   - Nicht-Geo-blocked wird bevorzugt.
#   - HD wird bevorzugt.
#   - Bei komplettem Quellenfehler bleibt die alte M3U erhalten.
#
# ============================================================


OUTPUT = "deutsch.m3u"
BACKUP_OUTPUT = "deutsch.m3u.bak"
TEMP_OUTPUT = "deutsch.m3u.tmp"


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
# Diese Reihenfolge bleibt immer bestehen.
#
# Die IDs sind nur bevorzugte Erkennungsmerkmale.
# Der Name dient als Fallback.
#
# ============================================================

FIXED_CHANNELS = [

    ("Das Erste", [
        "DasErste.de"
    ], [
        "das erste",
        "ard"
    ]),

    ("ZDF", [
        "ZDF.de"
    ], [
        "zdf"
    ]),

    ("ZDFinfo", [
        "ZDFinfo.de"
    ], [
        "zdf info",
        "zdfinfo"
    ]),

    ("ZDFneo", [
        "ZDFneo.de"
    ], [
        "zdf neo",
        "zdfneo"
    ]),

    ("3sat", [
        "3sat.de"
    ], [
        "3sat"
    ]),

    ("kabel eins", [
        "KabelEins.de"
    ], [
        "kabel eins",
        "kabel1"
    ]),

    ("ProSieben", [
        "ProSieben.de"
    ], [
        "prosieben"
    ]),

    # RTL ist absichtlich enthalten.
    #
    # Ist RTL aktuell nicht verfügbar:
    # -> es erscheint nicht.
    #
    # Taucht RTL später wieder auf:
    # -> automatisch hier einsortieren.
    #
    ("RTL", [
        "RTL.de"
    ], [
        "rtl"
    ]),

    ("sixx", [
        "sixx.de"
    ], [
        "sixx"
    ]),

    ("Sat.1 Gold", [
        "SAT1Gold.de"
    ], [
        "sat 1 gold",
        "sat.1 gold",
        "sat1 gold"
    ]),

    ("ARD-alpha", [
        "ARDAlpha.de"
    ], [
        "ard alpha",
        "ard-alpha"
    ]),

    ("Phoenix", [
        "Phoenix.de"
    ], [
        "phoenix"
    ]),

    ("ARTE", [
        "Arte.de"
    ], [
        "arte"
    ]),

    ("Tagesschau24", [
        "Tagesschau24.de"
    ], [
        "tagesschau24",
        "tagesschau 24"
    ]),

    ("MDR Fernsehen", [
        "MDRFernsehen.de"
    ], [
        "mdr fernsehen"
    ]),

    ("NDR Hamburg", [
        "NDRHamburg.de"
    ], [
        "ndr hamburg"
    ]),

    ("noa4 Hamburg", [], [
        "noa4",
        "noa 4"
    ]),

    ("Hamburg 1", [
        "Hamburg1.de"
    ], [
        "hamburg 1",
        "hamburg1"
    ]),

    ("Radio Weser TV Bremen", [], [
        "radio weser tv",
        "weser tv"
    ]),

    ("Radio Bremen Fernsehen", [
        "RadioBremenTV.de"
    ], [
        "radio bremen fernsehen",
        "radio bremen tv"
    ]),

    ("WDR Fernsehen", [
        "WDRKoeln.de",
        "WDR.de"
    ], [
        "wdr fernsehen"
    ]),

    ("SWR Fernsehen Rheinland-Pfalz", [
        "SWRRheinlandPfalz.de"
    ], [
        "swr fernsehen rheinland pfalz",
        "swr rheinland pfalz",
        "swr rp"
    ]),

    ("hr-fernsehen", [
        "HRFernsehen.de"
    ], [
        "hr fernsehen",
        "hr-fernsehen"
    ]),

    ("SR Fernsehen", [
        "SRFernsehen.de"
    ], [
        "sr fernsehen"
    ]),

    ("rbb Fernsehen", [
        "RBB.de"
    ], [
        "rbb fernsehen"
    ]),

    ("Oberpfalz TV", [], [
        "oberpfalz tv",
        "oberpfalztv"
    ]),

    ("BR Fernsehen Nord", [], [
        "br fernsehen nord"
    ]),

    ("München TV", [
        "MunchenTV.de@SD"
    ], [
        "münchen tv",
        "munchen tv",
        "muenchen tv"
    ]),

    ("Nachrichten 360", [], [
        "nachrichten 360"
    ]),

    ("SPIEGEL TV", [], [
        "spiegel tv"
    ]),

    ("N24 Doku", [
        "N24Doku.de"
    ], [
        "n24 doku",
        "n24doku"
    ]),

    ("RT DE", [], [
        "rt de",
        "rt deutsch"
    ]),

    ("DokuSat", [], [
        "dokusat"
    ]),

    ("Authentic History", [], [
        "authentic history"
    ]),

    ("Bibel TV", [
        "BibelTV.de"
    ], [
        "bibel tv",
        "bibeltv"
    ]),

    ("EWTN", [
        "EWTN.de"
    ], [
        "ewtn"
    ]),

    ("K-TV", [
        "K-TV.de"
    ], [
        "k tv",
        "k-tv",
        "k tv deutschland"
    ]),

    ("Terra Mater Wild", [], [
        "terra mater wild",
        "terra mater"
    ]),
]


# ============================================================
# WEITERE PRIVATE
#
# Diese Sender werden NUR genommen, wenn sie vorhanden sind.
#
# Sie kommen NACH RTL und den anderen festen Sendern.
# ============================================================

PRIVATE_ORDER = [

    ("Sat.1", [
        "SAT1.de"
    ], [
        "sat 1",
        "sat.1"
    ]),

    ("VOX", [
        "VOX.de"
    ], [
        "vox"
    ]),

    ("RTL Zwei", [
        "RTLZWEI.de"
    ], [
        "rtl zwei",
        "rtl2",
        "rtl ii"
    ]),

    ("Super RTL", [
        "SuperRTL.de"
    ], [
        "super rtl"
    ]),

    ("NITRO", [
        "NITRO.de"
    ], [
        "nitro"
    ]),

    ("VOXup", [
        "VOXup.de"
    ], [
        "voxup",
        "vox up"
    ]),

    ("ProSieben MAXX", [
        "ProSiebenMAXX.de"
    ], [
        "prosieben maxx"
    ]),

    ("kabel eins Doku", [
        "KabelEinsDoku.de"
    ], [
        "kabel eins doku",
        "kabel1 doku"
    ]),

    ("TELE 5", [
        "TELE5.de"
    ], [
        "tele 5",
        "tele5"
    ]),

    ("DMAX", [
        "DMAX.de"
    ], [
        "dmax"
    ]),

]


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
# KATEGORIEN
# ============================================================

CATEGORY_ORDER = {

    "00 Priorität": 0,
    "01 Weitere Private": 1,
    "02 Regional": 2,
    "03 Dritte Programme": 3,
    "04 Nachrichten": 4,
    "05 Dokumentation & Wissen": 5,
    "06 Kinder": 6,
    "07 Religion": 7,
    "08 Sport": 8,
    "09 Rakuten TV": 9,
    "10 Weitere deutsche Sender": 10,

}


# ============================================================
# NORMALIZE
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

    return " ".join(
        value.split()
    )


# ============================================================
# DOWNLOAD
# ============================================================

def download(url):

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
# GEO-BLOCKED ERKENNUNG
# ============================================================

def is_geo_blocked(entry):

    text = (
        entry["info"]
        + " "
        + entry["name"]
        + " "
        + entry.get("stream_label", "")
    )

    text = normalize(text)

    return (
        "geo blocked" in text
        or "geoblocked" in text
        or "geo block" in text
    )


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

        entries.append(entry)

        i += 2

    return entries


# ============================================================
# AUSSCHLÜSSE
# ============================================================

def excluded(entry):

    if entry["tvg_id"] in EXCLUDE_IDS:
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
# DEUTSCHER SENDER
# ============================================================

def is_german(entry):

    country = normalize(
        entry["country"]
    )

    language = normalize(
        entry["language"]
    )

    tvg_id = entry["tvg_id"].lower()

    if (
        "germany" in country
        or "deutschland" in country
        or country == "de"
        or "deutsch" in language
        or tvg_id.endswith(".de")
    ):
        return True

    return False


# ============================================================
# SENDER MATCHEN
# ============================================================

def matches_definition(entry, definition):

    display_name, ids, names = definition

    tvg_id = entry["tvg_id"]

    # 1. Exakte ID
    if tvg_id and tvg_id in ids:
        return True

    # 2. Name
    combined = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    for name in names:

        target = normalize(name)

        if target and target in combined:

            return True

    return False


# ============================================================
# BESTEN STREAM AUSWÄHLEN
#
# Reihenfolge:
#
#   1. nicht Geo-blocked + HD
#   2. nicht Geo-blocked
#   3. Geo-blocked + HD
#   4. Geo-blocked
#
# Geo-blocked wird also niemals automatisch entfernt.
# ============================================================

def stream_score(entry):

    geo = is_geo_blocked(entry)
    hd = is_hd(entry)

    if not geo and hd:
        return 0

    if not geo and not hd:
        return 1

    if geo and hd:
        return 2

    return 3


# ============================================================
# BESTEN MATCH FINDEN
# ============================================================

def find_best_match(entries, definition):

    matches = [

        entry

        for entry in entries

        if matches_definition(
            entry,
            definition
        )

    ]

    if not matches:
        return None

    matches.sort(
        key=stream_score
    )

    return matches[0]


# ============================================================
# FIXED CHANNELS
# ============================================================

def build_fixed_channels(entries):

    result = []

    used_ids = set()

    for definition in FIXED_CHANNELS:

        entry = find_best_match(
            entries,
            definition
        )

        if not entry:
            continue

        tvg_id = entry["tvg_id"]

        if not tvg_id:
            continue

        if tvg_id in used_ids:
            continue

        entry["category"] = "00 Priorität"

        entry["fixed_name"] = definition[0]

        result.append(entry)

        used_ids.add(tvg_id)

    return result, used_ids


# ============================================================
# WEITERE PRIVATE
# ============================================================

def build_private_channels(
    entries,
    used_ids
):

    result = []

    local_used = set(used_ids)

    for definition in PRIVATE_ORDER:

        entry = find_best_match(
            entries,
            definition
        )

        if not entry:
            continue

        tvg_id = entry["tvg_id"]

        if not tvg_id:
            continue

        if tvg_id in local_used:
            continue

        entry["category"] = (
            "01 Weitere Private"
        )

        entry["fixed_name"] = definition[0]

        result.append(entry)

        local_used.add(tvg_id)

    return result, local_used


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
    # Rakuten
    # --------------------------------------------------------

    if "rakuten tv" in name:

        return "09 Rakuten TV"

    # --------------------------------------------------------
    # Regional
    # --------------------------------------------------------

    regional_words = [

        "regional",
        "ndr hamburg",
        "noa4",
        "hamburg 1",
        "radio weser",
        "weser tv",
        "radio bremen",
        "oberpfalz tv",
        "oberpfalztv",
        "münchen tv",
        "munchen tv",
        "muenchen tv",
        "br fernsehen nord",
        "swr rheinland pfalz",

    ]

    if any(
        word in name
        for word in regional_words
    ):

        return "02 Regional"

    # --------------------------------------------------------
    # Dritte
    # --------------------------------------------------------

    third_words = [

        "ndr",
        "wdr",
        "swr",
        "mdr",
        "hr fernsehen",
        "rbb",
        "sr fernsehen",
        "br fernsehen",

    ]

    if any(
        word in name
        for word in third_words
    ):

        return "03 Dritte Programme"

    # --------------------------------------------------------
    # Nachrichten
    # --------------------------------------------------------

    news_words = [

        "welt",
        "n tv",
        "ntv",
        "euronews",
        "nachrichten",
        "news",

    ]

    if any(
        word in name
        for word in news_words
    ):

        return "04 Nachrichten"

    # --------------------------------------------------------
    # Dokumentation
    # --------------------------------------------------------

    doc_words = [

        "doku",
        "dokumentation",
        "documentary",
        "wissen",
        "history",
        "science",

    ]

    if any(
        word in name
        for word in doc_words
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

    if any(
        word in name
        for word in [
            "bibel tv",
            "bibeltv",
            "ewtn",
            "k tv",
            "k-tv",
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

    return "10 Weitere deutsche Sender"


# ============================================================
# DEDUP
#
# Geo-blocked und normale Streams desselben Senders:
# bester Stream gewinnt.
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

        if (
            stream_score(entry)
            < stream_score(existing)
        ):

            result[tvg_id] = entry

    return list(
        result.values()
    )


# ============================================================
# REST SORTIEREN
# ============================================================

def sort_rest(entries):

    for entry in entries:

        entry["category"] = get_category(
            entry
        )

    entries.sort(

        key=lambda entry: (

            CATEGORY_ORDER.get(
                entry["category"],
                99
            ),

            # Innerhalb von Rakuten alphabetisch
            # und sonst ebenfalls sauber sortieren.

            normalize(
                entry["name"]
            ),

        )

    )

    return entries


# ============================================================
# M3U INFO BEREINIGEN
# ============================================================

def clean_info(entry):

    info = entry["info"]

    # altes group-title entfernen

    info = re.sub(

        r'\s+group-title="[^"]*"',

        "",

        info,

        flags=re.IGNORECASE

    )

    # alten Sendernamen entfernen

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
# M3U BAUEN
# ============================================================

def build_m3u(entries):

    output = [

        "#EXTM3U",

        "",

        "# ==================================================",

        "# GER TV",

        "# Automatisch aktualisiert",

        "# Quelle: IPTV-org",

        "#",

        "# Geo-blocked wird nicht ausgeschlossen.",

        "# Nicht Geo-blocked wird bevorzugt.",

        "# HD wird bevorzugt.",

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

    with open(
        TEMP_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            content
        )

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
            f"nur {extinf_count} Sender."

        )

    if url_count < 10:

        os.remove(
            TEMP_OUTPUT
        )

        raise RuntimeError(

            "Sicherheitsprüfung fehlgeschlagen: "
            f"nur {url_count} URLs."

        )

    if os.path.exists(OUTPUT):

        shutil.copy2(
            OUTPUT,
            BACKUP_OUTPUT
        )

    os.replace(
        TEMP_OUTPUT,
        OUTPUT
    )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    print()
    print("==========================================")
    print("GER TV - UPDATE")
    print("==========================================")
    print()

    all_entries = []

    successful_sources = 0

    # ========================================================
    # DOWNLOAD
    # ========================================================

    for source_name, url in SOURCES:

        try:

            print(
                f"Lade {source_name} ..."
            )

            text = download(
                url
            )

            entries = parse_m3u(
                text,
                source_name
            )

            if not entries:

                raise RuntimeError(
                    "keine Sender gefunden"
                )

            print(
                f"  OK: {len(entries)}"
            )

            all_entries.extend(
                entries
            )

            successful_sources += 1

        except Exception as error:

            print(
                f"  FEHLER: {error}"
            )

    # ========================================================
    # QUELLENPRÜFUNG
    # ========================================================

    if successful_sources == 0:

        raise RuntimeError(

            "Keine Quelle konnte geladen werden. "
            "Alte M3U bleibt erhalten."

        )

    if len(all_entries) < 20:

        raise RuntimeError(

            "Ungewöhnlich wenige Sender geladen: "
            f"{len(all_entries)}"

        )

    print()
    print(
        "Gesamt geladen:",
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
    # DEUTSCHE SENDER
    # ========================================================

    german = [

        entry

        for entry in filtered

        if is_german(entry)

    ]

    # Fallback, falls IPTV-org Metadaten fehlen.

    if len(german) < 20:

        print(
            "Warnung: wenige Sender über "
            "Deutschland-Metadaten erkannt."
        )

        print(
            "Verwende gefilterte Daten."
        )

        german = filtered

    print(
        "Deutsche Sender:",
        len(german)
    )

    # ========================================================
    # DUPLIKATE
    # ========================================================

    german = deduplicate(
        german
    )

    print(
        "Nach Deduplizierung:",
        len(german)
    )

    # ========================================================
    # FESTE PRIORITÄT
    # ========================================================

    fixed, used_ids = build_fixed_channels(
        german
    )

    # ========================================================
    # WEITERE PRIVATE
    # ========================================================

    private, used_ids = build_private_channels(
        german,
        used_ids
    )

    # ========================================================
    # REST
    # ========================================================

    rest = [

        entry

        for entry in german

        if entry["tvg_id"]
        not in used_ids

    ]

    rest = sort_rest(
        rest
    )

    # ========================================================
    # ENDGÜLTIGE LISTE
    # ========================================================

    entries = (
        fixed
        + private
        + rest
    )

    # ========================================================
    # M3U
    # ========================================================

    content = build_m3u(
        entries
    )

    safe_write(
        content
    )

    # ========================================================
    # AUSGABE
    # ========================================================

    print()
    print("==========================================")
    print("PRIORITÄTSSENDER")
    print("==========================================")

    for number, entry in enumerate(
        fixed,
        start=1
    ):

        geo = (
            "GEO"
            if is_geo_blocked(entry)
            else "OK"
        )

        hd = (
            "HD"
            if is_hd(entry)
            else "SD"
        )

        print(

            f"{number:02d}. "
            f"{entry['name']} "
            f"[{hd}/{geo}] "
            f"[{entry['tvg_id']}]"

        )

    print()
    print("==========================================")
    print("WEITERE PRIVATE")
    print("==========================================")

    for number, entry in enumerate(
        private,
        start=1
    ):

        print(
            f"{number:02d}. "
            f"{entry['name']} "
            f"[{entry['tvg_id']}]"
        )

    print()
    print("==========================================")
    print("ERGEBNIS")
    print("==========================================")

    print(
        "Sender gesamt:",
        len(entries)
    )

    print(
        "Prioritätssender:",
        len(fixed)
    )

    print(
        "Weitere Private:",
        len(private)
    )

    print(
        "Weitere Sender:",
        len(rest)
    )

    print()
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

        raise SystemExit(1)

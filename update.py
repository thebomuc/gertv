import re
import os
import shutil
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - update.py
# ============================================================
#
# Täglicher automatischer Aufbau von deutsch.m3u
#
# PRIORITÄT:
#   1. feste persönliche Reihenfolge
#   2. weitere Private
#   3. Regional
#   4. Dritte Programme
#   5. Nachrichten
#   6. Dokumentation
#   7. Kinder
#   8. Religion
#   9. Sport
#   10. Rakuten TV
#   11. weitere deutsche Sender
#
# STREAM-PRIORITÄT:
#   1. HD + nicht Geo-blocked
#   2. SD + nicht Geo-blocked
#   3. HD + Geo-blocked
#   4. SD + Geo-blocked
#
# WICHTIG:
#   - Geo-blocked Sender werden NICHT entfernt.
#   - Wenn kein normaler Stream existiert, bleibt Geo-blocked.
#   - Nicht vorhandene Sender werden NICHT künstlich erzeugt.
#   - Bei Fehlern wird die vorhandene M3U nicht überschrieben.
#   - Ein Backup wird vor dem Überschreiben erstellt.
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
        "Bayern",
        "https://iptv-org.github.io/iptv/subdivisions/de-by.m3u"
    ),

    (
        "Berlin",
        "https://iptv-org.github.io/iptv/subdivisions/de-be.m3u"
    ),

    (
        "Brandenburg",
        "https://iptv-org.github.io/iptv/subdivisions/de-bb.m3u"
    ),

    (
        "Hamburg",
        "https://iptv-org.github.io/iptv/subdivisions/de-hh.m3u"
    ),

    (
        "Mecklenburg-Vorpommern",
        "https://iptv-org.github.io/iptv/subdivisions/de-mv.m3u"
    ),

    (
        "Niedersachsen",
        "https://iptv-org.github.io/iptv/subdivisions/de-ni.m3u"
    ),

    (
        "Schleswig-Holstein",
        "https://iptv-org.github.io/iptv/subdivisions/de-sh.m3u"
    ),
]


# ============================================================
# FESTE REIHENFOLGE
#
# Diese Reihenfolge ist wichtiger als Kategorien.
#
# RTL:
#   Wenn aktuell nicht vorhanden -> kein Eintrag.
#   Wenn später wieder vorhanden -> automatisch hier.
#
# ============================================================

FIXED_CHANNELS = [

    ("Das Erste",
     ["DasErste.de"],
     ["das erste"]),

    ("ZDF",
     ["ZDF.de"],
     ["zdf"]),

    ("ZDFinfo",
     ["ZDFinfo.de"],
     ["zdfinfo", "zdf info"]),

    ("ZDFneo",
     ["ZDFneo.de"],
     ["zdfneo", "zdf neo"]),

    ("3sat",
     ["3sat.de"],
     ["3sat"]),

    ("kabel eins",
     ["KabelEins.de"],
     ["kabel eins", "kabel1"]),

    ("ProSieben",
     ["ProSieben.de"],
     ["prosieben"]),

    ("RTL",
     ["RTL.de"],
     ["rtl"]),

    ("sixx",
     ["sixx.de"],
     ["sixx"]),

    ("Sat.1 Gold",
     ["SAT1Gold.de"],
     ["sat.1 gold", "sat 1 gold", "sat1 gold"]),

    ("ARD-alpha",
     ["ARDalpha.de"],
     ["ard alpha", "ard-alpha"]),

    ("Phoenix",
     ["Phoenix.de"],
     ["phoenix"]),

    ("ARTE",
     ["ARTEDeutsch.de", "Arte.de"],
     ["arte"]),

    ("Tagesschau24",
     ["tagesschau24.de"],
     ["tagesschau24", "tagesschau 24"]),

    # MDR:
    # Es gibt aktuell regionale IDs.
    # Alle drei werden akzeptiert.
    # Der erste gefundene passende Stream wird verwendet.
    ("MDR Fernsehen",
     [
         "MDRFernsehenSachsen.de",
         "MDRFernsehenSachsenAnhalt.de",
         "MDRFernsehenThuringen.de",
     ],
     [
         "mdr sachsen",
         "mdr sachsen anhalt",
         "mdr thüringen",
         "mdr fernsehen",
     ]),

    ("NDR Hamburg",
     [
         "NDRFernsehenHamburg.de",
         "NDRFernsehen.de@Hamburg",
     ],
     [
         "ndr hamburg",
     ]),

    ("noa4 Hamburg",
     [],
     [
         "noa4 hamburg",
         "noa4 hh",
     ]),

    ("Hamburg 1",
     ["Hamburg1.de"],
     [
         "hamburg 1",
         "hamburg1",
     ]),

    ("Radio Weser TV Bremen",
     [],
     [
         "radio weser tv",
         "weser tv bremen",
     ]),

    ("Radio Bremen Fernsehen",
     [
         "RadioBremenFernsehen.de",
         "RadioBremenTV.de",
     ],
     [
         "radio bremen",
         "radio bremen fernsehen",
         "radio bremen tv",
     ]),

    ("WDR Fernsehen",
     [
         "WDR.de",
         "WDRKoeln.de",
     ],
     [
         "wdr fernsehen",
         "wdr",
     ]),

    ("SWR Fernsehen Rheinland-Pfalz",
     [
         "SWRFernsehenRheinlandPfalz.de",
     ],
     [
         "swr rheinland pfalz",
         "swr fernsehen rheinland pfalz",
     ]),

    ("hr-fernsehen",
     [
         "HRFernsehen.de",
     ],
     [
         "hr fernsehen",
         "hr-fernsehen",
     ]),

    ("SR Fernsehen",
     [
         "SRFernsehen.de",
     ],
     [
         "sr fernsehen",
         "sr",
     ]),

    ("rbb Fernsehen",
     [
         "RBBBerlin.de",
         "RBBBrandenburg.de",
         "RBB.de",
     ],
     [
         "rbb berlin",
         "rbb brandenburg",
         "rbb fernsehen",
     ]),

    ("Oberpfalz TV",
     [],
     [
         "oberpfalz tv",
         "oberpfalztv",
     ]),

    ("BR Fernsehen Nord",
     [],
     [
         "br fernsehen nord",
         "br nord",
     ]),

    ("München TV",
     [
         "MunchenTV.de",
         "MunchenTV.de@SD",
     ],
     [
         "münchen tv",
         "munchen tv",
         "muenchen tv",
         "münchen.tv",
     ]),

    ("Nachrichten 360",
     [],
     [
         "nachrichten 360",
     ]),

    ("SPIEGEL TV",
     [],
     [
         "spiegel tv",
     ]),

    ("N24 Doku",
     [
         "N24Doku.de",
     ],
     [
         "n24 doku",
         "n24doku",
     ]),

    ("RT DE",
     [
         "RTDE.de",
         "RTDEUTSCH.de",
     ],
     [
         "rt de",
         "rt deutsch",
         "rt deutsch",
     ]),

    ("DokuSat",
     [],
     [
         "dokusat",
     ]),

    ("Authentic History",
     [],
     [
         "authentic history",
     ]),

    ("Bibel TV",
     [
         "BibelTV.de",
     ],
     [
         "bibel tv",
         "bibeltv",
     ]),

    ("EWTN",
     [
         "EWTN.de",
     ],
     [
         "ewtn",
     ]),

    ("K-TV",
     [
         "K-TV.de",
     ],
     [
         "k-tv",
         "k tv",
     ]),

    ("Terra Mater Wild",
     [],
     [
         "terra mater wild",
     ]),
]


# ============================================================
# WEITERE PRIVATE
#
# Diese kommen hinter RTL / sixx / Sat.1 Gold.
# Nur wenn tatsächlich vorhanden.
# ============================================================

PRIVATE_ORDER = [

    ("Sat.1",
     ["SAT1.de"],
     ["sat.1", "sat 1"]),

    ("VOX",
     ["VOX.de"],
     ["vox"]),

    ("RTL Zwei",
     ["RTLZWEI.de"],
     ["rtl zwei", "rtl2", "rtl ii"]),

    ("Super RTL",
     ["SuperRTL.de"],
     ["super rtl"]),

    ("NITRO",
     ["NITRO.de"],
     ["nitro"]),

    ("VOXup",
     ["VOXup.de"],
     ["voxup", "vox up"]),

    ("ProSieben MAXX",
     ["ProSiebenMAXX.de"],
     ["prosieben maxx"]),

    ("kabel eins Doku",
     ["KabelEinsDoku.de"],
     ["kabel eins doku", "kabel1 doku"]),

    ("TELE 5",
     ["TELE5.de"],
     ["tele 5", "tele5"]),

    ("DMAX",
     ["DMAX.de"],
     ["dmax"]),

]


# ============================================================
# AUSGESCHLOSSEN
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

    "deluxe music",
    "music",
    "musik",
    "schlager",
]


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
# ATTRIBUTE
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
# PARSER
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

        if not url:

            i += 2
            continue

        if url.startswith("#"):

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

            "group": get_attribute(
                line,
                "group-title"
            ),

            "source": source,

            "url": url,

        }

        entries.append(entry)

        i += 2

    return entries


# ============================================================
# AUSSCHLUSS
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
# GEO BLOCKED
# ============================================================

def is_geo_blocked(entry):

    text = normalize(
        entry["info"]
        + " "
        + entry["name"]
        + " "
        + entry["tvg_name"]
    )

    return (
        "geo blocked" in text
        or "geo blocked" in text.replace(
            "geo blocked",
            "geo blocked"
        )
        or "geoblocked" in text
    )


# ============================================================
# HD
# ============================================================

def is_hd(entry):

    text = normalize(
        entry["info"]
        + " "
        + entry["name"]
        + " "
        + entry["tvg_name"]
    )

    words = set(
        text.split()
    )

    return (
        "hd" in words
        or "1080p" in words
        or "720p" in words
    )


# ============================================================
# STREAM SCORE
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
# MATCH
# ============================================================

def matches_definition(entry, definition):

    display_name, ids, names = definition

    tvg_id = entry["tvg_id"].strip()

    # ========================================================
    # 1. TVG-ID
    #
    # ID muss EXAKT übereinstimmen.
    # Niemals Teilstring-Suche bei IDs.
    # ========================================================

    if tvg_id and tvg_id in ids:
        return True

    # ========================================================
    # 2. Namen
    #
    # Erst normalisieren.
    # ========================================================

    entry_name = normalize(
        entry["name"]
    )

    tvg_name = normalize(
        entry["tvg_name"]
    )

    # Beide Namen getrennt prüfen.
    names_to_check = {
        entry_name,
        tvg_name,
    }

    # ========================================================
    # 3. Exakte Namensübereinstimmung
    # ========================================================

    for candidate in names:

        target = normalize(
            candidate
        )

        if not target:
            continue

        if target in names_to_check:
            return True

    # ========================================================
    # 4. Sichere Sonderfälle
    #
    # Nur längere, eindeutige Namen dürfen innerhalb
    # eines längeren Sendernamens vorkommen.
    #
    # NICHT für:
    #   rtl
    #   zdf
    #   vox
    #   arte
    #   sr
    #   ndr
    # usw.
    # ========================================================

    SAFE_PARTIAL_NAMES = {
        "zdf info",
        "zdf neo",
        "sat 1 gold",
        "kabel eins doku",
        "prosieben maxx",
        "rtl zwei",
        "radio bremen fernsehen",
        "radio bremen tv",
        "radio weser tv",
        "radio weser tv bremen",
        "swr fernsehen rheinland pfalz",
        "br fernsehen nord",
        "terra mater wild",
        "authentic history",
        "nachrichten 360",
        "oberpfalz tv",
        "muenchen tv",
        "münchen tv",
        "noa4 hamburg",
    }

    for candidate in names:

        target = normalize(
            candidate
        )

        if target not in SAFE_PARTIAL_NAMES:
            continue

        for value in names_to_check:

            if target in value:
                return True

    return False


# ============================================================
# BESTEN MATCH
# ============================================================

def find_matches(
    entries,
    definition
):

    return [

        entry

        for entry in entries

        if matches_definition(
            entry,
            definition
        )

    ]


def find_best_match(
    entries,
    definition
):

    matches = find_matches(
        entries,
        definition
    )

    if not matches:
        return None

    matches.sort(
        key=stream_score
    )

    return matches[0]


# ============================================================
# FESTE SENDER
# ============================================================

def build_fixed(entries):

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

        entry["priority"] = (
            len(result)
        )

        entry["display_name"] = (
            definition[0]
        )

        result.append(entry)

        used_ids.add(tvg_id)

    return result, used_ids


# ============================================================
# WEITERE PRIVATE
# ============================================================

def build_private(
    entries,
    used_ids
):

    result = []

    local_used = set(
        used_ids
    )

    for definition in PRIVATE_ORDER:

        matches = find_matches(
            entries,
            definition
        )

        if not matches:
            continue

        # Besten Stream wählen
        matches.sort(
            key=stream_score
        )

        for entry in matches:

            tvg_id = entry["tvg_id"]

            if not tvg_id:
                continue

            if tvg_id in local_used:
                continue

            entry["category"] = (
                "01 Weitere Private"
            )

            entry["display_name"] = (
                definition[0]
            )

            result.append(entry)

            local_used.add(
                tvg_id
            )

            break

    return result, local_used


# ============================================================
# KATEGORIE
# ============================================================

def get_category(entry):

    name = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    # Rakuten IMMER ganz hinten
    if "rakuten tv" in name:

        return "09 Rakuten TV"

    # Regional
    regional = [
        "ndr hamburg",
        "noa4",
        "hamburg 1",
        "radio weser",
        "weser tv",
        "radio bremen",
        "oberpfalz tv",
        "oberpfalztv",
        "munchen tv",
        "muenchen tv",
        "br fernsehen nord",
        "swr rheinland pfalz",
    ]

    if any(
        word in name
        for word in regional
    ):

        return "02 Regional"

    # Dritte
    third = [
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
        for word in third
    ):

        return "03 Dritte Programme"

    # Nachrichten
    news = [
        "welt",
        "n tv",
        "ntv",
        "euronews",
        "nachrichten",
        "news",
    ]

    if any(
        word in name
        for word in news
    ):

        return "04 Nachrichten"

    # Doku
    docs = [
        "doku",
        "dokumentation",
        "history",
        "wissen",
        "science",
        "spiegel tv",
        "authentic history",
    ]

    if any(
        word in name
        for word in docs
    ):

        return "05 Dokumentation & Wissen"

    # Kinder
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

    # Religion
    if any(
        word in name
        for word in [
            "bibel tv",
            "bibeltv",
            "ewtn",
            "k tv",
            "erf",
        ]
    ):

        return "07 Religion"

    # Sport
    if "sport" in name:

        return "08 Sport"

    return "10 Weitere deutsche Sender"


# ============================================================
# DEDUP
#
# WICHTIG:
# Sender-ID wird dedupliziert.
# Der beste Stream gewinnt.
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

        old = result[tvg_id]

        if (
            stream_score(entry)
            < stream_score(old)
        ):

            result[tvg_id] = entry

    return list(
        result.values()
    )


# ============================================================
# REST
# ============================================================

def sort_rest(entries):

    for entry in entries:

        entry["category"] = (
            get_category(entry)
        )

    category_order = {
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

    entries.sort(
        key=lambda entry: (
            category_order.get(
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
# M3U INFO
# ============================================================

def clean_info(
    entry,
    category
):

    info = entry["info"]

    # altes group-title entfernen

    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

    # alten Namen entfernen

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
# M3U
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
        "# Eigene Senderpriorität",
        "# HD bevorzugt",
        "# Nicht Geo-blocked bevorzugt",
        "# Geo-blocked bleibt erhalten, falls notwendig",
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

    return (
        "\n".join(output)
        + "\n"
    )


# ============================================================
# SICHERES SCHREIBEN
# ============================================================

def safe_write(content):

    with open(
        TEMP_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    # Datei prüfen

    with open(
        TEMP_OUTPUT,
        "r",
        encoding="utf-8"
    ) as file:

        check = file.read()

    extinf_count = check.count(
        "#EXTINF:"
    )

    url_count = sum(

        1

        for line in check.splitlines()

        if (
            line.startswith(
                "http://"
            )
            or line.startswith(
                "https://"
            )
        )

    )

    if extinf_count < 10:

        os.remove(
            TEMP_OUTPUT
        )

        raise RuntimeError(
            "Zu wenige Sender."
        )

    if url_count < 10:

        os.remove(
            TEMP_OUTPUT
        )

        raise RuntimeError(
            "Zu wenige URLs."
        )

    # Backup

    if os.path.exists(
        OUTPUT
    ):

        shutil.copy2(
            OUTPUT,
            BACKUP_OUTPUT
        )

    # Atomar ersetzen

    os.replace(
        TEMP_OUTPUT,
        OUTPUT
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=========================================="
    )
    print(
        "GER TV - UPDATE"
    )
    print(
        "=========================================="
    )
    print()

    all_entries = []

    successful_sources = 0

    # --------------------------------------------------------
    # Quellen laden
    # --------------------------------------------------------

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
                    "Keine Einträge."
                )

            print(
                f"  OK: {len(entries)} Sender"
            )

            all_entries.extend(
                entries
            )

            successful_sources += 1

        except Exception as error:

            print(
                f"  FEHLER: {error}"
            )

    # --------------------------------------------------------
    # Keine Quelle
    # --------------------------------------------------------

    if successful_sources == 0:

        raise RuntimeError(
            "Keine Quelle konnte geladen werden."
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
    # Deduplizieren
    # --------------------------------------------------------

    filtered = deduplicate(
        filtered
    )

    print(
        "Nach Deduplizierung:",
        len(filtered)
    )

    # --------------------------------------------------------
    # Feste Sender
    # --------------------------------------------------------

    fixed, used_ids = build_fixed(
        filtered
    )

    # --------------------------------------------------------
    # Weitere Private
    # --------------------------------------------------------

    private, used_ids = build_private(
        filtered,
        used_ids
    )

    # --------------------------------------------------------
    # Rest
    # --------------------------------------------------------

    rest = [

        entry

        for entry in filtered

        if entry["tvg_id"]
        not in used_ids

    ]

    rest = sort_rest(
        rest
    )

    # --------------------------------------------------------
    # Endgültige Reihenfolge
    # --------------------------------------------------------

    entries = (
        fixed
        + private
        + rest
    )

    # --------------------------------------------------------
    # M3U
    # --------------------------------------------------------

    content = build_m3u(
        entries
    )

    safe_write(
        content
    )

    # --------------------------------------------------------
    # Ausgabe
    # --------------------------------------------------------

    print()
    print(
        "=========================================="
    )
    print(
        "FESTE PRIORITÄT"
    )
    print(
        "=========================================="
    )

    for number, entry in enumerate(
        fixed,
        start=1
    ):

        hd = (
            "HD"
            if is_hd(entry)
            else "SD"
        )

        geo = (
            "GEO"
            if is_geo_blocked(entry)
            else "OK"
        )

        print(
            f"{number:02d}. "
            f"{entry['name']} "
            f"[{hd}/{geo}] "
            f"[{entry['tvg_id']}]"
        )

    print()
    print(
        "=========================================="
    )
    print(
        "WEITERE PRIVATE"
    )
    print(
        "=========================================="
    )

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
    print(
        "=========================================="
    )
    print(
        "ERGEBNIS"
    )
    print(
        "=========================================="
    )

    print(
        "Gesamt:",
        len(entries)
    )

    print(
        "Feste Priorität:",
        len(fixed)
    )

    print(
        "Weitere Private:",
        len(private)
    )

    print(
        "Rest:",
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
        print(
            "=========================================="
        )
        print(
            "UPDATE FEHLGESCHLAGEN"
        )
        print(
            "=========================================="
        )

        print(
            error
        )

        print()
        print(
            "Die vorhandene deutsch.m3u "
            "wurde NICHT überschrieben."
        )

        # temporäre Datei entfernen

        if os.path.exists(
            TEMP_OUTPUT
        ):

            try:
                os.remove(
                    TEMP_OUTPUT
                )
            except OSError:
                pass

        raise SystemExit(1)

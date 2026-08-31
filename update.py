import re
import os
import shutil
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - update.py
# ============================================================
#
# Erstellt täglich:
#
#     deutsch.m3u
#
# Priorität:
#
#   00 Persönliche feste Reihenfolge
#   01 Weitere Private
#   02 Regional
#   03 Dritte Programme
#   04 Nachrichten
#   05 Dokumentation & Wissen
#   06 Kinder
#   07 Religion
#   08 Sport
#   09 Rakuten TV
#   10 Weitere deutsche Sender
#
#
# STREAM-PRIORITÄT:
#
#   1. HD + nicht Geo-blocked
#   2. SD + nicht Geo-blocked
#   3. HD + Geo-blocked
#   4. SD + Geo-blocked
#
#
# WICHTIG:
#
# - Geo-blocked wird NICHT automatisch entfernt.
# - Gibt es nur einen Geo-blocked Stream, bleibt er drin.
# - @HD und @SD gelten als Varianten desselben Senders.
# - Regionale Varianten wie @Hamburg / @Nord bleiben getrennt.
# - RTL erscheint nur, wenn tatsächlich gefunden.
# - Totally Turtles kann nicht als RTL erkannt werden.
# - Rakuten TV kommt immer ans Ende.
# - Bei einem fehlerhaften Download wird die alte M3U nicht
#   überschrieben.
# - Vor dem erfolgreichen Überschreiben wird ein Backup erstellt.
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
# Diese Reihenfolge steht immer ganz vorne.
#
# Sender, die aktuell nicht verfügbar sind, werden übersprungen.
#
# RTL ist absichtlich hier zwischen ProSieben und den weiteren
# privaten Sendern.
#
# Terra Mater Wild ist am Ende deiner persönlichen Reihenfolge.
# ============================================================

FIXED_CHANNELS = [

    # --------------------------------------------------------
    # Hauptsender
    # --------------------------------------------------------

    (
        "Das Erste",
        [
            "daserste.de",
        ],
        [
            "das erste",
        ],
    ),

    (
        "ZDF",
        [
            "zdf.de",
        ],
        [
            "zdf",
        ],
    ),

    (
        "ZDFinfo",
        [
            "zdfinfo.de",
        ],
        [
            "zdfinfo",
            "zdf info",
        ],
    ),

    (
        "ZDFneo",
        [
            "zdfneo.de",
        ],
        [
            "zdfneo",
            "zdf neo",
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

    # --------------------------------------------------------
    # Private Priorität
    # --------------------------------------------------------

    (
        "kabel eins",
        [
            "kabeleins.de",
        ],
        [
            "kabel eins",
        ],
    ),

    (
        "ProSieben",
        [
            "prosieben.de",
        ],
        [
            "prosieben",
        ],
    ),

    (
        "RTL",
        [
            "rtl.de",
        ],
        [
            "rtl",
        ],
    ),

    (
        "sixx",
        [
            "sixx.de",
        ],
        [
            "sixx",
        ],
    ),

    (
        "Sat.1 Gold",
        [
            "sat1gold.de",
        ],
        [
            "sat 1 gold",
            "sat.1 gold",
        ],
    ),

    # --------------------------------------------------------
    # Öffentlich-rechtlich
    # --------------------------------------------------------

    (
        "ARD-alpha",
        [
            "ardalpha.de",
            "ard-alpha.de",
        ],
        [
            "ard alpha",
            "ard-alpha",
        ],
    ),

    (
        "Phoenix",
        [
            "phoenix.de",
        ],
        [
            "phoenix",
        ],
    ),

    (
        "ARTE",
        [
            "arte.de",
            "artedeutsch.de",
        ],
        [
            "arte",
        ],
    ),

    (
        "Tagesschau24",
        [
            "tagesschau24.de",
        ],
        [
            "tagesschau24",
            "tagesschau 24",
        ],
    ),

    # --------------------------------------------------------
    # Region / Dritte
    # --------------------------------------------------------

    (
        "MDR Fernsehen",
        [
            "mdrfernsehen.de@sachsen",
            "mdrfernsehen.de@sachsenanhalt",
            "mdrfernsehen.de@thuringen",
            "mdrfernsehen.de@thueringen",
            "mdrfernsehen.de",
        ],
        [
            "mdr fernsehen",
            "mdr sachsen",
            "mdr sachsen anhalt",
            "mdr thüringen",
            "mdr thueringen",
        ],
    ),

    (
        "NDR Hamburg",
        [
            "ndrfernsehen.de@hamburg",
        ],
        [
            "ndr hamburg",
        ],
    ),

    (
        "Noa 4 Hamburg",
        [
            "noa4hamburg.de",
        ],
        [
            "noa4 hamburg",
            "noa4 hh",
        ],
    ),

    (
        "Hamburg 1",
        [
            "hamburg1.de",
        ],
        [
            "hamburg 1",
            "hamburg1",
        ],
    ),

    (
        "Radio Weser TV Bremen",
        [
            "radiowesertvbremen.de",
        ],
        [
            "radio weser tv bremen",
            "radio weser tv",
        ],
    ),

    (
        "Radio Bremen Fernsehen",
        [
            "radiobremenfernsehen.de",
            "radiobrem enfernsehen.de",
            "radiobrem en tv.de",
        ],
        [
            "radio bremen fernsehen",
            "radio bremen tv",
        ],
    ),

    (
        "WDR Fernsehen",
        [
            "wdrfernsehen.de@koln",
            "wdrfernsehen.de@koeln",
            "wdr.de",
        ],
        [
            "wdr fernsehen",
        ],
    ),

    (
        "SWR Fernsehen Rheinland-Pfalz",
        [
            "swrfernsehenrheinlandpfalz.de",
        ],
        [
            "swr fernsehen rheinland pfalz",
        ],
    ),

    (
        "hr-fernsehen",
        [
            "hrfernsehen.de",
        ],
        [
            "hr fernsehen",
            "hr-fernsehen",
        ],
    ),

    (
        "SR Fernsehen",
        [
            "srfernsehen.de",
        ],
        [
            "sr fernsehen",
        ],
    ),

    (
        "rbb Fernsehen",
        [
            "rbbfernsehen.de",
        ],
        [
            "rbb fernsehen",
        ],
    ),

    (
        "Oberpfalz TV",
        [
            "oberpfalz tv.de",
            "oberpfalztv.de",
        ],
        [
            "oberpfalz tv",
            "oberpfalztv",
        ],
    ),

    (
        "BR Fernsehen Nord",
        [
            "brfernsehen.de@nord",
        ],
        [
            "br fernsehen nord",
        ],
    ),

    (
        "München TV",
        [
            "munchentv.de",
            "munchen tv.de",
        ],
        [
            "muenchen tv",
            "münchen tv",
            "münchen.tv",
        ],
    ),

    # --------------------------------------------------------
    # Nachrichten / Doku
    # --------------------------------------------------------

    (
        "Nachrichten 360",
        [
            "nachrichten360.de",
        ],
        [
            "nachrichten 360",
        ],
    ),

    (
        "SPIEGEL TV",
        [],
        [
            "spiegel tv",
        ],
    ),

    (
        "N24 Doku",
        [
            "n24doku.de",
        ],
        [
            "n24 doku",
            "n24doku",
        ],
    ),

    (
        "RT DE",
        [
            "rtde.de",
            "rtdeutsch.de",
        ],
        [
            "rt de",
            "rt deutsch",
        ],
    ),

    (
        "DokuSat",
        [],
        [
            "dokusat",
        ],
    ),

    (
        "Authentic History",
        [],
        [
            "authentic history",
        ],
    ),

    # --------------------------------------------------------
    # Religion
    # --------------------------------------------------------

    (
        "Bibel TV",
        [
            "bibeltv.de",
        ],
        [
            "bibel tv",
            "bibeltv",
        ],
    ),

    (
        "EWTN",
        [
            "ewtn.de",
        ],
        [
            "ewtn",
        ],
    ),

    (
        "K-TV",
        [
            "k-tv.de",
        ],
        [
            "k tv",
            "k-tv",
        ],
    ),

    # --------------------------------------------------------
    # Ende der persönlichen Reihenfolge
    # --------------------------------------------------------

    (
        "Terra Mater WILD",
        [
            "terramaterwild.de",
        ],
        [
            "terra mater wild",
        ],
    ),
]


# ============================================================
# WEITERE PRIVATE
#
# Diese kommen NACH RTL.
# ============================================================

PRIVATE_CHANNELS = [

    (
        "Sat.1",
        [
            "sat1.de",
        ],
        [
            "sat 1",
            "sat.1",
        ],
    ),

    (
        "VOX",
        [
            "vox.de",
        ],
        [
            "vox",
        ],
    ),

    (
        "RTL Zwei",
        [
            "rtlzwei.de",
        ],
        [
            "rtl zwei",
            "rtl2",
            "rtl ii",
        ],
    ),

    (
        "Super RTL",
        [
            "superrtl.de",
        ],
        [
            "super rtl",
        ],
    ),

    (
        "NITRO",
        [
            "nitro.de",
        ],
        [
            "nitro",
        ],
    ),

    (
        "VOXup",
        [
            "voxup.de",
        ],
        [
            "voxup",
            "vox up",
        ],
    ),

    (
        "ProSieben MAXX",
        [
            "prosiebenmaxx.de",
        ],
        [
            "prosieben maxx",
        ],
    ),

    (
        "kabel eins Doku",
        [
            "kabeleinsdoku.de",
        ],
        [
            "kabel eins doku",
            "kabel1 doku",
        ],
    ),

    (
        "TELE 5",
        [
            "tele5.de",
        ],
        [
            "tele 5",
            "tele5",
        ],
    ),

    (
        "DMAX",
        [
            "dmax.de",
        ],
        [
            "dmax",
        ],
    ),

]


# ============================================================
# AUSGESCHLOSSENE TVG-IDS
# ============================================================

EXCLUDE_IDS = {
    "oneadria.hr",
    "zeeone.de",
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

    "deluxe music",
    "music",
    "musik",
    "schlager",

]


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
        r"[^a-z0-9@]+",
        " ",
        value
    )

    return " ".join(
        value.split()
    )


# ============================================================
# TVG-ID NORMALISIERUNG
#
# NUR Qualitäts-Suffix entfernen.
#
# @Hamburg
# @Nord
# @Thuringen
#
# bleiben erhalten!
# ============================================================

def normalize_tvg_id(tvg_id):

    value = tvg_id.strip().lower()

    value = re.sub(
        r"@(hd|sd|fhd|uhd|4k)$",
        "",
        value
    )

    return value


# ============================================================
# ATTRIBUTE
# ============================================================

def get_attribute(
    info,
    attribute
):

    match = re.search(
        rf'{re.escape(attribute)}="([^"]*)"',
        info,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    return ""


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
                "Chrome/131 Safari/537.36"
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
# M3U PARSER
# ============================================================

def parse_m3u(
    text,
    source
):

    lines = text.splitlines()

    entries = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith(
            "#EXTINF:"
        ):

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

        entries.append(
            entry
        )

        i += 2

    return entries


# ============================================================
# AUSSCHLUSS
# ============================================================

def excluded(entry):

    tvg_id = normalize_tvg_id(
        entry["tvg_id"]
    )

    if tvg_id in EXCLUDE_IDS:

        return True

    combined = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    for word in EXCLUDE_NAME_WORDS:

        target = normalize(
            word
        )

        if target in combined:

            return True

    return False


# ============================================================
# GEO BLOCKED
#
# Wir verlassen uns hier auf die Kennzeichnung in der
# IPTV-org-M3U.
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
        or "geoblocked" in text
        or "geo-blocked" in text
    )


# ============================================================
# HD ERKENNUNG
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
        or "fhd" in words
        or "uhd" in words
        or "4k" in words
        or "1080p" in words
        or "1080i" in words
        or "720p" in words
    )


# ============================================================
# STREAM SCORE
# ============================================================

def stream_score(entry):

    geo = is_geo_blocked(
        entry
    )

    hd = is_hd(
        entry
    )

    if hd and not geo:

        return 0

    if not hd and not geo:

        return 1

    if hd and geo:

        return 2

    return 3


# ============================================================
# ID MATCH
#
# Qualitäts-Suffixe werden ignoriert.
# Region bleibt wichtig.
# ============================================================

def id_matches(
    entry,
    ids
):

    entry_id = normalize_tvg_id(
        entry["tvg_id"]
    )

    if not entry_id:

        return False

    for channel_id in ids:

        target = normalize_tvg_id(
            channel_id
        )

        if entry_id == target:

            return True

    return False


# ============================================================
# NAMENS-MATCH
#
# WICHTIG:
#
# Keine allgemeinen Teilstring-Matches für:
#
#   rtl
#   zdf
#   vox
#   arte
#   ndr
#   swr
#   sr
#
# Dadurch kann "Totally Turtles" niemals RTL werden.
# ============================================================

def name_matches(
    entry,
    names
):

    entry_name = normalize(
        entry["name"]
    )

    tvg_name = normalize(
        entry["tvg_name"]
    )

    values = {
        value
        for value in (
            entry_name,
            tvg_name
        )
        if value
    }

    # --------------------------------------------------------
    # Exakte Namen
    # --------------------------------------------------------

    for candidate in names:

        target = normalize(
            candidate
        )

        if not target:

            continue

        if target in values:

            return True

    # --------------------------------------------------------
    # Sichere längere Namen
    # --------------------------------------------------------

    safe_partial = {

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

        "noa4 hamburg",

    }

    for candidate in names:

        target = normalize(
            candidate
        )

        if target not in safe_partial:

            continue

        for value in values:

            if target in value:

                return True

    return False


# ============================================================
# MATCH
#
# ID immer zuerst.
# Name nur als kontrollierter Fallback.
# ============================================================

def matches_definition(
    entry,
    definition
):

    display_name, ids, names = (
        definition
    )

    # ID
    if id_matches(
        entry,
        ids
    ):

        return True

    # Name
    if name_matches(
        entry,
        names
    ):

        return True

    return False


# ============================================================
# ALLE MATCHES
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


# ============================================================
# BESTER STREAM
# ============================================================

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
# FIXED CHANNELS
#
# Genau EIN Stream pro Fixed-Sender.
# ============================================================

def build_fixed(
    entries
):

    result = []

    used_ids = set()

    for definition in FIXED_CHANNELS:

        display_name = (
            definition[0]
        )

        matches = find_matches(
            entries,
            definition
        )

        if not matches:

            continue

        matches.sort(
            key=stream_score
        )

        selected = None

        for entry in matches:

            base_id = normalize_tvg_id(
                entry["tvg_id"]
            )

            if not base_id:

                continue

            if base_id in used_ids:

                continue

            selected = entry

            break

        if selected is None:

            continue

        base_id = normalize_tvg_id(
            selected["tvg_id"]
        )

        selected["category"] = (
            "00 Priorität"
        )

        selected["priority"] = (
            len(result)
        )

        selected["display_name"] = (
            display_name
        )

        result.append(
            selected
        )

        used_ids.add(
            base_id
        )

    return (
        result,
        used_ids
    )


# ============================================================
# WEITERE PRIVATE
# ============================================================

def build_private(
    entries,
    used_ids
):

    result = []

    already_used = set(
        used_ids
    )

    for definition in PRIVATE_CHANNELS:

        matches = find_matches(
            entries,
            definition
        )

        if not matches:

            continue

        matches.sort(
            key=stream_score
        )

        selected = None

        for entry in matches:

            base_id = normalize_tvg_id(
                entry["tvg_id"]
            )

            if not base_id:

                continue

            if base_id in already_used:

                continue

            selected = entry

            break

        if selected is None:

            continue

        base_id = normalize_tvg_id(
            selected["tvg_id"]
        )

        selected["category"] = (
            "01 Weitere Private"
        )

        selected["display_name"] = (
            definition[0]
        )

        result.append(
            selected
        )

        already_used.add(
            base_id
        )

    return (
        result,
        already_used
    )


# ============================================================
# KATEGORIE
# ============================================================

def get_category(entry):

    text = normalize(
        entry["name"]
        + " "
        + entry["tvg_name"]
    )

    # --------------------------------------------------------
    # Rakuten IMMER ganz hinten
    # --------------------------------------------------------

    if "rakuten tv" in text:

        return "09 Rakuten TV"

    # --------------------------------------------------------
    # Regional
    # --------------------------------------------------------

    regional_words = [

        "ndr hamburg",

        "noa4",
        "hamburg 1",
        "hamburg1",

        "radio weser",
        "weser tv",

        "radio bremen",

        "oberpfalz tv",
        "oberpfalztv",

        "muenchen tv",
        "munchen tv",

        "br fernsehen nord",

        "swr fernsehen rheinland pfalz",

    ]

    if any(
        word in text
        for word in regional_words
    ):

        return "02 Regional"

    # --------------------------------------------------------
    # Dritte Programme
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
        word in text
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
        "rt de",
        "rt deutsch",

    ]

    if any(
        word in text
        for word in news_words
    ):

        return "04 Nachrichten"

    # --------------------------------------------------------
    # Doku
    # --------------------------------------------------------

    documentary_words = [

        "doku",
        "dokumentation",
        "history",
        "wissen",
        "science",
        "spiegel tv",
        "authentic history",

    ]

    if any(
        word in text
        for word in documentary_words
    ):

        return "05 Dokumentation & Wissen"

    # --------------------------------------------------------
    # Kinder
    # --------------------------------------------------------

    children_words = [

        "kika",
        "kinder",
        "kids",
        "junior",

    ]

    if any(
        word in text
        for word in children_words
    ):

        return "06 Kinder"

    # --------------------------------------------------------
    # Religion
    # --------------------------------------------------------

    religion_words = [

        "bibel tv",
        "bibeltv",
        "ewtn",
        "k tv",
        "erf",

    ]

    if any(
        word in text
        for word in religion_words
    ):

        return "07 Religion"

    # --------------------------------------------------------
    # Sport
    # --------------------------------------------------------

    if "sport" in text:

        return "08 Sport"

    # --------------------------------------------------------
    # Rest
    # --------------------------------------------------------

    return "10 Weitere deutsche Sender"


# ============================================================
# DEDUPLIZIERUNG
#
# @HD / @SD werden zusammengefasst.
#
# Regionale IDs bleiben getrennt.
#
# Beispiel:
#
#   hrfernsehen.de@SD
#   hrfernsehen.de@HD
#
# = ein Sender
#
# Aber:
#
#   NDRFernsehen.de@Hamburg
#   NDRFernsehen.de@SchleswigHolstein
#
# = zwei verschiedene Sender.
# ============================================================

def deduplicate(
    entries
):

    result = OrderedDict()

    for entry in entries:

        tvg_id = normalize_tvg_id(
            entry["tvg_id"]
        )

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
# REST SORTIERUNG
# ============================================================

def sort_rest(
    entries
):

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
# M3U INFO BEREINIGEN
# ============================================================

def clean_info(
    entry,
    category
):

    info = entry["info"]

    # group-title ersetzen

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

    # tatsächlichen Namen behalten

    return (
        f'{info} '
        f'group-title="{category}",'
        f'{entry["name"]}'
    )


# ============================================================
# M3U ERSTELLEN
# ============================================================

def build_m3u(
    entries
):

    output = [

        "#EXTM3U",

        "",

        "# ==================================================",
        "# GER TV - Deutsche TV-Liste",
        "# Automatisch aktualisiert",
        "# Quelle: IPTV-org",
        "#",
        "# Persönliche Senderpriorität",
        "# HD bevorzugt",
        "# Nicht Geo-blocked bevorzugt",
        "# Geo-blocked bleibt erhalten",
        "# Rakuten TV am Ende",
        "# ==================================================",

        "",

    ]

    current_category = None

    for entry in entries:

        category = entry[
            "category"
        ]

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

def safe_write(
    content
):

    # --------------------------------------------------------
    # Temporäre Datei
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
    # Datei überprüfen
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

    # --------------------------------------------------------
    # Sicherheitsprüfung
    # --------------------------------------------------------

    if extinf_count < 20:

        try:
            os.remove(
                TEMP_OUTPUT
            )
        except OSError:
            pass

        raise RuntimeError(
            "Zu wenige Sender in der neuen M3U: "
            f"{extinf_count}"
        )

    if url_count < 20:

        try:
            os.remove(
                TEMP_OUTPUT
            )
        except OSError:
            pass

        raise RuntimeError(
            "Zu wenige URLs in der neuen M3U: "
            f"{url_count}"
        )

    # --------------------------------------------------------
    # Backup
    # --------------------------------------------------------

    if os.path.exists(
        OUTPUT
    ):

        shutil.copy2(
            OUTPUT,
            BACKUP_OUTPUT
        )

    # --------------------------------------------------------
    # Erst jetzt ersetzen
    # --------------------------------------------------------

    os.replace(
        TEMP_OUTPUT,
        OUTPUT
    )


# ============================================================
# HAUPTPROGRAMM
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
                    "Keine M3U-Einträge gefunden."
                )

            print(
                f"  OK: {len(entries)} Einträge"
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
    # Sicherheitsprüfung Quellen
    # --------------------------------------------------------

    print()

    print(
        "Erfolgreiche Quellen:",
        successful_sources,
        "/",
        len(SOURCES)
    )

    print(
        "Insgesamt geladen:",
        len(all_entries)
    )

    if successful_sources == 0:

        raise RuntimeError(
            "Keine Quelle konnte geladen werden."
        )

    if len(all_entries) < 50:

        raise RuntimeError(
            "Ungewöhnlich wenige Einträge geladen: "
            f"{len(all_entries)}"
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
    # Fixed
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

        if normalize_tvg_id(
            entry["tvg_id"]
        ) not in used_ids

    ]

    rest = sort_rest(
        rest
    )

    # --------------------------------------------------------
    # Endgültige Liste
    # --------------------------------------------------------

    entries = (

        fixed
        + private
        + rest

    )

    # --------------------------------------------------------
    # Sicherheitsprüfung
    # --------------------------------------------------------

    if len(entries) < 20:

        raise RuntimeError(
            "Nach Verarbeitung zu wenige Sender: "
            f"{len(entries)}"
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

    # ========================================================
    # AUSGABE
    # ========================================================

    print()

    print(
        "=========================================="
    )

    print(
        "FIXED / PRIORITÄT"
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
            f"{entry['display_name']} "
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
            f"{entry['display_name']} "
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
        "Priorität:",
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

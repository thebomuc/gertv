import re
import os
import shutil
import urllib.request
from collections import OrderedDict


# ============================================================
# GER TV - update.py
# ============================================================
#
# Erstellt:
#
#     deutsch.m3u
#
# MEHRERE QUELLEN
# ----------------
# Alle Quellen werden geladen und zusammengeführt.
#
# FIXED / PRIORITÄT
# -----------------
# Die persönliche Reihenfolge bleibt exakt erhalten.
#
# REGIONAL-FALLBACK
# -----------------
# Beispiel:
#
#   NDR Niedersachsen
#       ↓ falls nicht gefunden
#   NDR Hamburg
#
# STREAM-PRIORITÄT
# ----------------
#   1. HD + nicht Geo-blocked
#   2. SD + nicht Geo-blocked
#   3. HD + Geo-blocked
#   4. SD + Geo-blocked
#
# RAKUTEN
# -------
# Die fünf gewünschten Rakuten-TV-Sender stehen am Ende
# der persönlichen Prioritätsliste.
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

    (
        "German TV M3U",
        "https://raw.githubusercontent.com/josxha/german-tv-m3u/main/german-tv.m3u"
    ),
]


# ============================================================
# FESTE PRIORITÄT
#
# Reihenfolge exakt nach Wunsch.
#
# Jeder Sender kann mehrere IDs/Namen besitzen.
#
# Die Liste arbeitet mit Prioritätsgruppen:
#
#   "variants": [
#       [erste Variante],
#       [Fallback-Variante],
#       [weiterer Fallback]
#   ]
#
# Die ERSTE gefundene Variante gewinnt.
# Innerhalb derselben Variante entscheidet stream_score().
# ============================================================

FIXED_CHANNELS = [

    (
        "Das Erste",
        [
            {
                "ids": ["daserste.de"],
                "names": ["das erste"],
            }
        ],
    ),

    (
        "ZDF",
        [
            {
                "ids": ["zdf.de"],
                "names": ["zdf"],
            }
        ],
    ),

    (
        "ZDFinfo",
        [
            {
                "ids": ["zdfinfo.de"],
                "names": ["zdfinfo", "zdf info"],
            }
        ],
    ),

    (
        "ZDFneo",
        [
            {
                "ids": ["zdfneo.de"],
                "names": ["zdfneo", "zdf neo"],
            }
        ],
    ),

    (
        "3sat",
        [
            {
                "ids": ["3sat.de"],
                "names": ["3sat"],
            }
        ],
    ),

    (
        "kabel eins",
        [
            {
                "ids": ["kabeleins.de"],
                "names": ["kabel eins"],
            }
        ],
    ),

    (
        "ProSieben",
        [
            {
                "ids": ["prosieben.de"],
                "names": ["prosieben"],
            }
        ],
    ),

    (
        "RTL",
        [
            {
                "ids": ["rtl.de"],
                "names": ["rtl"],
            }
        ],
    ),

    (
        "Sat.1",
        [
            {
                "ids": ["sat1.de"],
                "names": ["sat 1", "sat.1"],
            }
        ],
    ),

    (
        "VOX",
        [
            {
                "ids": ["vox.de"],
                "names": ["vox"],
            }
        ],
    ),

    (
        "RTL Zwei",
        [
            {
                "ids": ["rtlzwei.de"],
                "names": ["rtl zwei", "rtl2", "rtl ii"],
            }
        ],
    ),

    (
        "Super RTL",
        [
            {
                "ids": ["superrtl.de"],
                "names": ["super rtl"],
            }
        ],
    ),

    (
        "NITRO",
        [
            {
                "ids": ["nitro.de"],
                "names": ["nitro"],
            }
        ],
    ),

    (
        "VOXup",
        [
            {
                "ids": ["voxup.de"],
                "names": ["voxup", "vox up"],
            }
        ],
    ),

    (
        "ProSieben MAXX",
        [
            {
                "ids": ["prosiebenmaxx.de"],
                "names": ["prosieben maxx"],
            }
        ],
    ),

    (
        "kabel eins Doku",
        [
            {
                "ids": ["kabeleinsdoku.de"],
                "names": [
                    "kabel eins doku",
                    "kabel1 doku",
                ],
            }
        ],
    ),

    (
        "TELE 5",
        [
            {
                "ids": ["tele5.de"],
                "names": ["tele 5", "tele5"],
            }
        ],
    ),

    (
        "DMAX",
        [
            {
                "ids": ["dmax.de"],
                "names": ["dmax"],
            }
        ],
    ),

    (
        "sixx",
        [
            {
                "ids": ["sixx.de"],
                "names": ["sixx"],
            }
        ],
    ),

    (
        "Sat.1 Gold",
        [
            {
                "ids": ["sat1gold.de", "sat1gold.de"],
                "names": [
                    "sat 1 gold",
                    "sat.1 gold",
                ],
            }
        ],
    ),

    (
        "ARD-alpha",
        [
            {
                "ids": [
                    "ardalpha.de",
                    "ard-alpha.de",
                ],
                "names": [
                    "ard alpha",
                    "ard-alpha",
                ],
            }
        ],
    ),

    (
        "Phoenix",
        [
            {
                "ids": ["phoenix.de"],
                "names": ["phoenix"],
            }
        ],
    ),

    (
        "ARTE",
        [
            {
                "ids": [
                    "arte.de",
                    "artedeutsch.de",
                ],
                "names": ["arte"],
            }
        ],
    ),

    (
        "Tagesschau24",
        [
            {
                "ids": ["tagesschau24.de"],
                "names": [
                    "tagesschau24",
                    "tagesschau 24",
                ],
            }
        ],
    ),

    (
        "MDR Fernsehen",
        [
            {
                "ids": [
                    "mdrfernsehen.de@sachsen",
                    "mdrfernsehen.de@sachsenanhalt",
                    "mdrfernsehen.de@thuringen",
                    "mdrfernsehen.de@thueringen",
                ],
                "names": [
                    "mdr sachsen",
                    "mdr sachsen anhalt",
                    "mdr thüringen",
                    "mdr thueringen",
                ],
            },
            {
                "ids": ["mdrfernsehen.de"],
                "names": ["mdr fernsehen"],
            },
        ],
    ),

    # ========================================================
    # NDR:
    #
    # 1. NDR Niedersachsen
    # 2. NDR Hamburg als Fallback
    # 3. allgemeiner NDR als letzter Fallback
    # ========================================================

    (
        "NDR Niedersachsen",
        [
            {
                "ids": [
                    "ndrfernsehen.de@niedersachsen",
                ],
                "names": [
                    "ndr niedersachsen",
                    "ndr niedersachsen hd",
                ],
            },
            {
                "ids": [
                    "ndrfernsehen.de@hamburg",
                ],
                "names": [
                    "ndr hamburg",
                ],
            },
            {
                "ids": ["ndrfernsehen.de"],
                "names": [
                    "ndr fernsehen",
                    "ndr",
                ],
            },
        ],
    ),

    (
        "Noa 4 Hamburg",
        [
            {
                "ids": ["noa4hamburg.de"],
                "names": [
                    "noa4 hamburg",
                    "noa4 hh",
                ],
            }
        ],
    ),

    (
        "Hamburg 1",
        [
            {
                "ids": ["hamburg1.de"],
                "names": [
                    "hamburg 1",
                    "hamburg1",
                ],
            }
        ],
    ),

    (
        "Radio Weser TV Bremen",
        [
            {
                "ids": ["radiowesertvbremen.de"],
                "names": [
                    "radio weser tv bremen",
                    "radio weser tv",
                ],
            }
        ],
    ),

    (
        "Radio Bremen Fernsehen",
        [
            {
                "ids": ["radiobremenfernsehen.de"],
                "names": [
                    "radio bremen fernsehen",
                    "radio bremen tv",
                ],
            }
        ],
    ),

    (
        "WDR Fernsehen",
        [
            {
                "ids": [
                    "wdrfernsehen.de@koln",
                    "wdrfernsehen.de@koeln",
                    "wdr.de",
                ],
                "names": ["wdr fernsehen"],
            }
        ],
    ),

    (
        "SWR Fernsehen Rheinland-Pfalz",
        [
            {
                "ids": ["swrfernsehenrheinlandpfalz.de"],
                "names": [
                    "swr fernsehen rheinland pfalz",
                ],
            }
        ],
    ),

    (
        "hr-fernsehen",
        [
            {
                "ids": ["hrfernsehen.de"],
                "names": [
                    "hr fernsehen",
                    "hr-fernsehen",
                ],
            }
        ],
    ),

    (
        "SR Fernsehen",
        [
            {
                "ids": ["srfernsehen.de"],
                "names": ["sr fernsehen"],
            }
        ],
    ),

    (
        "rbb Fernsehen",
        [
            {
                "ids": ["rbbfernsehen.de"],
                "names": ["rbb fernsehen"],
            }
        ],
    ),

    (
        "Oberpfalz TV",
        [
            {
                "ids": [
                    "oberpfalztv.de",
                    "oberpfalz tv.de",
                ],
                "names": [
                    "oberpfalz tv",
                    "oberpfalztv",
                ],
            }
        ],
    ),

    (
        "BR Fernsehen Nord",
        [
            {
                "ids": ["brfernsehen.de@nord"],
                "names": ["br fernsehen nord"],
            }
        ],
    ),

    (
        "München TV",
        [
            {
                "ids": [
                    "munchentv.de",
                    "munchen tv.de",
                ],
                "names": [
                    "muenchen tv",
                    "münchen tv",
                    "münchen.tv",
                ],
            }
        ],
    ),

    (
        "Nachrichten 360",
        [
            {
                "ids": ["nachrichten360.de"],
                "names": ["nachrichten 360"],
            }
        ],
    ),

    (
        "SPIEGEL TV",
        [
            {
                "ids": [],
                "names": ["spiegel tv"],
            }
        ],
    ),

    (
        "N24 Doku",
        [
            {
                "ids": ["n24doku.de"],
                "names": [
                    "n24 doku",
                    "n24doku",
                ],
            }
        ],
    ),

    (
        "WELT",
        [
            {
                "ids": ["welt.de"],
                "names": ["welt"],
            }
        ],
    ),

    (
        "RT DE",
        [
            {
                "ids": [
                    "rtde.de",
                    "rtdeutsch.de",
                ],
                "names": [
                    "rt de",
                    "rt deutsch",
                ],
            }
        ],
    ),

    (
        "DokuSat",
        [
            {
                "ids": [],
                "names": ["dokusat"],
            }
        ],
    ),

    (
        "Authentic History",
        [
            {
                "ids": [],
                "names": ["authentic history"],
            }
        ],
    ),

    (
        "Bibel TV",
        [
            {
                "ids": ["bibeltv.de"],
                "names": [
                    "bibel tv",
                    "bibeltv",
                ],
            }
        ],
    ),

    (
        "EWTN",
        [
            {
                "ids": ["ewtn.de"],
                "names": ["ewtn"],
            }
        ],
    ),

    (
        "K-TV",
        [
            {
                "ids": ["k-tv.de", "ktv.de"],
                "names": [
                    "k tv",
                    "k-tv",
                ],
            }
        ],
    ),

    (
        "Terra Mater WILD",
        [
            {
                "ids": ["terramaterwild.de"],
                "names": ["terra mater wild"],
            }
        ],
    ),

    (
        "Welt der Wunder",
        [
            {
                "ids": ["weltderwunder.de"],
                "names": ["welt der wunder"],
            }
        ],
    ),

    # ========================================================
    # RAKUTEN TV
    #
    # Fest am Ende der Fixed-Reihenfolge.
    # ========================================================

    (
        "Rakuten TV Action Movies Germany",
        [
            {
                "ids": ["rakutentvactionmovies.es@germany"],
                "names": [
                    "rakuten tv action movies germany",
                ],
            }
        ],
    ),

    (
        "Rakuten TV Comedy Movies Germany",
        [
            {
                "ids": ["rakutentvcomedymovies.es@germany"],
                "names": [
                    "rakuten tv comedy movies germany",
                ],
            }
        ],
    ),

    (
        "Rakuten TV Drama Movies Germany",
        [
            {
                "ids": ["rakutentvdramamovies.es@germany"],
                "names": [
                    "rakuten tv drama movies germany",
                ],
            }
        ],
    ),

    (
        "Rakuten TV Family Movies Germany",
        [
            {
                "ids": ["rakutentvfamilymovies.es@germany"],
                "names": [
                    "rakuten tv family movies germany",
                ],
            }
        ],
    ),

    (
        "Rakuten TV Top Movies Germany",
        [
            {
                "ids": ["rakutentvtopmovies.es@germany"],
                "names": [
                    "rakuten tv top movies germany",
                ],
            }
        ],
    ),
]


# ============================================================
# AUSSCHLÜSSE
# ============================================================

EXCLUDE_IDS = {
    "oneadria.hr",
    "zeeone.de",
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
        value = value.replace(old, new)

    value = re.sub(
        r"[^a-z0-9@]+",
        " ",
        value
    )

    return " ".join(value.split())


# ============================================================
# TVG-ID NORMALISIERUNG
#
# Nur Qualitäts-Suffix entfernen.
#
# @HD / @SD / @FHD / @UHD / @4K
#
# Regionale Kennzeichnungen bleiben erhalten.
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
        raise RuntimeError("Leere Antwort")

    return data.decode(
        "utf-8",
        errors="replace"
    )


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
        or "geoblocked" in text
        or "geo blocked" in text
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

    words = set(text.split())

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

    geo = is_geo_blocked(entry)
    hd = is_hd(entry)

    if hd and not geo:
        return 0

    if not hd and not geo:
        return 1

    if hd and geo:
        return 2

    return 3


# ============================================================
# ID MATCH
# ============================================================

def id_matches(entry, ids):

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
# NAME MATCH
#
# Sehr vorsichtig, damit z.B.
#
#   Totally Turtles
#
# niemals RTL wird.
# ============================================================

def name_matches(entry, names):

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
    # Exakter Name
    # --------------------------------------------------------

    for candidate in names:

        target = normalize(candidate)

        if target in values:
            return True

    # --------------------------------------------------------
    # Sichere längere Teilmatches
    # --------------------------------------------------------

    safe_partial = {

        "zdf info",
        "zdf neo",

        "sat 1 gold",

        "kabel eins doku",
        "kabel1 doku",

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

        "ndr niedersachsen",

        "ndr hamburg",

        "ndr fernsehen",

        "welt der wunder",

        "spiegel tv",

        "dokusat",

    }

    for candidate in names:

        target = normalize(candidate)

        if target not in safe_partial:
            continue

        for value in values:

            if target in value:
                return True

    return False


# ============================================================
# DEFINITION MATCH
# ============================================================

def matches_definition(
    entry,
    definition
):

    ids = definition.get("ids", [])
    names = definition.get("names", [])

    if id_matches(entry, ids):
        return True

    if name_matches(entry, names):
        return True

    return False


# ============================================================
# MATCHES EINER VARIANTE
# ============================================================

def find_variant_matches(
    entries,
    variant
):

    return [

        entry

        for entry in entries

        if matches_definition(
            entry,
            variant
        )

    ]


# ============================================================
# BESTE VARIANTE
#
# WICHTIG:
#
# Variante 1 hat Vorrang vor Variante 2.
#
# Beispiel:
#
# NDR Niedersachsen vorhanden:
#     -> Niedersachsen
#
# nicht:
#     -> Hamburg
#
# Nur wenn Niedersachsen NICHT gefunden wird:
#     -> Hamburg
# ============================================================

def find_best_variant(
    entries,
    variants
):

    for variant_number, variant in enumerate(
        variants,
        start=1
    ):

        matches = find_variant_matches(
            entries,
            variant
        )

        if not matches:
            continue

        matches.sort(
            key=stream_score
        )

        return (
            matches[0],
            variant_number
        )

    return (
        None,
        None
    )


# ============================================================
# FIXED AUFBAU
# ============================================================

def build_fixed(entries):

    result = []

    used_ids = set()

    missing = []

    for priority_number, definition in enumerate(
        FIXED_CHANNELS,
        start=1
    ):

        display_name = definition[0]
        variants = definition[1]

        selected = None
        selected_variant = None

        for variant_number, variant in enumerate(
            variants,
            start=1
        ):

            matches = find_variant_matches(
                entries,
                variant
            )

            # Bereits verwendete TVG-ID nicht doppelt
            matches = [

                entry

                for entry in matches

                if (
                    normalize_tvg_id(
                        entry["tvg_id"]
                    )
                    not in used_ids
                )

            ]

            if not matches:
                continue

            matches.sort(
                key=stream_score
            )

            selected = matches[0]
            selected_variant = variant_number

            break

        if selected is None:

            missing.append(
                display_name
            )

            continue

        base_id = normalize_tvg_id(
            selected["tvg_id"]
        )

        selected["category"] = "00 Priorität"
        selected["priority"] = priority_number
        selected["display_name"] = display_name
        selected["matched_variant"] = selected_variant

        result.append(selected)

        if base_id:
            used_ids.add(base_id)

    return (
        result,
        used_ids,
        missing
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

    if "rakuten tv" in text:
        return "09 Rakuten TV"

    regional_words = [

        "ndr niedersachsen",
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

    if "sport" in text:
        return "08 Sport"

    return "10 Weitere deutsche Sender"


# ============================================================
# REST DEDUP
# ============================================================

def deduplicate(entries):

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

    return list(result.values())


# ============================================================
# REST SORTIERUNG
# ============================================================

def sort_rest(entries):

    for entry in entries:

        entry["category"] = get_category(
            entry
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

    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

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
# M3U ERSTELLEN
# ============================================================

def build_m3u(entries):

    output = [

        "#EXTM3U",

        "",

        "# ==================================================",
        "# GER TV - Deutsche TV-Liste",
        "# Automatisch aktualisiert",
        "#",
        "# Mehrere Quellen",
        "# Persönliche Senderpriorität",
        "# Regionale Fallbacks",
        "# HD bevorzugt",
        "# Nicht Geo-blocked bevorzugt",
        "# Geo-blocked bleibt erhalten",
        "# Rakuten TV am Ende der Priorität",
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
# SICHER SCHREIBEN
# ============================================================

def safe_write(content):

    with open(
        TEMP_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

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
            line.startswith("http://")
            or line.startswith("https://")
        )

    )

    if extinf_count < 20:

        try:
            os.remove(TEMP_OUTPUT)
        except OSError:
            pass

        raise RuntimeError(
            "Zu wenige Sender in der neuen M3U: "
            f"{extinf_count}"
        )

    if url_count < 20:

        try:
            os.remove(TEMP_OUTPUT)
        except OSError:
            pass

        raise RuntimeError(
            "Zu wenige URLs in der neuen M3U: "
            f"{url_count}"
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

    # --------------------------------------------------------
    # QUELLEN
    # --------------------------------------------------------

    for source_name, url in SOURCES:

        try:

            print(
                f"Lade {source_name} ..."
            )

            text = download(url)

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

            all_entries.extend(entries)

            successful_sources += 1

        except Exception as error:

            print(
                f"  FEHLER: {error}"
            )

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
    # Fixed zuerst
    #
    # Noch NICHT global deduplizieren.
    #
    # So kann z.B. eine benötigte Variante gefunden werden,
    # bevor andere Quellen sie verdrängen.
    # --------------------------------------------------------

    fixed, used_ids, missing = build_fixed(
        filtered
    )

    # --------------------------------------------------------
    # ÜBRIGE EINTRÄGE
    # --------------------------------------------------------

    rest = [

        entry

        for entry in filtered

        if normalize_tvg_id(
            entry["tvg_id"]
        ) not in used_ids

    ]

    # --------------------------------------------------------
    # Rest deduplizieren
    # --------------------------------------------------------

    rest = deduplicate(rest)

    # --------------------------------------------------------
    # Rest sortieren
    # --------------------------------------------------------

    rest = sort_rest(rest)

    # --------------------------------------------------------
    # Rakuten aus dem Rest entfernen.
    #
    # Sie werden ausschließlich über die feste Rakuten-
    # Definition einsortiert.
    # --------------------------------------------------------

    fixed_ids = {

        normalize_tvg_id(
            entry["tvg_id"]
        )

        for entry in fixed

    }

    # Bereits Fixed-Rakuten sind korrekt positioniert.
    # Weitere Rakuten-Versionen sollen nicht vor ihnen landen.

    non_rakuten_rest = []
    rakuten_rest = []

    for entry in rest:

        text = normalize(
            entry["name"]
            + " "
            + entry["tvg_name"]
        )

        if "rakuten tv" in text:

            rakuten_rest.append(entry)

        else:

            non_rakuten_rest.append(entry)

    rest = (
        non_rakuten_rest
        + rakuten_rest
    )

    # --------------------------------------------------------
    # ENDGÜLTIGE LISTE
    # --------------------------------------------------------

    entries = fixed + rest

    if len(entries) < 20:

        raise RuntimeError(
            "Nach Verarbeitung zu wenige Sender: "
            f"{len(entries)}"
        )

    # --------------------------------------------------------
    # M3U
    # --------------------------------------------------------

    content = build_m3u(entries)

    safe_write(content)

    # ========================================================
    # AUSGABE
    # ========================================================

    print()
    print("==========================================")
    print("FIXED / PRIORITÄT")
    print("==========================================")

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

        fallback = ""

        if entry.get("matched_variant", 1) > 1:

            fallback = (
                f" FALLBACK#{entry['matched_variant']}"
            )

        print(

            f"{number:02d}. "
            f"{entry['display_name']} "
            f"[{hd}/{geo}]"
            f"{fallback} "
            f"[{entry['tvg_id']}]"

        )

    # --------------------------------------------------------
    # Fehlende Fixed-Sender
    # --------------------------------------------------------

    if missing:

        print()
        print("==========================================")
        print("NICHT GEFUNDENE PRIORITÄTS-SENDER")
        print("==========================================")

        for name in missing:

            print(
                f"- {name}"
            )

    print()
    print("==========================================")
    print("ERGEBNIS")
    print("==========================================")

    print(
        "Gesamt:",
        len(entries)
    )

    print(
        "Priorität:",
        len(fixed)
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
        print("==========================================")
        print("UPDATE FEHLGESCHLAGEN")
        print("==========================================")
        print(error)
        print()
        print(
            "Die vorhandene deutsch.m3u "
            "wurde NICHT überschrieben."
        )

        if os.path.exists(TEMP_OUTPUT):

            try:
                os.remove(TEMP_OUTPUT)
            except OSError:
                pass

        raise SystemExit(1)

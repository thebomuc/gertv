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
# ============================================================
#
# FESTE PRIORITÄT
#
# 01  Das Erste
# 02  ZDF
# 03  ZDFinfo
# 04  ZDFneo
# 05  3sat
# 06  kabel eins
# 07  ProSieben
# 08  RTL
# 09  Sat.1
# 10  VOX
# 11  RTL Zwei
# 12  Super RTL
# 13  NITRO
# 14  VOXup
# 15  ProSieben MAXX
# 16  kabel eins Doku
# 17  TELE 5
# 18  DMAX
# 19  sixx
# 20  Sat.1 Gold
# 21  ARD-alpha
# 22  Phoenix
# 23  ARTE
# 24  Tagesschau24
# 25  MDR Fernsehen
# 26  NDR Niedersachsen
# 27  Noa 4 Hamburg
# 28  Hamburg 1
# 29  Radio Weser TV Bremen
# 30  Radio Bremen Fernsehen
# 31  WDR Fernsehen
# 32  SWR Fernsehen Rheinland-Pfalz
# 33  hr-fernsehen
# 34  SR Fernsehen
# 35  rbb Fernsehen
# 36  Oberpfalz TV
# 37  BR Fernsehen Nord
# 38  München TV
# 39  Nachrichten 360
# 40  SPIEGEL TV
# 41  N24 Doku
# 42  WELT
# 43  RT DE
# 44  DokuSat
# 45  Authentic History
# 46  Bibel TV
# 47  EWTN
# 48  K-TV
# 49  Terra Mater WILD
# 50  Welt der Wunder
# 51  Rakuten TV Action Movies Germany
# 52  Rakuten TV Comedy Movies Germany
# 53  Rakuten TV Drama Movies Germany
# 54  Rakuten TV Family Movies Germany
# 55  Rakuten TV Top Movies Germany
#
# Danach:
#
#   weitere deutsche Sender
#
# ============================================================
#
# STREAM-PRIORITÄT
#
#   1. HD + nicht Geo-blocked
#   2. SD + nicht Geo-blocked
#   3. HD + Geo-blocked
#   4. SD + Geo-blocked
#
# ============================================================
#
# WICHTIG
#
# - Geo-blocked wird NICHT automatisch entfernt.
# - Gibt es nur Geo-blocked, bleibt dieser Stream erhalten.
# - @HD / @SD werden als Qualitätsvarianten behandelt.
# - Regionale Varianten bleiben getrennt.
# - RTL wird nur über exakte ID oder exakten Namen erkannt.
# - "Totally Turtles" kann NICHT als RTL erkannt werden.
# - Rakuten TV steht immer ganz am Ende der Prioritätsliste.
# - Bei Fehlern wird deutsch.m3u NICHT überschrieben.
# - Vor dem Überschreiben wird ein Backup erstellt.
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
        "IPTV-org Deutschland",
        "https://iptv-org.github.io/iptv/countries/de.m3u"
    ),

    (
        "IPTV-org Bayern",
        "https://iptv-org.github.io/iptv/subdivisions/de-by.m3u"
    ),

    (
        "IPTV-org Berlin",
        "https://iptv-org.github.io/iptv/subdivisions/de-be.m3u"
    ),

    (
        "IPTV-org Brandenburg",
        "https://iptv-org.github.io/iptv/subdivisions/de-bb.m3u"
    ),

    (
        "IPTV-org Hamburg",
        "https://iptv-org.github.io/iptv/subdivisions/de-hh.m3u"
    ),

    (
        "IPTV-org Mecklenburg-Vorpommern",
        "https://iptv-org.github.io/iptv/subdivisions/de-mv.m3u"
    ),

    (
        "IPTV-org Niedersachsen",
        "https://iptv-org.github.io/iptv/subdivisions/de-ni.m3u"
    ),

    (
        "IPTV-org Schleswig-Holstein",
        "https://iptv-org.github.io/iptv/subdivisions/de-sh.m3u"
    ),

    # --------------------------------------------------------
    # Zusätzliche deutsche Free-TV-Quelle
    # --------------------------------------------------------

    (
        "German TV M3U",
        "https://raw.githubusercontent.com/josxha/german-tv-m3u/main/german-tv.m3u"
    ),
]


# ============================================================
# FESTE PRIORITÄT
# ============================================================

FIXED_CHANNELS = [

    # --------------------------------------------------------
    # 01-05 Hauptsender
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
    # 06-20 Private
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
    # 21-24 Öffentlich-rechtlich
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
    # 25-38 Regional / Dritte
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
        "NDR Niedersachsen",
        [
            "ndrfernsehen.de@niedersachsen",
        ],
        [
            "ndr niedersachsen",
            "ndr fernsehen niedersachsen",
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
            "noa 4 hamburg",
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
            "muenchentv.de",
        ],
        [
            "muenchen tv",
            "munchen tv",
            "münchen tv",
            "münchen.tv",
        ],
    ),

    # --------------------------------------------------------
    # 39-45 Nachrichten / Doku
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
        "WELT",
        [
            "welt.de",
        ],
        [
            "welt",
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
    # 46-50 Religion / Wissen
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
            "ktv.de",
        ],
        [
            "k tv",
            "k-tv",
            "k tv kirche",
        ],
    ),

    (
        "Terra Mater WILD",
        [
            "terramaterwild.de",
        ],
        [
            "terra mater wild",
        ],
    ),

    (
        "Welt der Wunder",
        [
            "weltderwunder.de",
        ],
        [
            "welt der wunder",
        ],
    ),

    # --------------------------------------------------------
    # 51-55 Rakuten TV
    #
    # Werden ebenfalls fest priorisiert und stehen nach
    # Welt der Wunder.
    # --------------------------------------------------------

    (
        "Rakuten TV Action Movies Germany",
        [
            "rakutentvactionmovies.es@germany",
        ],
        [
            "rakuten tv action movies germany",
        ],
    ),

    (
        "Rakuten TV Comedy Movies Germany",
        [
            "rakutentvcomedymovies.es@germany",
        ],
        [
            "rakuten tv comedy movies germany",
        ],
    ),

    (
        "Rakuten TV Drama Movies Germany",
        [
            "rakutentvdramamovies.es@germany",
        ],
        [
            "rakuten tv drama movies germany",
        ],
    ),

    (
        "Rakuten TV Family Movies Germany",
        [
            "rakutentvfamilymovies.es@germany",
        ],
        [
            "rakuten tv family movies germany",
        ],
    ),

    (
        "Rakuten TV Top Movies Germany",
        [
            "rakutentvtopmovies.es@germany",
        ],
        [
            "rakuten tv top movies germany",
        ],
    ),
]


# ============================================================
# HARTE RAKUTEN FALLBACKS
#
# Wenn eine der Rakuten-Quellen den Sender nicht liefert,
# wird der bekannte Stream verwendet.
#
# Dadurch bleiben die fünf gewünschten Rakuten-Sender
# zuverlässig in der Liste.
# ============================================================

RAKUTEN_FALLBACKS = {

    "Rakuten TV Action Movies Germany": (
        'RakutenTVActionMovies.es@Germany',
        'https://i.imgur.com/Meew6eX.png',
        'Rakuten TV Action Movies Germany (1080p)',
        'https://284824cf70404fdfb6ddf9349009c710.mediatailor.eu-west-1.amazonaws.com/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6066/master.m3u8'
    ),

    "Rakuten TV Comedy Movies Germany": (
        'RakutenTVComedyMovies.es@Germany',
        'https://i.imgur.com/Meew6eX.png',
        'Rakuten TV Comedy Movies Germany (1080p)',
        'https://ecac08c9e2214375b907d6825aaf9a01.mediatailor.eu-west-1.amazonaws.com/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6182/master.m3u8'
    ),

    "Rakuten TV Drama Movies Germany": (
        'RakutenTVDramaMovies.es@Germany',
        'https://i.imgur.com/Meew6eX.png',
        'Rakuten TV Drama Movies Germany (1080p)',
        'https://968754c2483045c1a9a7f677caec35b6.mediatailor.eu-west-1.amazonaws.com/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6096/master.m3u8'
    ),

    "Rakuten TV Family Movies Germany": (
        'RakutenTVFamilyMovies.es@Germany',
        'https://i.imgur.com/Meew6eX.png',
        'Rakuten TV Family Movies Germany (1080p)',
        'https://af230031eeac45f3b78d4f8a13265105.mediatailor.eu-west-1.amazonaws.com/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6209/master.m3u8'
    ),

    "Rakuten TV Top Movies Germany": (
        'RakutenTVTopMovies.es@Germany',
        'https://i.imgur.com/Meew6eX.png',
        'Rakuten TV Top Movies Germany (1080p)',
        'https://cbb622b29f5d43b598991f3fa19de291.mediatailor.eu-west-1.amazonaws.com/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-5985/master.m3u8'
    ),
}


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
# @Niedersachsen
# @Nord
# @Thuringen
#
# bleiben erhalten.
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
# FALLBACK-ENTRY
# ============================================================

def create_fallback_entry(
    display_name
):

    data = RAKUTEN_FALLBACKS.get(
        display_name
    )

    if not data:

        return None

    tvg_id, logo, name, url = data

    return {

        "info": (
            f'#EXTINF:-1 tvg-id="{tvg_id}" '
            f'tvg-logo="{logo}" '
            f'group-title="09 Rakuten TV",'
            f'{name}'
        ),

        "name": name,

        "tvg_id": tvg_id,

        "tvg_name": name,

        "language": "German",

        "country": "Germany",

        "group": "09 Rakuten TV",

        "source": "Rakuten Fallback",

        "url": url,

    }


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
# ============================================================

def is_geo_blocked(entry):

    text = (
        entry["info"]
        + " "
        + entry["name"]
        + " "
        + entry["tvg_name"]
    ).lower()

    return (
        "geo-blocked" in text
        or "geo blocked" in text
        or "geoblocked" in text
        or "[blocked]" in text
        or "blocked" in text
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
# NAME MATCH
#
# ABSICHTLICH KEINE allgemeinen Teilstrings.
#
# Dadurch:
#
#   RTL
#
# matcht NICHT:
#
#   Totally Turtles
#
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

    for candidate in names:

        target = normalize(
            candidate
        )

        if not target:

            continue

        if target in values:

            return True

    return False


# ============================================================
# MATCH
# ============================================================

def matches_definition(
    entry,
    definition
):

    display_name, ids, names = definition

    if id_matches(
        entry,
        ids
    ):

        return True

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
# DEDUP
#
# @HD / @SD werden zusammengefasst.
# Regionale Varianten bleiben getrennt.
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
# FIXED AUFBAUEN
# ============================================================

def build_fixed(
    entries
):

    result = []

    used_ids = set()

    found_names = set()

    for definition in FIXED_CHANNELS:

        display_name = definition[0]

        matches = find_matches(
            entries,
            definition
        )

        matches.sort(
            key=stream_score
        )

        selected = None

        for entry in matches:

            base_id = normalize_tvg_id(
                entry["tvg_id"]
            )

            if (
                base_id
                and base_id in used_ids
            ):

                continue

            selected = entry

            break

        # ----------------------------------------------------
        # Rakuten Fallback
        # ----------------------------------------------------

        if selected is None:

            selected = create_fallback_entry(
                display_name
            )

        if selected is None:

            continue

        base_id = normalize_tvg_id(
            selected["tvg_id"]
        )

        if base_id:

            if base_id in used_ids:

                continue

            used_ids.add(
                base_id
            )

        selected["category"] = (
            "00 Priorität"
        )

        selected["priority"] = (
            len(result) + 1
        )

        selected["display_name"] = (
            display_name
        )

        result.append(
            selected
        )

        found_names.add(
            display_name
        )

    return (
        result,
        used_ids
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

    # Rakuten immer ganz hinten

    if "rakuten tv" in text:

        return "09 Rakuten TV"

    # --------------------------------------------------------
    # Regional
    # --------------------------------------------------------

    regional_words = [

        "ndr niedersachsen",
        "ndr hamburg",

        "noa4",
        "noa 4",

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
    # Dokumentation
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
    # Rakuten
    # --------------------------------------------------------

    if "rakuten" in text:

        return "09 Rakuten TV"

    # --------------------------------------------------------
    # Rest
    # --------------------------------------------------------

    return "10 Weitere deutsche Sender"


# ============================================================
# REST SORTIEREN
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
# M3U INFO
# ============================================================

def clean_info(
    entry,
    category
):

    info = entry["info"]

    # group-title entfernen

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
        "#",
        "# 00 Priorität = feste Senderreihenfolge",
        "# HD bevorzugt",
        "# Nicht Geo-blocked bevorzugt",
        "# Geo-blocked bleibt erhalten",
        "# Rakuten TV am Ende der Priorität",
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
            os.remove(
                TEMP_OUTPUT
            )
        except OSError:
            pass

        raise RuntimeError(
            "Zu wenige Sender in neuer M3U: "
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
            "Zu wenige URLs in neuer M3U: "
            f"{url_count}"
        )

    if os.path.exists(
        OUTPUT
    ):

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
    # Quellen prüfen
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
    # Rest
    # --------------------------------------------------------

    rest = [

        entry

        for entry in filtered

        if (
            not normalize_tvg_id(
                entry["tvg_id"]
            )
            or normalize_tvg_id(
                entry["tvg_id"]
            ) not in used_ids
        )

    ]

    rest = sort_rest(
        rest
    )

    # --------------------------------------------------------
    # Endgültige Liste
    # --------------------------------------------------------

    entries = (
        fixed
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
    # M3U schreiben
    # --------------------------------------------------------

    content = build_m3u(
        entries
    )

    safe_write(
        content
    )

    # ========================================================
    # AUSGABE FIXED
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

        print(

            f"{number:02d}. "
            f"{entry['display_name']} "
            f"[{hd}/{geo}] "
            f"[{entry['source']}]"

        )

    # --------------------------------------------------------
    # Fehlende Fixed-Sender anzeigen
    # --------------------------------------------------------

    if len(fixed) < len(FIXED_CHANNELS):

        print()
        print(
            "FEHLENDE FIXED-SENDER:"
        )

        found = {
            entry["display_name"]
            for entry in fixed
        }

        for definition in FIXED_CHANNELS:

            name = definition[0]

            if name not in found:

                print(
                    f"  FEHLT: {name}"
                )

    # ========================================================
    # ERGEBNIS
    # ========================================================

    print()
    print("==========================================")
    print("ERGEBNIS")
    print("==========================================")

    print(
        "Gesamt:",
        len(entries)
    )

    print(
        "Fixed:",
        len(fixed),
        "/",
        len(FIXED_CHANNELS)
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

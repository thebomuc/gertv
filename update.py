import re
import urllib.request
from collections import OrderedDict

# ============================================================
# GER TV - persönliche deutsche M3U
# ============================================================
#
# Priorität:
#   1. Öffentlich-rechtlich
#   2. Niedersachsen / Norddeutschland
#   3. weitere Dritte
#   4. Private
#   5. Nachrichten / Doku
#   6. Religion
#
# Ausgeschlossen:
#   - Musik
#   - Shopping
#   - Erotik
#   - Zee One
#   - ONE Adria
#
# Wichtig:
# Die Sender werden über IPTV-org tvg-id erkannt,
# nicht über unzuverlässige Namenssuche.
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
# IPTV-org IDs.
#
# Falls ein ID-Name bei IPTV-org geändert wird, erscheint
# der Sender nicht künstlich als falscher Sender.
# ============================================================

TOP_50 = [

    # --------------------------------------------------------
    # Öffentlich-rechtlich
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Niedersachsen / Norddeutschland
    # --------------------------------------------------------

    "NDRNiedersachsen.de",
    "RTLNordNiedersachsenBremen.de",
    "RadioBremenTV.de",
    "Hamburg1.de",
    "1730SAT1REGIONALHamburgSchleswigHolstein.de",

    # --------------------------------------------------------
    # Weitere Dritte
    # --------------------------------------------------------

    "WDRKoeln.de",
    "BRFernsehen.de",
    "HRFernsehen.de",
    "MDRSachsen.de",
    "MDRSachsenAnhalt.de",
    "MDRThueringen.de",
    "RBB.de",
    "SWR.de",
    "SRFernsehen.de",

    # --------------------------------------------------------
    # Private
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Nachrichten / Doku
    # --------------------------------------------------------

    "Welt.de",
    "N-TV.de",
    "EuronewsDeutsch.de",
    "N24Doku.de",

    # --------------------------------------------------------
    # Religion
    # --------------------------------------------------------

    "BibelTV.de",
    "K-TV.de",
    "EWTN.de",
    "ERF1.de",
]


# ============================================================
# NICHT GEWÜNSCHTE KANÄLE
# ============================================================

EXCLUDE_IDS = {
    # Musik / falsche ONE-Varianten
    "OneAdria.hr",

    # Zee One / indisches Fernsehen
    "ZeeOne.de",
}


# ============================================================
# Unerwünschte Kategorien / Namen
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
# M3U PARSER
# ============================================================

def parse_m3u(text):

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

                # Sendername
                match = re.search(
                    r",(.+)$",
                    info
                )

                name = (
                    match.group(1).strip()
                    if match
                    else ""
                )

                # tvg-id
                match_id = re.search(
                    r'tvg-id="([^"]*)"',
                    info,
                    re.IGNORECASE
                )

                tvg_id = (
                    match_id.group(1).strip()
                    if match_id
                    else ""
                )

                # tvg-name
                match_name = re.search(
                    r'tvg-name="([^"]*)"',
                    info,
                    re.IGNORECASE
                )

                tvg_name = (
                    match_name.group(1).strip()
                    if match_name
                    else ""
                )

                # language
                match_lang = re.search(
                    r'tvg-language="([^"]*)"',
                    info,
                    re.IGNORECASE
                )

                language = (
                    match_lang.group(1).strip()
                    if match_lang
                    else ""
                )

                # country
                match_country = re.search(
                    r'tvg-country="([^"]*)"',
                    info,
                    re.IGNORECASE
                )

                country = (
                    match_country.group(1).strip()
                    if match_country
                    else ""
                )

                entries.append({
                    "info": info,
                    "name": name,
                    "tvg_name": tvg_name,
                    "tvg_id": tvg_id,
                    "language": language,
                    "country": country,
                    "url": url,
                })

            i += 2

        else:
            i += 1

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
    name = normalize(entry["name"])

    # Religion
    if tvg_id in {
        "BibelTV.de",
        "K-TV.de",
        "EWTN.de",
        "ERF1.de",
    }:
        return "09 Religion"

    # Norden
    if tvg_id in {
        "NDRNiedersachsen.de",
        "RTLNordNiedersachsenBremen.de",
        "RadioBremenTV.de",
        "Hamburg1.de",
        "1730SAT1REGIONALHamburgSchleswigHolstein.de",
    }:
        return "02 Niedersachsen & Norddeutschland"

    # Doku
    if tvg_id in {
        "KabelEinsDoku.de",
        "DMAX.de",
        "N24Doku.de",
    }:
        return "06 Dokumentation & Wissen"

    # Nachrichten
    if tvg_id in {
        "Welt.de",
        "N-TV.de",
        "EuronewsDeutsch.de",
    }:
        return "05 Nachrichten"

    # Kinder
    if tvg_id in {
        "KiKA.de",
    }:
        return "08 Kinder"

    # Öffentlich-rechtlich
    if tvg_id in {
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
    }:
        return "01 Öffentlich-Rechtlich"

    # Dritte
    if tvg_id in {
        "WDRKoeln.de",
        "BRFernsehen.de",
        "HRFernsehen.de",
        "MDRSachsen.de",
        "MDRSachsenAnhalt.de",
        "MDRThueringen.de",
        "RBB.de",
        "SWR.de",
        "SRFernsehen.de",
    }:
        return "03 Dritte Programme"

    # Private
    if tvg_id in {
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
    }:
        return "04 Private"

    # Sport
    if "sport" in name:
        return "10 Sport"

    return "11 Weitere deutsche Sender"


# ============================================================
# TOP-PRIORITÄT
# ============================================================

def priority(entry):

    tvg_id = entry["tvg_id"]

    try:
        return TOP_50.index(tvg_id)

    except ValueError:
        return 9999


# ============================================================
# M3U INFO BEREINIGEN
# ============================================================

def clean_info(info, name, group):

    # group-title ersetzen
    info = re.sub(
        r'\s+group-title="[^"]*"',
        "",
        info,
        flags=re.IGNORECASE
    )

    # alten Sendernamen hinter letztem Komma entfernen
    info = re.sub(
        r",.*$",
        "",
        info
    )

    return (
        f'{info} '
        f'group-title="{group}",'
        f'{name}'
    )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    all_entries = []

    # --------------------------------------------------------
    # Quellen
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
    # Nur echte deutsche Sender bevorzugen
    #
    # tvg-country kann mehrere Länder enthalten.
    # DE muss vorhanden sein.
    # --------------------------------------------------------

    german = []

    for entry in filtered:

        country = entry["country"].upper()

        language = normalize(
            entry["language"]
        )

        if (
            "DE" in country
            or "GERMANY" in country
            or "DEUTSCH" in language
            or entry["tvg_id"].endswith(".de")
        ):
            german.append(entry)

    # Falls eine Quelle keine tvg-country Angaben hat,
    # nicht alles verlieren.
    if len(german) < 20:
        german = filtered

    # --------------------------------------------------------
    # Nach tvg-id deduplizieren
    #
    # Ein Sender kann in mehreren Quellen stehen.
    # Wir wollen nur EINEN.
    # --------------------------------------------------------

    by_id = OrderedDict()

    for entry in german:

        tvg_id = entry["tvg_id"]

        if not tvg_id:
            continue

        if tvg_id not in by_id:

            by_id[tvg_id] = entry

        else:

            existing = by_id[tvg_id]

            # HD bevorzugen
            old_name = normalize(
                existing["name"]
            )

            new_name = normalize(
                entry["name"]
            )

            if (
                "hd" in new_name
                and "hd" not in old_name
            ):
                by_id[tvg_id] = entry

    entries = list(
        by_id.values()
    )

    print(
        "Nach tvg-id-Deduplizierung:",
        len(entries)
    )

    # --------------------------------------------------------
    # Metadaten
    # --------------------------------------------------------

    for entry in entries:

        entry["priority"] = priority(entry)

        entry["category"] = get_category(
            entry
        )

    # --------------------------------------------------------
    # Sortieren
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
            normalize(
                entry["name"]
            ),
        )
    )

    # --------------------------------------------------------
    # M3U
    # --------------------------------------------------------

    output = [
        "#EXTM3U",
        "",
        "# ==================================================",
        "# GER TV - Deutsche TV-Liste",
        "# Automatisch aktualisiert",
        "# Quelle: IPTV-org",
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
    # Ausgabe
    # --------------------------------------------------------

    found_top = [
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
        len(entries)
    )

    print(
        "Top-Sender gefunden:",
        len(found_top)
    )

    print()
    print("TOP-PRIORITÄT:")

    for number, entry in enumerate(
        found_top,
        start=1
    ):

        print(
            f"{number:02d}. "
            f"{entry['name']} "
            f"[{entry['tvg_id']}]"
        )

    print()
    print(
        "Datei:",
        OUTPUT
    )


if __name__ == "__main__":
    main()

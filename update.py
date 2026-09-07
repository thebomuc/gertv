import re
import os
import shutil
import urllib.request
import urllib.error
import socket
import threading
import traceback
from urllib.parse import urlparse, urljoin
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# GER TV - update.py
# ============================================================
#
# Erstellt:
#
#     deutsch.m3u
#
# REIHENFOLGE
# -----------
# 1. Persönliche FIXED / PRIORITÄT exakt in dieser Reihenfolge
# 2. Danach alle übrigen Sender alphabetisch A-Z
#
# QUELLEN
# -------
# Quellen besitzen eine feste Priorität.
#
# Eine neue Quelle ersetzt NICHT automatisch einen bereits
# vorhandenen Stream aus einer höher priorisierten Quelle.
#
# Innerhalb derselben Quellen-Priorität entscheidet:
#
#   1. HD + nicht Geo-blocked
#   2. SD + nicht Geo-blocked
#   3. HD + Geo-blocked
#   4. SD + Geo-blocked
#
# REGIONAL-FALLBACK
# -----------------
# Beispiel:
#
#   NDR Niedersachsen
#       ↓ falls nicht gefunden
#   NDR Hamburg
#       ↓ falls nicht gefunden
#   allgemeiner NDR
#
# KODI
# ----
# Fremde tvg-chno-Werte werden entfernt.
# Kodi soll die Reihenfolge der erzeugten M3U verwenden.
#
# NETPLUS
# -------
# viamotionhsi.netplus.ch wird grundsätzlich ausgeschlossen.
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
        "https://github.io"
    ),

    (
        "Bayern",
        "https://github.io"
    ),

    (
        "Berlin",
        "https://github.io"
    ),

    (
        "Brandenburg",
        "https://github.io"
    ),

    (
        "Hamburg",
        "https://github.io"
    ),

    (
        "Mecklenburg-Vorpommern",
        "https://github.io"
    ),

    (
        "Niedersachsen",
        "https://github.io"
    ),

    (
        "Schleswig-Holstein",
        "https://github.io"
    ),

    (
        "German TV M3U",
        "https://githubusercontent.com"
    ),

]


# ============================================================
# ZUSÄTZLICHE FALLBACK-QUELLEN
# ============================================================
#
# Diese Quellen werden beim normalen Quellenlauf geladen.
# Für den Rest-Lauf werden sie vollautomatisch per Multithreading
# auf Erreichbarkeit (Health-Check) geprüft.
# ============================================================

FALLBACK_SOURCES = [
    (
        "Kodinerds",
        "https://githubusercontent.com"
    ),
    (
        "Free-TV/IPTV Deutschland",
        "https://githubusercontent.com"
    ),
    (
        "deutsche-iptv-playlist",
        "https://githubusercontent.com"
    ),
]

# Pro Lauf wird jede Fallback-Quelle höchstens einmal geladen.
FALLBACK_ENTRIES_CACHE = {}
FALLBACK_SOURCE_ERRORS = {}


# ============================================================
# QUELLEN-PRIORITÄT
# ============================================================
#
# Kleine Zahl = höhere Priorität.
#
# Die Reihenfolge deiner bisherigen Quellen bleibt erhalten.
# Die drei zusätzlichen Quellen kommen danach als Fallback.
#
# Wichtig:
# Die Quellen-Priorität kommt VOR dem Stream-Score.
#
# Also:
#
#   bessere Quelle + SD
#
# kann gegenüber
#
#   schlechtere Quelle + HD
#
# gewinnen.
#
# Dadurch ersetzen neue Quellen nicht ungefragt deine
# bisherigen funktionierenden Streams.
# ============================================================

SOURCE_PRIORITY = {

    "Deutschland": 1,

    "Bayern": 2,
    "Berlin": 3,
    "Brandenburg": 4,
    "Hamburg": 5,
    "Mecklenburg-Vorpommern": 6,
    "Niedersachsen": 7,
    "Schleswig-Holstein": 8,

    "German TV M3U": 9,

    # Neue Quellen ausschließlich als Fallback
    "Kodinerds": 10,
    "Free-TV/IPTV Deutschland": 11,
    "deutsche-iptv-playlist": 12,
}


def source_score(entry):
    return SOURCE_PRIORITY.get(
        entry.get("source", ""),
        99
    )


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
# Innerhalb derselben Variante:
#
#   Quelle → Stream-Qualität
#
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
        "ONE HD",
        [
            {
                "ids": ["one.de"],
                "names": ["one hd"],
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

    # Restliche Definitionen hier weiter einfügen...

]

# ... weitere Funktionen und Code ...

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("==========================================")
        print("UPDATE FEHLGESCHLAGEN")
        print("==========================================")
        print(f"{type(error).__name__}: {error}")
        traceback.print_exc()
        print()
        print("Die vorhandene deutsch.m3u wurde NICHT überschrieben.")
        if os.path.exists(TEMP_OUTPUT):
            try:
                os.remove(TEMP_OUTPUT)
            except OSError:
                pass
        raise SystemExit(1)

"""Zentrale Einstellungen. Alles, was man wöchentlich evtl. anpassen will, steht hier."""

SITE_TITLE = "Hinkowicz Bestpreis-Listen"
SITE_URL = "https://hinkowicz.com"

# Wird an JEDEN Geizhals-Link angehängt (Provision).
AFFILIATE_PARAMS = "cs_id=491744683&ccpid=hinkowiczlisten"
GEIZHALS_BASE = "https://geizhals.de"

AD_NOTICE = (
    "Die mit * markierten Links sind Affiliate-Links. Kaufst du darüber ein, "
    "erhalte ich eine kleine Provision – für dich ändert sich am Preis nichts."
)

# --- Geizhals-Kategorien -----------------------------------------------------
# Regex auf den Kategoriepfad im /categories-Baum. Unterkategorien (z. B. "AMD AM5")
# sind bei Geizhals Filter (xf/preset) einer Oberkategorie – die werden automatisch mitgenommen.
CATEGORIES = {
    "gpu":         r"Grafikkarten > PCIe$",
    "cpu_am5":     r"CPUs > AMD AM5$",
    "cpu_am4":     r"CPUs > AMD AM4$",
    "cpu_1700":    r"CPUs > Intel 1700$",
    "mb_am5":      r"Mainboards > Mainboards > AMD AM5$",
    "mb_am4":      r"Mainboards > Mainboards > AMD AM4$",
    "mb_1700":     r"Mainboards > Mainboards > Intel 1700$",
    "ram_ddr5_16": r"Speicher > DDR5 DIMM 2x 8GB$",
    "ram_ddr5_32": r"Speicher > DDR5 DIMM 2x 16GB$",
    "ram_ddr4_16": r"Speicher > DDR4 DIMM 2x 8GB$",
    "ram_ddr4_32": r"Speicher > DDR4 DIMM 2x 16GB$",
    "ssd":         r"Solid State Drives \(SSD\) > M\.2 \(PCIe\)$",
    "psu":         r"Netzteile & USV > Netzteile$",
    "case":        r"PC-Gehäuse > Midi-Tower$",
    "cooler":      r"Luftkühlung > CPU-Kühler$",
}

# --- Plattformen ---------------------------------------------------------------
PLATFORMS = {
    "AM5": {"cpu": "cpu_am5", "mb": "mb_am5", "ram": "ram_ddr5",
            "mb_regex": r"\bB[68]50M?\b", "ram_speed": r"DDR5-(5600|6000|6400)"},
    "AM4": {"cpu": "cpu_am4", "mb": "mb_am4", "ram": "ram_ddr4",
            "mb_regex": r"\bB550M?\b", "ram_speed": r"DDR4-(3200|3600)"},
    "LGA1700": {"cpu": "cpu_1700", "mb": "mb_1700", "ram": "ram_ddr5",
                "mb_regex": r"\bB760M?\b", "mb_exclude": r"DDR4",
                "ram_speed": r"DDR5-(5200|5600|6000)"},
}

# --- Budget-Stufen --------------------------------------------------------------
# max = harte Obergrenze. gpu_weight = wie stark die GPU im Score zählt (Rest: CPU).
TIERS = [
    {"id": "600",  "name": "Einsteiger",    "budget": 600,  "max": 630,
     "platforms": ["AM4", "AM5", "LGA1700"], "ram_gb": 16, "ssd_tb": 1,
     "min_vram": 8, "gpu_weight": 0.80, "case_max": 60, "cooler_max": 25, "board_wifi": False,
     "boxed_cooler_ok": True},
    {"id": "800",  "name": "Full-HD Allrounder", "budget": 800, "max": 840,
     "platforms": ["AM4", "AM5", "LGA1700"], "ram_gb": 16, "ssd_tb": 1,
     "min_vram": 8, "gpu_weight": 0.78, "case_max": 75, "cooler_max": 30, "board_wifi": False,
     "boxed_cooler_ok": True},
    {"id": "1000", "name": "WQHD Einstieg", "budget": 1000, "max": 1050,
     "platforms": ["AM4", "AM5", "LGA1700"], "ram_gb": 16, "ssd_tb": 1,
     "min_vram": 12, "gpu_weight": 0.75, "case_max": 90, "cooler_max": 40, "board_wifi": False},
    {"id": "1500", "name": "WQHD High-End", "budget": 1500, "max": 1575,
     "platforms": ["AM5"], "ram_gb": 32, "ssd_tb": 1,
     "min_vram": 16, "gpu_weight": 0.72, "case_max": 120, "cooler_max": 55, "board_wifi": True},
    {"id": "2000", "name": "4K Enthusiast", "budget": 2000, "max": 2300,
     "platforms": ["AM5"], "ram_gb": 32, "ssd_tb": 2,
     "min_vram": 16, "gpu_weight": 0.70, "case_max": 160, "cooler_max": 70, "board_wifi": True},
]

# --- Qualitäts-Whitelist (eigene Auswahl) ---------------------------------------
BOARD_BRANDS = r"^(ASUS|MSI|GIGABYTE|Gigabyte|ASRock)\b"
SSD_GOOD = (r"990 (PRO|EVO)|9100 PRO|SN850X|SN7100|SN770|SN5000|KC3000|NV3\b|Fury Renegade|"
            r"MP44|P3 Plus|P5 Plus|T500|T700|FireCuda 5[23]0|Lexar NM790|NM790|Lexar NQ790|"
            r"Kingston NV3|Crucial P310|P310|Solidigm P44|Corsair MP600|MP700|PNY CS2150|Patriot Viper VP4300")
PSU_GOOD = (r"Pure Power 1[23]|Straight Power 1[2-9]|Dark Power|System Power 11|MAG A\d{3}BN|PK\d{3}D|"
            r"Corsair RM\d|RM\d{3,4}e|RM\d{3,4}x|CX\d{3}|"
            r"MAG A\d{3}G?L|MPG A\d{3}G|"
            r"Focus GX|Focus GM|Core GX|Vertex|"
            r"Toughpower GF A3|Toughpower GF3|Endorfy Supremo|Supremo FM5|Vero L5|"
            r"Seasonic G12|Cooler Master MWE Gold|MWE Gold V2|Enermax Revolution|"
            r"Lian Li (EG|SP)|NZXT C\d{3,4}|DeepCool PN|PN\d{3}M|PX\d{3,4}G")
CASE_GOOD = (r"Pop Air|Pop XL|North|Meshify|Focus 2|"
             r"Lancool (207|216|217|III)|O11 Vision|Lian Li A3|"
             r"XT View|XT Pro|XT Ultra|NV5|NV7|Eclipse G3|"
             r"Montech (XR|AIR 903|AIR 100|Sky Two|King 95)|"
             r"3000D|4000D|5000D|Frame 4000D|"
             r"Pure Base 50[01]|Light Base|Shadow Base|"
             r"CC560|CH560|CH510|CG580|CH690|"
             r"Endorfy (Ventum|Signum|Arx)|Jonsbo D4[01]|Kolink Observatory|"
             r"H5 Flow|H6 Flow|H7 Flow|"
             r"Antec (C5|C8|Flux)|Fractal Design Terra")
COOLER_GOOD = (r"Peerless Assassin 120|Phantom Spirit 120|Assassin X 120|Assassin Spirit 120|"
               r"Freezer 36|Freezer 34|Pure Rock (2|3|Pro 3)|Dark Rock (4|5|Pro 5|Elite)|"
               r"Fortis 5|AK400|AK500|AK620|Hyper 212|Royal Knight 120|Frozen Notte|"
               r"Liquid Freezer III|NH-D15|NH-U12A")

# --- Deals -------------------------------------------------------------------------
# Top-Level-Kategorien, die als "Technik" zählen (Regex auf den Titel).
DEAL_TOPCATS = r"Hardware|Video|Foto|TV|Telefon|Audio|HIFI|Games|Spiele|Software|Haushalt"
DEAL_SETTINGS = {
    "interval": "31d",
    "pricemin": 30,
    "drop_percentmin": 10,
    "per_topcat": 100,
    "max_per_midcat": 3,
    "top_n": 30,
}

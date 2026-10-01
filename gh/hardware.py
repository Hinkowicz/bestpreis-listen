"""Eigene Leistungs-Indizes (Hinkowicz-Score).

Werte sind relative Gaming-Leistung, gemittelt aus öffentlichen Benchmarks
(WQHD für GPUs, CPU-Limit-Tests für CPUs). Bewusst eigene Gewichtung –
regelmäßig prüfen und bei neuen Releases ergänzen.

GPU:  RTX 5070 = 100      CPU: Ryzen 7 9800X3D = 100
"""
import re

# (Anzeigename, Regex auf Geizhals-Produktnamen, Leistung, empf. Netzteil-Watt, Standard-VRAM)
GPUS = [
    ("GeForce RTX 5090",    r"RTX 5090(?!\s*D)",        205, 1000, 32),
    ("GeForce RTX 5080",    r"RTX 5080",                150, 850, 16),
    ("GeForce RTX 5070 Ti", r"RTX 5070 Ti",             130, 750, 16),
    ("Radeon RX 9070 XT",   r"RX 9070 XT",              127, 750, 16),
    ("Radeon RX 9070",      r"RX 9070(?! XT|\s*GRE)",   112, 650, 16),
    ("Radeon RX 9070 GRE",  r"RX 9070 GRE",              96, 650, 12),
    ("GeForce RTX 5070",    r"RTX 5070(?! Ti)",          100, 650, 12),
    ("Radeon RX 7800 XT",   r"RX 7800 XT",               92, 700, 16),
    ("GeForce RTX 4070 Super", r"RTX 4070 S(uper|UPER)", 102, 650, 12),
    ("Radeon RX 7700 XT",   r"RX 7700 XT",               80, 700, 12),
    ("GeForce RTX 5060 Ti", r"RTX 5060 Ti",              77, 550, 16),
    ("Radeon RX 9060 XT",   r"RX 9060 XT",               75, 550, 16),
    ("GeForce RTX 5060",    r"RTX 5060(?! Ti)",           65, 550, 8),
    ("GeForce RTX 4060",    r"RTX 4060(?! Ti)",           57, 550, 8),
    ("Intel Arc B580",      r"Arc B580",                  59, 550, 12),
    ("Intel Arc B570",      r"Arc B570",                  51, 500, 10),
    ("Radeon RX 7600",      r"RX 7600(?! XT)",            50, 550, 8),
    ("GeForce RTX 5050",    r"RTX 5050",                  49, 500, 8),
    ("Radeon RX 6600",      r"RX 6600(?! XT)",            40, 500, 8),
]

# (Anzeigename, Regex, Leistung, Plattform, Leistungsaufnahme-Klasse in W)
CPUS = [
    ("Ryzen 7 9850X3D",  r"Ryzen 7 9850X3D",   104, "AM5", 120),
    ("Ryzen 7 9800X3D",  r"Ryzen 7 9800X3D",   100, "AM5", 120),
    ("Ryzen 9 9950X3D",  r"Ryzen 9 9950X3D",   101, "AM5", 170),
    ("Ryzen 7 7800X3D",  r"Ryzen 7 7800X3D",    89, "AM5", 120),
    ("Ryzen 5 7600X3D",  r"Ryzen 5 7600X3D",    84, "AM5", 65),
    ("Ryzen 7 9700X",    r"Ryzen 7 9700X\b",    78, "AM5", 65),
    ("Ryzen 5 9600X",    r"Ryzen 5 9600X\b",    76, "AM5", 65),
    ("Ryzen 5 9600",     r"Ryzen 5 9600(?![X\d])", 74, "AM5", 65),
    ("Ryzen 7 7700",     r"Ryzen 7 7700(?![X\d])", 73, "AM5", 65),
    ("Ryzen 5 7600X",    r"Ryzen 5 7600X\b",    71, "AM5", 105),
    ("Ryzen 5 7600",     r"Ryzen 5 7600(?![X\d])", 69, "AM5", 65),
    ("Ryzen 5 7500F",    r"Ryzen 5 7500F",      67, "AM5", 65),
    ("Ryzen 5 8400F",    r"Ryzen 5 8400F",      58, "AM5", 65),
    ("Ryzen 7 5700X3D",  r"Ryzen 7 5700X3D",    70, "AM4", 105),
    ("Ryzen 7 5800X3D",  r"Ryzen 7 5800X3D",    72, "AM4", 105),
    ("Ryzen 7 5700X",    r"Ryzen 7 5700X\b",    57, "AM4", 65),
    ("Ryzen 5 5600X",    r"Ryzen 5 5600X\b",    55, "AM4", 65),
    ("Ryzen 5 5600",     r"Ryzen 5 5600(?![XGT\d])", 54, "AM4", 65),
    ("Ryzen 5 5500",     r"Ryzen 5 5500\b",     45, "AM4", 65),
    ("Core i5-14600KF",  r"i5-14600KF",         77, "LGA1700", 180),
    ("Core i5-14400F",   r"i5-14400F",          66, "LGA1700", 150),
    ("Core i5-13400F",   r"i5-13400F",          63, "LGA1700", 150),
    ("Core i5-12400F",   r"i5-12400F",          58, "LGA1700", 120),
]

GB_RE = re.compile(r"(?<![\w.])(\d{1,2})\s?GB\b", re.I)


def match_gpu(name):
    for label, rx, perf, psu, vram in GPUS:
        if re.search(rx, name, re.I):
            m = GB_RE.search(name)
            v = int(m.group(1)) if m else vram
            # 8-GB-Varianten (z. B. 5060 Ti 8GB) sind spürbar schwächer bei neuen Spielen
            adj = perf * (0.95 if v <= 8 and vram > 8 else 1.0)
            return {"chip": label, "perf": adj, "psu": psu, "vram": v}
    return None


def match_cpu(name, platform):
    for label, rx, perf, plat, watt in CPUS:
        if plat == platform and re.search(rx, name, re.I):
            return {"chip": label, "perf": perf, "watt": watt}
    return None

"""Offline-Testdaten (BEISPIELPREISE, keine echten Angebote) – für Vorschau & Tests."""
from . import config

_P = {
    "gpu": [("Sapphire Pulse Radeon RX 9070 XT, 16GB GDDR6", 649), ("PowerColor Reaper Radeon RX 9070 XT, 16GB GDDR6", 639),
            ("XFX Swift Radeon RX 9070, 16GB GDDR6", 569), ("MSI GeForce RTX 5070 Ventus 2X OC, 12GB GDDR7", 539),
            ("ASUS Prime GeForce RTX 5070 Ti OC, 16GB GDDR7", 799), ("Gainward GeForce RTX 5080 Phoenix, 16GB GDDR7", 1059),
            ("Palit GeForce RTX 5060 Ti Infinity 3, 16GB GDDR7", 429), ("Palit GeForce RTX 5060 Ti Dual, 8GB GDDR7", 359),
            ("Sapphire Pulse Radeon RX 9060 XT, 16GB GDDR6", 369), ("XFX Swift Radeon RX 9060 XT, 8GB GDDR6", 299),
            ("Gigabyte GeForce RTX 5060 Windforce OC, 8GB GDDR7", 289), ("Intel Arc B580 Limited Edition, 12GB GDDR6", 259),
            ("ASRock Challenger Arc B570, 10GB GDDR6", 219), ("Zotac Gaming GeForce RTX 5050 Twin Edge, 8GB GDDR6", 239),
            ("Gigabyte Radeon RX 7600 Gaming OC, 8GB GDDR6", 239), ("Zotac GeForce RTX 5090 Solid, 32GB GDDR7", 2399)],
    "cpu_am5": [("AMD Ryzen 7 9800X3D, 8C/16T, 4.70-5.20GHz, boxed ohne Kühler", 449), ("AMD Ryzen 7 7800X3D, 8C/16T, boxed ohne Kühler", 339),
                ("AMD Ryzen 5 7500F, 6C/12T, tray", 129), ("AMD Ryzen 5 9600X, 6C/12T, boxed ohne Kühler", 189),
                ("AMD Ryzen 5 7600, 6C/12T, boxed", 159), ("AMD Ryzen 7 9700X, 8C/16T, boxed ohne Kühler", 269),
                ("AMD Ryzen 5 7600X3D, 6C/12T, boxed ohne Kühler", 289)],
    "cpu_am4": [("AMD Ryzen 5 5600, 6C/12T, boxed", 79), ("AMD Ryzen 7 5700X3D, 8C/16T, boxed ohne Kühler", 199),
                ("AMD Ryzen 7 5700X, 8C/16T, boxed ohne Kühler", 119), ("AMD Ryzen 5 5500, 6C/12T, boxed", 59)],
    "cpu_1700": [("Intel Core i5-12400F, 6C/12T, boxed", 99), ("Intel Core i5-14400F, 10C/16T, boxed", 139)],
    "mb_am5": [("MSI PRO B650M-P", 109), ("ASRock B650M-HDV/M.2", 99), ("Gigabyte B650 Eagle AX", 149),
               ("MSI MAG B850 Tomahawk MAX WIFI", 219), ("ASUS TUF Gaming B850-Plus WIFI", 199)],
    "mb_am4": [("MSI B550-A PRO", 99), ("ASRock B550M Pro4", 89)],
    "mb_1700": [("MSI PRO B760M-E DDR4", 85), ("ASRock B760M-HDV/M.2", 99), ("Gigabyte B760 Gaming X", 129)],
    "ram_ddr5_32": [("Kingston FURY Beast DIMM Kit 32GB, DDR5-6000, CL30-40-40, on-die ECC", 149),
                 ("Crucial Pro DIMM Kit 32GB, DDR5-5600, CL46-45-45", 129),
                 ("G.Skill Flare X5 DIMM Kit 16GB, DDR5-6000, CL36-36-36", 79),
                 ("Patriot Viper Venom DIMM Kit 16GB, DDR5-5600, CL40", 72)],
    "ram_ddr4_16": [("Corsair Vengeance LPX DIMM Kit 16GB, DDR4-3200, CL16", 59),
                 ("G.Skill Ripjaws V DIMM Kit 16GB, DDR4-3600, CL16", 64),
                 ("Kingston FURY Beast DIMM Kit 32GB, DDR4-3200, CL16", 109)],
    "ssd": [("Kingston NV3 NVMe SSD 1TB, M.2 2280 / M-Key / PCIe 4.0 x4", 69), ("WD_BLACK SN7100 NVMe SSD 1TB, M.2 2280 / PCIe 4.0 x4", 79),
            ("Samsung SSD 990 EVO Plus 2TB, M.2 2280 / PCIe 4.0 x4 / 5.0 x2", 139), ("Lexar NM790 SSD 2TB, M.2 2280 / PCIe 4.0 x4", 129),
            ("Samsung SSD 870 EVO 1TB, SATA", 89)],
    "psu": [("be quiet! Pure Power 12 M 550W ATX 3.0", 79), ("be quiet! Pure Power 12 M 650W ATX 3.1", 89),
            ("Corsair RM750e 750W ATX 3.1, modular", 99), ("MSI MAG A850GL PCIE5 850W", 109),
            ("Corsair RM1000x 1000W ATX 3.1", 179), ("Inter-Tech Argus 600W", 49), ("MSI MAG A550BN 550W", 49), ("MSI MAG A650BN 650W", 57)],
    "case": [("Montech AIR 903 Base, schwarz", 69), ("Phanteks XT Pro Ultra, schwarz", 79), ("Lian Li Lancool 207, schwarz", 85),
             ("Fractal Design Pop Air, schwarz", 79), ("Sharkoon VS4-V, schwarz", 39), ("Kolink Observatory HF Glass ARGB", 49),
             ("Fractal Design North, Charcoal Black", 129)],
    "cooler": [("Thermalright Peerless Assassin 120 SE", 39), ("Thermalright Assassin X 120 Refined SE", 19),
               ("Arctic Freezer 36", 25), ("be quiet! Pure Rock 3", 39), ("Arctic Liquid Freezer III Pro 360", 89)],
}

_DEALS = [
    ("Samsung Galaxy S25, 256GB, Navy", 619, -21, "Telefon & Co", "Handys", True),
    ("Sony WH-1000XM6 schwarz", 329, -18, "Audio/HIFI", "Kopfhörer", False),
    ("LG OLED65C57LA 65\" OLED TV", 1299, -24, "Video/Foto/TV", "Fernseher", True),
    ("Samsung Odyssey OLED G6 27\" 360Hz", 499, -26, "Hardware", "Monitore", True),
    ("Apple iPad Air 11\" M3 128GB", 579, -12, "Hardware", "Tablets", False),
    ("Logitech G Pro X Superlight 2", 119, -25, "Hardware", "Mäuse", False),
    ("Nintendo Switch 2", 449, -10, "Games", "Konsolen", False),
    ("Dyson V15 Detect Absolute", 499, -22, "Haushalt", "Staubsauger", False),
    ("Crucial T705 2TB, M.2", 219, -19, "Hardware", "SSDs", True),
    ("Sonos Arc Ultra", 749, -17, "Audio/HIFI", "Soundbars", False),
]


class MockAPI:
    calls = 0

    def categories(self, m=None):
        # pro Config-Eintrag ein Knoten, dessen Pfad auf die Regex passt
        def node(k, rx):
            parts = rx.replace("\\", "").rstrip("$").split(" > ")
            leaf = {"id": {"cat": k}, "title": parts[-1]}
            for t in reversed(parts[:-1]):
                leaf = {"id": {}, "title": t, "childs": [leaf]}
            return leaf
        return [{"id": {"m": 1}, "title": "Hardware",
                 "childs": [node(k, rx) for k, rx in config.CATEGORIES.items()]},
            {"id": {"m": 2}, "title": "Audio/HIFI"}, {"id": {"m": 3}, "title": "Video/Foto/TV"}]

    def categorylist(self, category, **params):
        key = category
        if key.startswith("ram_"):  # Beispiel-RAM liegt gemischt vor, Builder filtert nach Größe
            _P.setdefault(key, _P["ram_ddr5_32"] if "ddr5" in key else _P["ram_ddr4_16"])
        prods = [{"id": 1000000 + 1000 * list(config.CATEGORIES).index(key) + i, "product": n, "best_price": p,
                  "hname": "Beispielshop", "image_thumb": None} for i, (n, p) in enumerate(_P.get(key, []))]
        if params.get("sort") == "p":
            prods.sort(key=lambda x: x["best_price"])
        return {"products": prods}

    def bestprice_development(self, **params):
        deals = [{"id": 3000000 + i, "product": n, "best_price": p, "change_in_percent": pct, "alltime_best": at,
                  "category_path": f"{top} > {cat}", "middle_category_name": cat, "offer_count": 30, "hname": "Beispielshop"}
                 for i, (n, p, pct, top, cat, at) in enumerate(_DEALS)]
        if params.get("h_id") == 4711:  # Amazon-Liste: gleiche Beispiel-Deals, Amazon als Bestpreis-Händler
            deals = [{**d, "hname": "Amazon.de", "h_id": "4711"} for d in deals]
        return {"deals": deals if params.get("m") == 1 else [],
                "merchants": [{"id": 1234, "name": "Beispielshop", "count": "9"}, {"id": 4711, "name": "Amazon.de", "count": "7"}]}

    def post(self, endpoint, payload):
        if endpoint == "query_product":  # Beispiel-ASIN aus der Geizhals-ID
            return {"response": {"products": [{"asins": [f"B0MOCK{int(payload['query']) % 10000:04d}"]}]}}
        raise NotImplementedError(endpoint)

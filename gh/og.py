"""Vorschaukarten (Open Graph) für geteilte Links: Meta-Tags + automatisch erzeugte Bilder im Hinkowicz-Look."""
import html
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SITE = "https://hinkowicz.de"
W, H = 1200, 630
FONTS = Path(__file__).parent / "fonts"
CYAN, MAGENTA = (34, 211, 238), (228, 64, 208)


def meta(title, description, image, path):
    t, d = html.escape(title), html.escape(description)
    img, url = f"{SITE}/og/{image}", SITE + path
    return (f'\n<meta property="og:type" content="website"><meta property="og:site_name" content="Hinkowicz">'
            f'<meta property="og:title" content="{t}"><meta property="og:description" content="{d}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{img}">'
            f'<meta property="og:image:width" content="{W}"><meta property="og:image:height" content="{H}">'
            f'<meta property="og:locale" content="de_DE"><meta name="twitter:card" content="summary_large_image">'
            f'<link rel="canonical" href="{url}">')


def _font(size, bold=True):
    return ImageFont.truetype(str(FONTS / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)


def _base():
    """Dunkler Hintergrund mit Farbwolken, Logo-Muster und Glasfläche."""
    img = Image.new("RGB", (W, H), (6, 7, 10))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((-250, -300, 650, 500), fill=(18, 110, 125))
    d.ellipse((650, 180, 1500, 950), fill=(120, 30, 110))
    d.ellipse((250, 420, 900, 1000), fill=(45, 45, 120))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(140)), 0.85)
    pattern = Path("assets/pattern.webp")
    if pattern.exists():
        p = Image.open(pattern).convert("RGB").resize((700, 388))
        tile = Image.new("RGB", (W, H))
        for x in range(0, W, 700):
            for y in range(0, H, 388):
                tile.paste(p, (x, y))
        img = Image.blend(img, tile, 0.12)
    img = img.convert("RGBA")
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((40, 40, W - 40, H - 40), radius=44, fill=(255, 255, 255, 20),
                                            outline=(255, 255, 255, 60), width=2)
    return Image.alpha_composite(img, panel)


def _logo(img, x, y, height):
    p = Path("assets/logo-dark.png")
    if p.exists():
        logo = Image.open(p).convert("RGBA")
        logo = logo.resize((round(logo.width * height / logo.height), height), Image.LANCZOS)
        img.alpha_composite(logo, (x, y))
        return logo.width
    return 0


def _gradient_text(img, xy, text, font):
    """Text mit Cyan→Magenta-Verlauf."""
    d = ImageDraw.Draw(img)
    box = d.textbbox(xy, text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    grad = Image.new("RGBA", (w, h))
    for x in range(w):
        t = x / max(w - 1, 1)
        c = tuple(round(CYAN[i] + (MAGENTA[i] - CYAN[i]) * t) for i in range(3)) + (255,)
        ImageDraw.Draw(grad).line([(x, 0), (x, h)], fill=c)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.paste(grad, (box[0], box[1]))
    img.paste(layer, (0, 0), mask)


def _fit(text, size, max_w, bold=True):
    while size > 20:
        f = _font(size, bold)
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return _font(size, bold)


def card(path, kicker, title, lines=(), big=None):
    img = _base()
    d = ImageDraw.Draw(img)
    _logo(img, 90, 88, 64)
    _gradient_text(img, (92, 186), kicker.upper(), _font(26))
    d.text((90, 228), title, font=_fit(title, 64, W - 180), fill=(243, 245, 249))
    y = 330
    if big:
        _gradient_text(img, (88, y - 6), big, _fit(big, 96, W - 180))
        y += 120
    for line in lines:
        d.text((92, y), line, font=_fit(line, 32, W - 190, bold=False), fill=(200, 205, 220))
        y += 46
    d.text((92, H - 104), "hinkowicz.de", font=_font(28), fill=(235, 240, 255))
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)


def eur(v):
    return f"{v:,.0f} €".replace(",", ".")


def write_all(out_dir, builds, deals, tiers):
    o = Path(out_dir) / "og"
    card(o / "home.png", "Gaming · Technik · Setup", "Hinkowicz", ["Links, Rabattcodes, mein Setup,", "Gaming-PC Bestpreis-Listen & Technik-Deals"])
    card(o / "setup.png", "Mein Setup", "Alles, was auf meinem Tisch steht",
         ["Monitore, Peripherie, Kabelmanagement & mehr"])
    last = tiers[-1]["id"]
    overview = [f"bis {b['budget']}{'+' if b['tier'] == last else ''} €:  {eur(b['total'])}  ·  {b['parts'][1]['note'].split(' · ')[0]}"
                for b in builds]
    card(o / "pc.png", "Jede Woche neu berechnet", "Gaming-PC Bestpreis-Listen", overview[:4])
    for b in builds:
        plus = "+" if b["tier"] == last else ""
        card(o / f"pc-{b['tier']}.png", f"Gaming-PC bis {b['budget']}{plus} € · Hinko-Score {b['score']}", "Diese Woche für",
             [f"{b['parts'][0]['note']}  +  {b['parts'][1]['note']}"], big=eur(b["total"]))
    top = [f"{d['percent']} %  {d['name'][:46]}" for d in deals[:3]]
    card(o / "deals.png", "Größte Preissenkungen", "Technik-Deals der Woche", top)

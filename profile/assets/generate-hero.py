"""Generate the org profile hero banner (this directory: hero-{dark,light}.svg).

The starworks.dev homepage hero, restated as a static, CSS-animated SVG that
GitHub can show through an <img>: the hero's 135deg gradient (#4e4376 ->
#2b5876), the seeded star field from src/lib/actions/starField.ts (mulberry32,
same size / speed / brightness formulas) drifting down, the two shooting-star
lanes, and the STARWORKS title (Space Mono Bold, 0.1em tracking, white glow)
over a divider and the Inter Light subtitle. Text is converted to outlines, so
the SVG needs no fonts (GitHub's image proxy loads nothing external).

    python generate-hero.py <starworks website repo> profile/assets

Fonts: the site's vendored Space Mono / Inter woff2 (both SIL OFL 1.1).
"""
import math
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

W, H = 1280, 400
TITLE = "STARWORKS"
SUBTITLE = "An independent studio making games, and the engine they run on."
SEED = 20260913  # any fixed seed: the field must not change between regenerations


def mulberry32(seed):
    """The site's PRNG (hero3d's mulberry32), bit for bit."""
    state = [seed & 0xFFFFFFFF]

    def rng():
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = state[0]
        t = (((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF)
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng


def star_field(seed, count):
    """createStarField from starField.ts."""
    rng = mulberry32(seed)
    stars = []
    for _ in range(count):
        x, y = rng(), rng()
        size = rng() * 1 + 0.5
        norm = (size - 0.5) / 1
        speed = (0.025 + norm * 0.2) * (1 + (rng() - 0.5) * 0.3) * 60
        brightness = max(0.05, min(1, (0.3 + norm * 0.7) * (1 + (rng() - 0.5) * 0.8)))
        stars.append((x, y, size, speed, brightness))
    return stars


def text_path(font, text, size, tracking_em, center_x, baseline):
    """Outline `text` as one SVG path, centred on center_x."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    names = [cmap[ord(c)] for c in text]
    advances = [font["hmtx"][n][0] * scale for n in names]
    track = tracking_em * size
    width = sum(advances) + track * (len(text) - 1)
    x = center_x - width / 2
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    for n, adv in zip(names, advances):
        gs[n].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        x += adv + track
    return pen.getCommands(), width


def build(site, variant):
    fonts = Path(site) / "static/assets/vendor/fonts"
    mono = TTFont(fonts / "i7dMIFZifjKcF5UAWdDRaPpZUFWaHg.woff2")  # Space Mono 700, basic Latin
    inter = TTFont(fonts / "UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2")  # Inter variable, basic Latin
    if "fvar" in inter:
        inter = instantiateVariableFont(inter, {"wght": 300})

    title, _ = text_path(mono, TITLE, 104, 0.1, W / 2, 196)
    subtitle, _ = text_path(inter, SUBTITLE, 27, 0.05 * 0.6, W / 2, 278)

    # Density: the site paints 416 stars on a desktop viewport (~1920x1080);
    # the same density over the banner is ~100. A few more read better small.
    stars = star_field(SEED, 150)
    # Group into drift layers by speed so each layer loops seamlessly: the
    # layer's stars are drawn twice (y and y - H) and the group slides by H.
    layers = {}
    for x, y, size, speed, b in stars:
        band = min(3, int((speed - 1.5) / 3.2))
        layers.setdefault(band, []).append((x * W, y * H, size, b))
    layer_svg = []
    css = []
    for band, items in sorted(layers.items()):
        # Layer period: H at the band's mean speed (px/s) -> seconds per loop.
        mean_speed = 1.5 + 3.2 * band + 1.6
        period = H / mean_speed
        dots = []
        for x, y, size, b in items:
            for dy in (0, -H):
                dots.append(f'<circle cx="{x:.1f}" cy="{y + dy:.1f}" r="{size:.2f}" fill-opacity="{b:.2f}"/>')
        layer_svg.append(f'<g class="drift d{band}">{"".join(dots)}</g>')
        css.append(f".d{band}{{animation:drift {period:.1f}s linear infinite}}")
    # A handful of the brightest stars twinkle, as the eye reads them on the site.
    bright = sorted(stars, key=lambda s: -s[4])[:10]
    twinkles = "".join(
        f'<circle class="tw" style="animation-delay:-{i * 0.73:.2f}s" cx="{x * W:.1f}" cy="{y * H:.1f}" r="{size + 0.6:.2f}"/>'
        for i, (x, y, size, _, _) in enumerate(bright)
    )

    # Shooting stars: the site's two lanes (one every ~5-13 s); here two
    # streaks on a 14 s cycle, down-right at 45-90 degrees like launch().
    def streak(cls, x, y, angle_deg, length):
        rad = math.radians(angle_deg)
        dx, dy = math.cos(rad) * length, math.sin(rad) * length
        return (f'<g class="shoot {cls}"><line x1="{x:.0f}" y1="{y:.0f}" x2="{x + dx:.0f}" y2="{y + dy:.0f}" '
                f'stroke="url(#tail)" stroke-width="2" stroke-linecap="round"/></g>')

    shooting = streak("s1", 210, 40, 32, 120) + streak("s2", 860, 26, 38, 100)

    dark = variant == "dark"
    # The site fades the hero's lower half into the page ground (#08090c);
    # on GitHub dark the fade lands on the page colour instead (#0d1117).
    ground = "#0d1117"
    fade = (f'<rect width="{W}" height="{H}" fill="url(#fade)"/>' if dark else "")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">Starworks</title>
<desc id="d">{SUBTITLE}</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1" gradientTransform="rotate(0)">
<stop offset="0" stop-color="#4e4376"/><stop offset="1" stop-color="#2b5876"/>
</linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
<stop offset="0.52" stop-color="{ground}" stop-opacity="0"/>
<stop offset="0.70" stop-color="{ground}" stop-opacity="0.22"/>
<stop offset="0.85" stop-color="{ground}" stop-opacity="0.65"/>
<stop offset="1" stop-color="{ground}" stop-opacity="1"/>
</linearGradient>
<linearGradient id="tail" x1="1" y1="1" x2="0" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0.95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<filter id="glow" x="-10%" y="-40%" width="120%" height="180%">
<feGaussianBlur in="SourceAlpha" stdDeviation="11" result="b"/>
<feFlood flood-color="#fff" flood-opacity="0.3"/><feComposite in2="b" operator="in" result="g"/>
<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="{0 if dark else 14}"/></clipPath>
</defs>
<style>
@keyframes drift{{from{{transform:translateY(0)}}to{{transform:translateY({H}px)}}}}
{"".join(css)}
.drift circle{{fill:#fff}}
.tw{{fill:#fff;animation:tw 4.4s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}
.shoot{{opacity:0;animation:shoot 14s linear infinite}}
.s2{{animation-delay:7.3s}}
@keyframes shoot{{0%{{opacity:0;transform:translate(0,0)}}1%{{opacity:1}}7%{{opacity:0;transform:translate(260px,150px)}}100%{{opacity:0;transform:translate(260px,150px)}}}}
.copy{{animation:up .6s ease both}}
@keyframes up{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion: reduce){{.drift,.tw,.shoot,.copy{{animation:none}}.shoot{{opacity:0}}}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{"".join(layer_svg)}
{twinkles}
{shooting}
{fade}
<g class="copy">
<path d="{title}" fill="#fff" filter="url(#glow)"/>
<rect x="{W / 2 - 50:.0f}" y="226" width="100" height="3" fill="#fff" fill-opacity="0.8"/>
<path d="{subtitle}" fill="#fff" fill-opacity="0.9"/>
</g>
</g>
</svg>
'''
    return svg


def main():
    site, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for v in ("dark", "light"):
        for name, fn in (("hero", build), ("stack", build_stack)):
            p = out / f"{name}-{v}.svg"
            p.write_text(fn(site, v), encoding="utf-8", newline="\n")
            print(p, p.stat().st_size, "bytes")


def build_stack(site, variant):
    """The stack as the Mosaic page draws it (src/lib/components/mosaic/MosaicFlow.svelte
    + src/styles/products/mosaic.css): dark layered cards with a tinted icon mark in
    each product's tone, hairline routes with rounded elbows (Arcane's trunk forks to
    Astra and Manifold2D and runs on to Mosaic; they merge back into Mosaic; Mosaic
    drops to the standard library), and a comet of light in each product's tone on
    one timeline at the site's speed. The site's JS timeline is precomputed into CSS
    keyframes. Dark: transparent on GitHub's page; light: the same on a night panel.
    Icons: Font Awesome Free 6.5.2 solid (CC BY 4.0), the site's vendored subset."""
    fonts = Path(site) / "static/assets/vendor/fonts"
    fa_path = Path(site) / "static/assets/vendor/fontawesome-6.5.2/webfonts/fa-solid-900-subset-07976e2a84.woff2"
    inter_vf = TTFont(fonts / "UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2")
    inter = {w: instantiateVariableFont(TTFont(fonts / "UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2"), {"wght": w})
             for w in (300, 400, 600)} if "fvar" in inter_vf else {w: inter_vf for w in (300, 400, 600)}
    fa = TTFont(fa_path)
    INK, SOFT, FAINT = "#f5f5f7", "#a1a1a6", "#8e8e93"

    def left_text(font, text, size, x, baseline, fill, tracking=0.0):
        _, w = text_path(font, text, size, tracking, 0, baseline)
        d, _ = text_path(font, text, size, tracking, x + w / 2, baseline)
        return f'<path d="{d}" fill="{fill}"/>', w

    def icon(code, cx, cy, size, fill):
        gs, cmap = fa.getGlyphSet(), fa.getBestCmap()
        name = cmap[code]
        upm = fa["head"].unitsPerEm
        s = size / upm
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(gs)
        gs[name].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        ox = cx - (x0 + x1) / 2 * s
        oy = cy + (y0 + y1) / 2 * s
        gs[name].draw(TransformPen(pen, (s, 0, 0, -s, ox, oy)))
        return f'<path d="{pen.getCommands()}" fill="{fill}"/>'

    # ---- layout: the site's 880 px column, row-gap 76, pair column-gap 72 ----
    PAD = 40
    COL = 880
    sw = COL + 2 * PAD
    gap_row, gap_col = 76, 72
    tone = {"arcane": (155, 109, 214), "astra": (46, 155, 214), "manifold": (240, 70, 79),
            "mosaic": (217, 164, 65), "base": (161, 161, 166)}
    rgb = lambda t, a=1: f"rgba({t[0]},{t[1]},{t[2]},{a})"
    y = PAD
    top = dict(x=PAD, y=y, w=COL, h=114); y += top["h"] + gap_row
    mid_w = (COL - gap_col) / 2
    left = dict(x=PAD, y=y, w=mid_w, h=118)
    right = dict(x=PAD + mid_w + gap_col, y=y, w=mid_w, h=118); y += left["h"] + gap_row
    core = dict(x=PAD, y=y, w=COL, h=118); y += core["h"] + gap_row
    base = dict(x=PAD, y=y, w=COL, h=68); y += base["h"]
    sh = y + PAD
    for b in (top, left, right, core, base):
        b["cx"] = b["x"] + b["w"] / 2

    # ---- routes (MosaicFlow.measure) ----
    R = 16

    def elbow(x1, y1, m, x2, y2):
        if abs(x2 - x1) < 1:
            return f"M{x1:.1f} {y1:.1f}V{y2:.1f}", y2 - y1
        s = 1 if x2 > x1 else -1
        r = min(R, abs(x2 - x1) / 2, m - y1, y2 - m)
        d = (f"M{x1:.1f} {y1:.1f}V{m - r:.1f}Q{x1:.1f} {m:.1f} {x1 + s * r:.1f} {m:.1f}"
             f"H{x2 - s * r:.1f}Q{x2:.1f} {m:.1f} {x2:.1f} {m + r:.1f}V{y2:.1f}")
        quarter = 1.1478 * r  # a quadratic quarter-elbow's arc length (r * ~1.1478)
        length = (m - r - y1) + 2 * quarter + (abs(x2 - x1) - 2 * r) + (y2 - m - r)
        return d, length

    tx, ty = top["cx"], top["y"] + top["h"]
    fork = (ty + left["y"]) / 2
    merge = (left["y"] + left["h"] + core["y"]) / 2
    routes = [
        (*elbow(tx, ty, fork, left["cx"], left["y"]), "arcane", [], None),
        (*elbow(tx, ty, fork, right["cx"], right["y"]), "arcane", [], None),
        (f"M{tx:.1f} {ty:.1f}V{core['y']:.1f}", core["y"] - ty, "arcane", [], [3, 4]),
        (*elbow(left["cx"], left["y"] + left["h"], merge, core["cx"], core["y"]), "astra", [0], None),
        (*elbow(right["cx"], right["y"] + right["h"], merge, core["cx"], core["y"]), "manifold", [1], None),
        (f"M{core['cx']:.1f} {core['y'] + core['h']:.1f}V{base['y']:.1f}", base["y"] - core["y"] - core["h"], "mosaic", [2, 3, 4], None),
    ]
    # ---- timeline (MosaicFlow.timeline): SPEED px/s, THROUGH s crossing a card, REST s between journeys ----
    SPEED, THROUGH, REST = 240, 0.3, 1.4
    COMET = [(70, 2, 0.22), (34, 2, 0.5), (9, 2.6, 1.0)]  # tail .. head: (len, width, alpha)
    start, end = {}, {}
    for pss in (0, 1):
        for i, (_, L, _, after, arrive) in enumerate(routes):
            if pss == 0 and (arrive or any(routes[k][4] for k in after)):
                continue  # the JS computes these in pass 0 as NaN and fixes them in pass 1
            if pss == 1 and not arrive and not any(routes[k][4] for k in after):
                continue
            start[i] = (max(end[k] for k in after) + THROUGH) if after else 0.0
            end[i] = max(end[k] for k in arrive) if arrive else start[i] + L / SPEED
    period = max(end.values()) + REST
    tail = COMET[0][0]

    css, comets = [], []
    pct = lambda t: f"{max(0.0, min(100.0, 100 * t / period)):.3f}%"
    for i, (d, L, who, _, _) in enumerate(routes):
        s0, e0 = start[i], end[i]
        dur = e0 - s0
        e_tail = e0 + dur * tail / L  # the tail slides on into the card
        fade_in = s0 + dur / 6
        fade_out = e_tail - dur / 6
        layers = []
        for j, (D, wdt, alpha) in enumerate(COMET):
            name = f"c{i}{j}"
            css.append(
                f"@keyframes {name}{{0%,{pct(s0)}{{stroke-dashoffset:{D}px;opacity:0;animation-timing-function:cubic-bezier(.455,.03,.515,.955)}}"
                f"{pct(fade_in)}{{opacity:{alpha}}}"
                f"{pct(e0)}{{stroke-dashoffset:{D - L:.1f}px;animation-timing-function:linear}}"
                f"{pct(fade_out)}{{opacity:{alpha}}}"
                f"{pct(e_tail)},100%{{stroke-dashoffset:{D - L - tail:.1f}px;opacity:0}}}}"
                f".{name}{{stroke-dasharray:{D} {L + D + 200:.0f};animation:{name} {period:.3f}s linear infinite}}")
            glow = ' filter="url(#glow-%s)"' % who if j == len(COMET) - 1 else ""
            layers.append(f'<path class="{name}" d="{d}" stroke="{rgb(tone[who])}" stroke-width="{wdt}" opacity="0"{glow}/>')
        comets.append("".join(layers))

    # ---- cards (mosaic.css) ----
    def card(b, who, title, lines, title_size, tclass="", chevron=True, core_card=False):
        t = tone[who]
        g0, g1 = ("#2d2d31", "#1f1f23") if core_card else ("#242427", "#1b1b1e")
        gid = f"g-{who}"
        out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{g0}"/><stop offset="1" stop-color="{g1}"/></linearGradient>']
        x, yy, w, h = b["x"], b["y"], b["w"], b["h"]
        body = []
        if core_card:  # the gold halo: 0 0 70px -24px rgba(tone,.3)
            body.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" rx="22" fill="{rgb(t, 0.5)}" filter="url(#halo)"/>')
        body.append(f'<rect x="{x}" y="{yy + 18}" width="{w}" height="{h}" rx="22" fill="#000" fill-opacity="0.55" filter="url(#drop)"/>')
        body.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" rx="22" fill="url(#{gid})"/>')
        ring = rgb(t, 0.3) if core_card else "rgba(255,255,255,0.05)"
        body.append(f'<rect x="{x + 0.5}" y="{yy + 0.5}" width="{w - 1}" height="{h - 1}" rx="21.5" fill="none" stroke="{ring}"/>')
        body.append(f'<path d="M{x + 22} {yy + 1}H{x + w - 22}" stroke="#fff" stroke-opacity="{0.1 if core_card else 0.07}"/>')
        padx = 34 if who in ("arcane", "mosaic") else 28
        mx, my = x + padx, yy + h / 2 - 22
        body.append(f'<rect x="{mx}" y="{my}" width="44" height="44" rx="12" fill="{rgb(t, 0.13)}" stroke="{rgb(t, 0.26)}"/>')
        body.append(icon({"arcane": 0xF1B2, "astra": 0xF005, "manifold": 0xF5CB, "mosaic": 0xF84C}[who], mx + 22, my + 22, 18, rgb(t)))
        tx0 = mx + 44 + 18
        n_lines = len(lines)
        block = title_size * 1.25 + 4 + n_lines * 14 * 1.45
        top_y = yy + h / 2 - block / 2
        p, _ = left_text(inter[600], title, title_size, tx0, top_y + title_size * 0.98, INK, -0.01)
        body.append(p)
        ly = top_y + title_size * 1.25 + 4 + 14 * 1.05
        for line in lines:
            p, _ = left_text(inter[400], line, 14, tx0, ly, SOFT)
            body.append(p)
            ly += 14 * 1.45
        if chevron:
            cv, cw = text_path(inter[300], "›", 26, 0, 0, 0)
            p, _ = left_text(inter[300], "›", 26, x + w - padx - cw, yy + h / 2 + 9, FAINT)
            body.append(p)
        return out, body

    defs, cards = [], []
    for args in (
        (top, "arcane", "Arcane", ["The engine. Its world runs on Astra, its physics on Manifold2D."], 24),
        (left, "astra", "Astra", ["The ECS. Archetype storage,", "compile-time queries."], 19),
        (right, "manifold", "Manifold2D", ["2D physics. Deterministic rigid", "bodies."], 19),
    ):
        d_, b_ = card(*args)
        defs += d_
        cards += b_
    d_, b_ = card(core, "mosaic", "Mosaic", ["Platform · Jobs · Log · Assert · SIMD · Bits · FunctionRef"], 26,
                  chevron=False, core_card=True)
    defs += d_
    cards += b_
    # the base: a ghost card, centred mark + text
    bt = tone["base"]
    cards.append(f'<rect x="{base["x"] + 0.5}" y="{base["y"] + 0.5}" width="{base["w"] - 1}" height="{base["h"] - 1}" rx="21.5" fill="none" stroke="rgba(255,255,255,0.08)"/>')
    _, w1 = text_path(inter[600], "C++ standard library", 15, -0.01, 0, 0)
    group_w = 32 + 18 + w1
    gx = base["cx"] - group_w / 2
    gy = base["y"] + base["h"] / 2
    cards.append(f'<rect x="{gx}" y="{gy - 16}" width="32" height="32" rx="9" fill="{rgb(bt, 0.13)}" stroke="{rgb(bt, 0.26)}"/>')
    cards.append(icon(0xF121, gx + 16, gy, 13, rgb(bt)))
    p, _ = left_text(inter[600], "C++ standard library", 15, gx + 50, gy - 2, SOFT, -0.01)
    cards.append(p)
    p, _ = left_text(inter[400], "and nothing else", 12.5, gx + 50, gy + 15, FAINT)
    cards.append(p)

    dark = variant == "dark"
    panel = ""
    if not dark:
        # Light theme: the flow sits on the site's night ground, with a few static stars.
        stars = star_field(SEED + 7, 70)
        dots = "".join(f'<circle cx="{x * sw:.1f}" cy="{yy * sh:.1f}" r="{size * 0.8:.2f}" fill="#fff" fill-opacity="{b * 0.5:.2f}"/>'
                       for x, yy, size, _, b in stars)
        panel = f'<rect width="{sw}" height="{sh}" rx="16" fill="#0b0b0e"/>{dots}'

    glows = "".join(
        f'<filter id="glow-{k}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="a"/>'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        for k in ("arcane", "astra", "manifold", "mosaic"))
    route_paths = "".join(f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity="0.16" stroke-width="1.5" stroke-linejoin="round"/>'
                          for d, *_ in routes)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{sw}" height="{sh}" viewBox="0 0 {sw} {sh}" role="img" aria-labelledby="t d">
<title id="t">The Starworks stack</title>
<desc id="d">Each route runs from a product to what it is built on. Arcane builds on Astra, Manifold2D and Mosaic; Astra and Manifold2D build on Mosaic; Mosaic needs only the C++ standard library.</desc>
<!-- Icons: Font Awesome Free 6.5.2 by @fontawesome - https://fontawesome.com (CC BY 4.0). Text: Inter (SIL OFL 1.1). -->
<defs>
{"".join(defs)}
<filter id="drop" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>
<filter id="halo" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="22"/></filter>
{glows}
</defs>
<style>
{"".join(css)}
path[class^="c"]{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
@media (prefers-reduced-motion: reduce){{path[class^="c"]{{animation:none;opacity:0}}}}
</style>
{panel}
{route_paths}
{"".join(comets)}
{"".join(cards)}
</svg>
'''


if __name__ == "__main__":
    main()

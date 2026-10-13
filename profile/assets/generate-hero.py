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
    """The stack diagram: Arcane on Astra + Manifold2D on Mosaic. Arcane's card
    wears the hero gradient; the libraries are outlined cards in the site's
    accent (#b3a6ff dark / #5b4d9e light). Static -- no animation."""
    fonts = Path(site) / "static/assets/vendor/fonts"
    mono = TTFont(fonts / "i7dMIFZifjKcF5UAWdDRaPpZUFWaHg.woff2")
    inter = TTFont(fonts / "UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2")
    if "fvar" in inter:
        inter = instantiateVariableFont(inter, {"wght": 400})
    dark = variant == "dark"
    ink = "#e6edf3" if dark else "#1f2328"
    soft = "#9198a1" if dark else "#59636e"
    accent = "#b3a6ff" if dark else "#5b4d9e"
    card = "rgba(179,166,255,0.07)" if dark else "rgba(91,77,158,0.05)"
    sw, sh = 1280, 380

    def label(cx, top, name, sub, name_fill, sub_fill):
        n, _ = text_path(mono, name, 30, 0.06, cx, top + 46)
        s, _ = text_path(inter, sub, 17, 0.01, cx, top + 76)
        return f'<path d="{n}" fill="{name_fill}"/><path d="{s}" fill="{sub_fill}"/>'

    parts = []
    # Arcane (top), hero gradient.
    ax, ay, aw, ah = 340, 16, 600, 100
    parts.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="14" fill="url(#hero)"/>')
    parts.append(label(sw / 2, ay, "ARCANE", "game engine + editor", "#fff", "rgba(255,255,255,0.82)"))
    # Libraries (middle).
    lib_y, lib_w, lib_h = 146, 380, 100
    libs = [(240, "ASTRA", "entity component system"), (660, "MANIFOLD2D", "deterministic 2D physics")]
    for x, name, sub in libs:
        parts.append(f'<rect x="{x}" y="{lib_y}" width="{lib_w}" height="{lib_h}" rx="14" fill="{card}" stroke="{accent}" stroke-opacity="0.55" stroke-width="1.5"/>')
        parts.append(label(x + lib_w / 2, lib_y, name, sub, ink, soft))
    # Mosaic (bottom).
    mx, my, mw, mh = 340, 276, 600, 100
    parts.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="14" fill="{card}" stroke="{accent}" stroke-opacity="0.55" stroke-width="1.5" stroke-dasharray="6 5"/>')
    parts.append(label(sw / 2, my, "MOSAIC", "zero-dependency foundation", ink, soft))
    # Connectors: each layer builds on the one below (arrow points up).
    def arrow(x, y1, y2):
        return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 + 7}" stroke="{accent}" stroke-width="2" stroke-opacity="0.8"/>'
                f'<path d="M{x - 6} {y2 + 9} L{x} {y2} L{x + 6} {y2 + 9} Z" fill="{accent}"/>')
    for x, _, _ in libs:
        cx = x + lib_w / 2
        parts.append(arrow(cx, lib_y, ay + ah))
        parts.append(arrow(cx, my, lib_y + lib_h))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{sw}" height="{sh + 8}" viewBox="0 0 {sw} {sh + 8}" role="img" aria-labelledby="t d">
<title id="t">The Starworks stack</title>
<desc id="d">Arcane, the game engine and editor, builds on Astra (entity component system) and Manifold2D (deterministic 2D physics), which are usable on their own and both build on Mosaic, the zero-dependency foundation.</desc>
<defs><linearGradient id="hero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4e4376"/><stop offset="1" stop-color="#2b5876"/></linearGradient></defs>
{"".join(parts)}
</svg>
'''


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
web3Diagrams.py  →  generates web3-arch-web20.svg  and  web3-arch-web30.svg

Run:
    python3 docs/web3Diagrams.py
"""
import base64
from pathlib import Path

OUT_DIR = Path(__file__).parent

def _png_data_uri(filename):
    data = base64.b64encode((OUT_DIR / filename).read_bytes()).decode()
    return f"data:image/png;base64,{data}"

_THINKER_URI = _png_data_uri("iconThinker.png")


# ── shared helpers (same style as lifeTrackerDiagram.py) ──────────────────────

def _attrs(d):
    return "".join(f' {k}="{v}"' for k, v in d.items())

def tag(name, attrs, content=None):
    a = _attrs(attrs)
    if content is None:
        return f"<{name}{a}/>"
    return f"<{name}{a}>{content}</{name}>"

def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1.5, filt=None, opacity=None):
    a = {"x": x, "y": y, "width": w, "height": h, "fill": fill, "rx": rx}
    if stroke:   a["stroke"] = stroke; a["stroke-width"] = sw
    if filt:     a["filter"]  = f"url(#{filt})"
    if opacity is not None: a["opacity"] = opacity
    return tag("rect", a)

def line(x1, y1, x2, y2, stroke="#64748b", sw=1.8, dash=None, marker=None):
    a = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
         "stroke": stroke, "stroke-width": sw}
    if dash:   a["stroke-dasharray"] = dash
    if marker: a["marker-end"] = f"url(#{marker})"
    return tag("line", a)

def circle(cx, cy, r, fill, stroke=None, sw=2, filt=None):
    a = {"cx": cx, "cy": cy, "r": r, "fill": fill}
    if stroke: a["stroke"] = stroke; a["stroke-width"] = sw
    if filt:   a["filter"] = f"url(#{filt})"
    return tag("circle", a)

def text(x, y, msg, size, fill, anchor="middle", bold=False, italic=False, spacing=None):
    a = {"x": x, "y": y, "text-anchor": anchor, "font-size": size, "fill": fill}
    if bold:    a["font-weight"]  = "700"
    if italic:  a["font-style"]   = "italic"
    if spacing: a["letter-spacing"] = spacing
    return tag("text", a, content=msg)

def sep_line(x1, y, x2, stroke="#a7f3d0", sw=1):
    return tag("line", {"x1": x1, "y1": y, "x2": x2, "y2": y,
                        "stroke": stroke, "stroke-width": sw})

def arrow_marker(mid, color):
    poly = tag("polygon", {"points": "0 0,9 3,0 6", "fill": color})
    return (f'<marker id="{mid}" markerWidth="9" markerHeight="6" '
            f'refX="8" refY="3" orient="auto">{poly}</marker>')

def arrow_marker_rev(mid, color):
    poly = tag("polygon", {"points": "9 0,0 3,9 6", "fill": color})
    return (f'<marker id="{mid}" markerWidth="9" markerHeight="6" '
            f'refX="1" refY="3" orient="auto">{poly}</marker>')

def bidir_line(x1, y1, x2, y2, stroke="#64748b", sw=1.8):
    a = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
         "stroke": stroke, "stroke-width": sw,
         "marker-start": "url(#arr-rev)", "marker-end": "url(#arr)"}
    return tag("line", a)

def drop_shadow(fid, dx=0, dy=2, std=3, color="#0f172a", opacity="0.08",
                px="-5%", py="-5%", pw="115%", ph="130%"):
    inner = (f'<feDropShadow dx="{dx}" dy="{dy}" stdDeviation="{std}" '
             f'flood-color="{color}" flood-opacity="{opacity}"/>')
    return (f'<filter id="{fid}" x="{px}" y="{py}" width="{pw}" height="{ph}">'
            f'{inner}</filter>')

def svg_wrap(w, h, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%"\n'
            f'     font-family="system-ui,-apple-system,sans-serif">\n'
            f'{content}\n</svg>')


# ══════════════════════════════════════════════════════════════════════════════
# WEB 2.0 DIAGRAM  —  upside-down triangle: Principal · World → [interface|Javier]
# ══════════════════════════════════════════════════════════════════════════════

def thinker_icon(x, y, h):
    """PNG thinker icon with top-left at (x,y), height h; width auto-scaled (208:316)."""
    w = round(h * 208 / 316)
    return f'<image href="{_THINKER_URI}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


W20, H20 = 500, 428

# two top-tier actors (closer together)
PRINC_CX, PRINC_CY, PRINC_R = 175, 94, 23
WORLD_CX, WORLD_CY, WORLD_R = 325, 94, 23

# Javier box: chips (top) · identity+thinker (mid) · AI/KB (mid) · agents (bottom)
JAV_X, JAV_Y, JAV_W, JAV_H = 48, 158, 404, 140
JAV_CX  = JAV_X + JAV_W // 2   # 250
JAV_BOT = JAV_Y + JAV_H        # 298

# Principal Data box
DATA_X, DATA_Y, DATA_W, DATA_H = 28, 316, 444, 62
DATA_CX = DATA_X + DATA_W // 2  # 250
DATA_BOT = DATA_Y + DATA_H      # 378

# interface channel chips  (icon, label, bg, border)
_CHANNELS = [
    ("📞", "Twilio",  "#fff7ed", "#ea580c"),
    ("📱", "iPhone",  "#eff6ff", "#3b82f6"),
    ("💻", "Web UI",  "#f0fdf4", "#16a34a"),
]

# discipline agent boxes (inside Javier bottom)
_AGENTS = [
    ("🏠", "houseAgent",   "#f0fdf4", "#16a34a"),
    ("🏥", "medicalAgent", "#eff6ff", "#3b82f6"),
    ("💰", "moneyAgent",   "#fefce8", "#ca8a04"),
    ("📄", "estateAgent",  "#fdf4ff", "#9333ea"),
]


def build_web20():
    # ── Javier internals ──
    CH_Y   = JAV_Y + 4         # 162
    CH_H   = 22
    SEP1_Y = CH_Y + CH_H + 3  # 187
    ID_ICN = SEP1_Y + 15      # thinker center-y: 202
    SEP2_Y = SEP1_Y + 42      # 229
    AI_Y   = SEP2_Y + 3       # 232
    AI_H   = 26
    SEP3_Y = AI_Y + AI_H + 2  # 260
    AG_Y   = SEP3_Y + 3       # 263
    AG_H   = 30

    ag_w = (JAV_W - 5 * 4) // 4   # 96px each
    ag_x_starts = [JAV_X + 4 + i*(ag_w + 4) for i in range(4)]
    ag_centers  = [x + ag_w // 2 for x in ag_x_starts]  # [100, 200, 300, 400]

    parts = [
        "\n".join([
            "<defs>",
            f"  {arrow_marker('arr', '#64748b')}",
            f"  {arrow_marker_rev('arr-rev', '#64748b')}",
            f"  {drop_shadow('shadow')}",
            "</defs>",
        ]),
        rect(0, 0, W20, H20, "#f8fafc", rx=12),
        rect(0, 0, W20, 48, "#1e293b", rx=12),
        rect(0, 36, W20, 12, "#1e293b"),
        text(W20//2, 22, "Web 2.0  —  Javier in Others' Platforms",
             13, "#f1f5f9", bold=True, spacing="0.3"),
        text(W20//2, 39, "BirthPlan · current state", 9, "#94a3b8"),
        # ── triangle skeleton ──
        line(PRINC_CX+PRINC_R, PRINC_CY, WORLD_CX-WORLD_R, WORLD_CY,
             stroke="#cbd5e1", sw=1.2, dash="5,4"),
        bidir_line(PRINC_CX, PRINC_CY+PRINC_R, 210, JAV_Y),
        bidir_line(WORLD_CX, WORLD_CY+WORLD_R, 290, JAV_Y),
        # ── actors ──
        circle(PRINC_CX, PRINC_CY, PRINC_R, "#dbeafe", stroke="#3b82f6", sw=2, filt="shadow"),
        text(PRINC_CX, PRINC_CY+7,           "🧑", 20, "#000"),
        text(PRINC_CX, PRINC_CY+PRINC_R+16, "Principal", 10, "#1e40af", bold=True),
        circle(WORLD_CX, WORLD_CY, WORLD_R, "#dcfce7", stroke="#16a34a", sw=2, filt="shadow"),
        text(WORLD_CX, WORLD_CY+7,           "🌐", 20, "#000"),
        text(WORLD_CX, WORLD_CY+WORLD_R+16, "The World", 10, "#15803d", bold=True),
        # ── Javier outer box ──
        rect(JAV_X, JAV_Y, JAV_W, JAV_H, "#ccfbf1", rx=9,
             stroke="#0f766e", sw=2.5, filt="shadow"),
    ]

    # interface chips (slim, inside Javier top)
    ch_x = JAV_X + 6
    for icon, label, bg, border in _CHANNELS:
        cw = 126
        ccx = ch_x + cw // 2
        parts += [
            rect(ch_x, CH_Y, cw, CH_H, bg, rx=3, stroke=border, sw=0.8),
            text(ccx, CH_Y+9,  icon,  8, "#000"),
            text(ccx, CH_Y+18, label, 6.5, border, bold=True),
        ]
        ch_x += cw + 5

    parts += [
        sep_line(JAV_X+10, SEP1_Y, JAV_X+JAV_W-10, "#a7f3d0"),
        # thinker PNG icon + Javier identity — group centered in J box
        # icon h=24 matches two-line text block; w≈16 (208:316 ratio)
        thinker_icon(x=JAV_CX - 56, y=ID_ICN - 10, h=24),
        text(JAV_CX - 34, ID_ICN + 2,  "Javier", 12, "#064e3b", bold=True, anchor="start"),
        text(JAV_CX - 34, ID_ICN + 16, "Personal Assistant", 8, "#065f46", anchor="start"),
        sep_line(JAV_X+10, SEP2_Y, JAV_X+JAV_W-10, "#a7f3d0"),
        # AI/KB strip
        rect(JAV_X+3, AI_Y, JAV_W-6, AI_H, "#0d9488", rx=5),
        text(JAV_CX, AI_Y + AI_H//2 + 5, "🧠  AI · Knowledge Base", 9, "#ccfbf1", bold=True),
        sep_line(JAV_X+10, SEP3_Y, JAV_X+JAV_W-10, "#a7f3d0"),
    ]

    # agent boxes inside Javier
    for i, (icon, label, bg, border) in enumerate(_AGENTS):
        ax = ag_x_starts[i]
        acx = ag_centers[i]
        parts += [
            rect(ax, AG_Y, ag_w, AG_H, bg, rx=4, stroke=border, sw=1),
            text(acx, AG_Y+11, icon,  10, "#000"),
            text(acx, AG_Y+24, label,  6.5, border, bold=True),
        ]

    # 1 line per agent piercing through Javier bottom → data box top
    for acx in ag_centers:
        parts.append(
            line(acx, AG_Y+AG_H, acx, DATA_Y, stroke="#94a3b8", sw=1.2, marker="arr")
        )

    parts += [
        # Principal Data box (no label above)
        rect(DATA_X, DATA_Y, DATA_W, DATA_H, "#fffbeb", rx=8,
             stroke="#d97706", sw=1.5, filt="shadow"),
        # Google Drive sub-section
        rect(DATA_X+4, DATA_Y+4, 294, DATA_H-8, "#fff7ed", rx=5, stroke="#fbbf24", sw=1),
        text(DATA_X+151, DATA_Y+20, "📁  Google Drive", 10, "#92400e", bold=True),
        text(DATA_X+151, DATA_Y+36, "🏠 house  ·  🏥 medical  ·  💰 finance  ·  …", 8.5, "#b45309"),
        text(DATA_X+151, DATA_Y+50, "Google owns · can read · can go down", 7.5, "#d97706"),
        # Gmail sub-section
        rect(DATA_X+302, DATA_Y+4, 138, DATA_H-8, "#fff7ed", rx=5, stroke="#fbbf24", sw=1),
        text(DATA_X+371, DATA_Y+20, "✉  Gmail", 10, "#92400e", bold=True),
        text(DATA_X+371, DATA_Y+36, "email · comm", 8.5, "#b45309"),
        text(DATA_X+371, DATA_Y+50, "Google reads", 7.5, "#d97706"),
        # label + warning BELOW data box
        text(DATA_CX, DATA_BOT+13,
             "principal data  (platforms own it ⚠)", 8, "#b45309", italic=True),
        text(DATA_CX, DATA_BOT+27,
             "⚠  Principal is a user of these platforms — not an owner",
             8, "#dc2626", bold=True),
        text(DATA_CX, DATA_BOT+39,
             "any platform can read the data · go dark · sell to a competitor",
             7.5, "#dc2626"),
    ]

    return svg_wrap(W20, H20, "\n".join(parts))


# ══════════════════════════════════════════════════════════════════════════════
# WEB 3.0 DIAGRAM  —  "Javier as a Sovereign Agent"
# ══════════════════════════════════════════════════════════════════════════════
W30, H30 = 740, 390

# Principal DID box
FK_X, FK_Y, FK_W, FK_H = 18, 156, 158, 100
FK_CX = FK_X + FK_W // 2     # 97

# Javier box
JV_X, JV_Y, JV_W, JV_H = 238, 112, 162, 190
JV_CX = JV_X + JV_W // 2     # 319
JV_RX = JV_X + JV_W          # 400 — right edge

# Branch boxes (right side)
BR_X, BR_W = 480, 234
BR_CX = BR_X + BR_W // 2     # 597

# Each branch: box geometry, colors, arrow source y on Javier, lines of text
BRANCHES = [
    dict(
        y=58, h=100, icon="🗄", label="SOLID Pod",
        bg="#dcfce7", border="#16a34a", title_c="#15803d",
        arr_id="arr-green", arr_color="#059669",
        from_y=JV_Y+46, to_y=108,
        lines=[
            ("Principal's personal data store",           "#166534", 10),
            ("Encrypted · Self-hosted",                "#15803d",  9),
            ("Apps request access · Principal revokes",    "#15803d",  9),
            ("RecordAgent API unchanged — swap store", "#16a34a", 8.5),
        ],
    ),
    dict(
        y=173, h=84, icon="🤝", label="Agent Mesh  (A2A)",
        bg="#e0f2fe", border="#0284c7", title_c="#0369a1",
        arr_id="arr-sky", arr_color="#0284c7",
        from_y=JV_Y+JV_H//2, to_y=215,
        lines=[
            ("Doctor · Attorney · Contractor agents",  "#075985", 10),
            ("Agent2Agent protocol · DID-auth",         "#0284c7",  9),
            ("Javier books, negotiates, delegates",     "#0284c7",  9),
        ],
    ),
    dict(
        y=271, h=88, icon="🔒", label="ZK Proofs",
        bg="#f3e8ff", border="#7c3aed", title_c="#6b21a8",
        arr_id="arr-purple", arr_color="#7c3aed",
        from_y=JV_Y+JV_H-46, to_y=315,
        lines=[
            ("Share proof, not raw data",                   "#581c87", 10),
            ('"A1C &lt; 7.5" — insurer sees proof only',    "#7c3aed",  9),
            ("HIPAA-compatible · privacy by design",         "#7c3aed",  9),
        ],
    ),
]


def web30_defs():
    parts = ["<defs>",
             f"  {arrow_marker('arr-blue', '#1d4ed8')}"]
    for b in BRANCHES:
        parts.append(f"  {arrow_marker(b['arr_id'], b['arr_color'])}")
    parts += [
        f"  {drop_shadow('shadow')}",
        f"  {drop_shadow('glow', dx=0, dy=0, std=6, color='#059669', opacity='0.35', px='-12%', py='-12%', pw='128%', ph='134%')}",
        "</defs>",
    ]
    return "\n".join(parts)


def web30_header():
    return "\n".join([
        rect(0, 0, W30, 56, "#064e3b", rx=12),
        rect(0, 44, W30, 12, "#064e3b"),
        text(W30//2, 26, "Web 3.0  —  Javier as a Sovereign Agent",
             14, "#d1fae5", bold=True, spacing="0.3"),
        text(W30//2, 44, "TrustedPlan+ · target state", 10, "#6ee7b7"),
    ])


def web30_Principal():
    cx, mid_y = FK_CX, FK_Y + FK_H // 2
    auth_label_x = (FK_X + FK_W + JV_X) // 2
    return "\n".join([
        rect(FK_X, FK_Y, FK_W, FK_H, "#dbeafe", rx=9, stroke="#1d4ed8", sw=2, filt="shadow"),
        text(cx, FK_Y+28, "🔑", 24, "#000"),
        text(cx, FK_Y+52, "Principal", 13, "#1e40af", bold=True),
        text(cx, FK_Y+68, "did:key:z6MkPrincipal…", 8.5, "#1d4ed8"),
        text(cx, FK_Y+82, "self-sovereign identity", 8.5, "#3b82f6"),
        text(cx, FK_Y+94, "cryptographic · no middleman", 8, "#60a5fa"),
        # arrow Principal → Javier
        line(FK_X+FK_W, mid_y, JV_X, JV_Y+JV_H//2, stroke="#1d4ed8", sw=2.2, marker="arr-blue"),
        text(auth_label_x, mid_y-8, "authorizes", 8.5, "#1d4ed8", italic=True),
    ])


def web30_javier():
    cx, sep_y = JV_CX, JV_Y+98
    return "\n".join([
        rect(JV_X, JV_Y, JV_W, JV_H, "#d1fae5", rx=11, stroke="#059669", sw=3, filt="glow"),
        text(cx, JV_Y+38, "🛡", 30, "#000"),
        text(cx, JV_Y+70, "Javier", 16, "#064e3b", bold=True),
        text(cx, JV_Y+88, "Sovereign Agent", 10, "#047857", bold=True),
        sep_line(JV_X+18, sep_y, JV_X+JV_W-18),
        text(cx, JV_Y+112, "did:key:z6MkJavier…", 8.5, "#065f46"),
        text(cx, JV_Y+127, "Principal's authorized actor", 8.5, "#065f46"),
        text(cx, JV_Y+142, "holds keys · acts on Principal's", 8.5, "#065f46"),
        text(cx, JV_Y+157, "behalf in the world", 8.5, "#065f46"),
        text(cx, JV_Y+173, "A2A endpoint · VC authority", 8, "#6ee7b7"),
        text(cx, JV_Y+185, "pod ACL manager", 8, "#6ee7b7"),
    ])


def web30_branches():
    parts = []
    for b in BRANCHES:
        title_y = b["y"] + 24
        # arrow from Javier right edge
        parts.append(line(JV_RX, b["from_y"], BR_X, b["to_y"],
                          stroke=b["arr_color"], sw=2.2, marker=b["arr_id"]))
        # box
        parts.append(rect(BR_X, b["y"], BR_W, b["h"],
                          b["bg"], rx=8, stroke=b["border"], sw=2, filt="shadow"))
        # title with icon
        parts.append(text(BR_CX, title_y, f'{b["icon"]}  {b["label"]}',
                          12, b["title_c"], bold=True))
        # detail lines
        line_y = title_y + 20
        for msg, fill, sz in b["lines"]:
            parts.append(text(BR_CX, line_y, msg, sz, fill))
            line_y += int(sz) + 5
    return "\n".join(parts)


def web30_success():
    return "\n".join([
        rect(28, H30-22, 684, 14, "#86efac", rx=6, opacity=0.5),
        text(W30//2, H30-11,
             "✓  Principal owns every layer — identity · data · communication · privacy",
             9.5, "#15803d", bold=True),
    ])


def build_web30():
    sections = [
        web30_defs(),
        rect(0, 0, W30, H30, "#f0fdf4", rx=12),
        "<!-- header -->", web30_header(),
        "<!-- Principal DID -->", web30_Principal(),
        "<!-- Javier sovereign agent -->", web30_javier(),
        "<!-- branch arrows + boxes -->", web30_branches(),
        "<!-- success banner -->", web30_success(),
    ]
    return svg_wrap(W30, H30, "\n".join(sections))


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for name, build_fn in [
        ("web3-arch-web20.svg", build_web20),
        ("web3-arch-web30.svg", build_web30),
    ]:
        out = OUT_DIR / name
        svg = build_fn()
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out}  ({len(svg):,} bytes)")

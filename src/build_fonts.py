#!/usr/bin/env fontforge
"""Build TU Dating fonts from the SVG glyphs in this repository.

Run from the repository root with:
    fontforge -script src/build_fonts.py
"""

from pathlib import Path
import re

import fontforge


ROOT = Path(__file__).resolve().parent.parent
SVG_ROOT = ROOT / "svg"
OUTPUT_ROOT = ROOT / "fonts"
UPM = 1000

# Filename -> Unicode character.
GLYPHS = {
    "0.svg": "0",
    "1.svg": "1",
    "2.svg": "2",
    "3.svg": "3",
    "4.svg": "4",
    "5.svg": "5",
    "6.svg": "6",
    "7.svg": "7",
    "8.svg": "8",
    "9.svg": "9",
    "dot.svg": ".",
    "hyphen.svg": "-",
}


def svg_width(path):
    """Read the SVG canvas width; its built-in side margins are preserved."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\bwidth\s*=\s*[\"']([0-9.]+)", text)
    return round(float(match.group(1))) if match else UPM


def add_name(font, language, name, value):
    # FontForge raises on a name that is not supported by an older build.
    # Metadata is useful but must not prevent font generation.
    try:
        font.appendSFNTName(language, name, value)
    except Exception:
        pass


def build(style_directory, postscript_name, full_name, japanese_full_name, width_class):
    source_root = SVG_ROOT / style_directory
    output_path = OUTPUT_ROOT / f"{postscript_name}.ttf"

    font = fontforge.font()
    font.encoding = "UnicodeFull"
    # FontForge requires its internal ascent + descent to equal the UPM and
    # stores the internal descent as positive. The requested signed metrics
    # are written separately to the OpenType OS/2 and hhea tables below.
    font.em = UPM
    font.ascent = 750
    font.descent = 250
    font.fontname = postscript_name
    font.familyname = "TU Dating"
    font.fullname = full_name
    font.weight = "Regular"
    font.version = "0.2.0"
    font.copyright = "Copyright © Nono Yuu. Licensed under the SIL Open Font License, Version 1.1."

    # OpenType vertical metrics and classification.
    font.hhea_ascent_add = False
    font.hhea_descent_add = False
    font.hhea_ascent = 750
    font.hhea_descent = -140
    font.hhea_linegap = 110
    font.os2_typoascent_add = False
    font.os2_typodescent_add = False
    font.os2_typoascent = 750
    font.os2_typodescent = -140
    font.os2_typolinegap = 110
    font.os2_winascent_add = False
    font.os2_windescent_add = False
    font.os2_winascent = 750
    font.os2_windescent = 140
    font.os2_capheight = 730
    font.os2_xheight = 520
    font.os2_weight = 400
    font.os2_width = width_class

    add_name(font, "English (US)", "Family", "TU Dating")
    add_name(font, "English (US)", "SubFamily", "Regular")
    add_name(font, "English (US)", "Fullname", full_name)
    add_name(font, "English (US)", "Version", "Version 0.2.0")
    add_name(font, "English (US)", "Designer", "Nono Yuu")
    add_name(font, "English (US)", "Manufacturer", "Nono Yuu")
    add_name(font, "English (US)", "License", "SIL Open Font License, Version 1.1")
    add_name(font, "English (US)", "License URL", "https://openfontlicense.org")
    add_name(font, "Japanese", "Family", "TUダッチング体")
    add_name(font, "Japanese", "Fullname", japanese_full_name)

    for filename, character in GLYPHS.items():
        svg_path = source_root / filename
        if not svg_path.is_file():
            raise FileNotFoundError(f"Missing glyph SVG: {svg_path}")

        glyph = font.createChar(ord(character))
        glyph.importOutlines(str(svg_path))
        glyph.correctDirection()
        glyph.removeOverlap()
        glyph.round()

        # Keep the SVG's own canvas and side margins, while adding no extra
        # spacing outside that canvas.
        glyph.width = svg_width(svg_path)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    font.generate(str(output_path), flags=["opentype"])
    font.close()
    print(f"Generated {output_path}")


build(
    "regular",
    "TUDating-Regular",
    "TU Dating Regular",
    "TUダッチング体 Regular",
    5,
)
build(
    "compressed_regular",
    "TUDating-CompressedRegular",
    "TU Dating Compressed Regular",
    "TUダッチング体 Compressed Regular",
    2,
)

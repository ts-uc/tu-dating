#!/usr/bin/env fontforge
"""Build TU Dating fonts from the SVG glyphs in this repository.

Run from the repository root with:
    fontforge -script src/build_fonts.py
"""

from pathlib import Path
from xml.etree import ElementTree

import fontforge


ROOT = Path(__file__).resolve().parent.parent
SVG_ROOT = ROOT / "svg"
OUTPUT_ROOT = ROOT / "fonts"
UPM = 1000
DIGIT_GROUP_SPACE_CODEPOINT = 0xE000
DIGIT_GROUP_SPACE_WIDTH = 50

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
    "space.svg": " ",
}


def svg_width(path):
    """Read the SVG canvas width; its built-in side margins are preserved."""
    root = ElementTree.parse(path).getroot()
    width = root.get("width")
    if width is None:
        raise ValueError(f"SVG has no width: {path}")

    try:
        value = round(float(width))
    except ValueError as error:
        raise ValueError(f"SVG width must be unitless font units: {path}: {width}") from error

    if value <= 0:
        raise ValueError(f"SVG width must be positive: {path}: {width}")
    return value


def add_name(font, language, name, value):
    font.appendSFNTName(language, name, value)


def add_notdef(font, width):
    """Add a visible .notdef glyph whose width fits the font's metrics."""
    glyph = font.createChar(-1, ".notdef")
    outer_margin = max(round(width * 0.1), 20)
    inner_margin = max(round(width * 0.2), outer_margin + 20)

    pen = glyph.glyphPen()
    pen.moveTo((outer_margin, 0))
    pen.lineTo((width - outer_margin, 0))
    pen.lineTo((width - outer_margin, 700))
    pen.lineTo((outer_margin, 700))
    pen.closePath()
    pen.moveTo((inner_margin, 50))
    pen.lineTo((width - inner_margin, 50))
    pen.lineTo((width - inner_margin, 650))
    pen.lineTo((inner_margin, 650))
    pen.closePath()
    pen = None
    glyph.correctDirection()
    glyph.width = width


def build(
    style_directory,
    postscript_name,
    subfamily,
    full_name,
    japanese_full_name,
    width_class,
):
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
    font.os2_use_typo_metrics = True
    font.os2_vendor = "NYUU"

    add_name(font, "English (US)", "Family", "TU Dating")
    add_name(font, "English (US)", "SubFamily", subfamily)
    add_name(font, "English (US)", "Preferred Family", "TU Dating")
    add_name(font, "English (US)", "Preferred Styles", subfamily)
    add_name(font, "English (US)", "Fullname", full_name)
    add_name(font, "English (US)", "Version", "Version 0.2.0")
    add_name(font, "English (US)", "Designer", "Nono Yuu")
    add_name(font, "English (US)", "Manufacturer", "Nono Yuu")
    add_name(font, "English (US)", "License", "SIL Open Font License, Version 1.1")
    add_name(font, "English (US)", "License URL", "https://openfontlicense.org")
    add_name(font, "Japanese", "Family", "TUダッチング体")
    add_name(font, "Japanese", "SubFamily", subfamily)
    add_name(font, "Japanese", "Preferred Family", "TUダッチング体")
    add_name(font, "Japanese", "Preferred Styles", subfamily)
    add_name(font, "Japanese", "Fullname", japanese_full_name)

    glyph_sources = []
    for filename, character in GLYPHS.items():
        svg_path = source_root / filename
        if not svg_path.is_file():
            raise FileNotFoundError(f"Missing glyph SVG: {svg_path}")
        glyph_sources.append((svg_path, character, svg_width(svg_path)))

    maximum_width = max(width for _, _, width in glyph_sources)
    add_notdef(font, maximum_width)
    font.createChar(-1, ".null").width = 0
    font.createChar(-1, "nonmarkingreturn").width = 0

    # Use space.svg's canvas width for both normal and non-breaking spaces.
    space_width = next(width for _, character, width in glyph_sources if character == " ")
    font.createChar(0x00A0).width = space_width

    # U+E000 is a private-use spacer for padding compressed digit groups.
    if style_directory == "compressed_regular":
        digit_group_space = font.createChar(
            DIGIT_GROUP_SPACE_CODEPOINT,
            "digitgroupspace",
        )
        digit_group_space.width = DIGIT_GROUP_SPACE_WIDTH

    for svg_path, character, advance_width in glyph_sources:
        glyph = font.createChar(ord(character))

        # A space must remain outline-free. space.svg supplies its width only;
        # the other SVG files supply both outlines and widths.
        if character != " ":
            glyph.importOutlines(str(svg_path))
            glyph.correctDirection()
            glyph.removeOverlap()
            glyph.round()

        # Keep the SVG's own canvas and side margins, while adding no extra
        # spacing outside that canvas.
        glyph.width = advance_width

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    font.generate(str(output_path), flags=["opentype"])
    font.close()
    print(f"Generated {output_path}")


def main():
    build(
        "regular",
        "TUDating-Regular",
        "Regular",
        "TU Dating Regular",
        "TUダッチング体 Regular",
        5,
    )
    build(
        "compressed_regular",
        "TUDating-CompressedRegular",
        "Compressed Regular",
        "TU Dating Compressed Regular",
        "TUダッチング体 Compressed Regular",
        2,
    )


if __name__ == "__main__":
    main()

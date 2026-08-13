# Third-party notices

## Coat of arms generator (Settlements)

The heraldry generator (`lib/data/heraldry/`) is a clean-room Dart
reimplementation of the generation algorithm and shield/ordinary/division/
charge data model from **Armoria** by Azgaar
(<https://github.com/Azgaar/Armoria>), licensed MIT. No source code was
copied; the data tables in `assets/dataset/heraldry.json` (shield shapes,
ordinaries, divisions, positions, tincture palette) are transcribed from
Armoria's `src/data/*` under that MIT license.

The 353 charge icon SVGs in `assets/charges/` are copied verbatim from
Armoria's `public/charges/`. Unlike Armoria's own code, these icons are
individually sourced (mostly from Wikimedia Commons) under a mix of
licenses set per file by their original authors — **not** uniformly
MIT/CC0. Per-file author, source, and license are recorded in
`assets/dataset/heraldry.json` under the `chargeCredits` key (also
embedded in each source SVG's `<metadata>` tag).

## Spell area-shape icons

The 8 `assets/icons/area-*.svg` glyphs (sphere, cube, cone, cylinder,
square, circle, hemisphere, line — used next to a spell's Range/Area stat,
see `lib/widgets/spell_area_shape_icon.dart`; the "wall" area shape reuses
the line glyph rather than getting its own file) are copied verbatim
from **Tabler Icons** (<https://github.com/tabler/tabler-icons>), licensed
MIT. Copyright belongs to the upstream author (Paweł Kuna); see
`assets/icons/LICENSE.tabler-icons.txt`.

## 3D dice roller

Portions of the 3D dice geometry and physics approach in
`assets/web/three-dice/` are adapted from **Obsidian-TTRPG-Community/dice-roller**
(<https://github.com/Obsidian-TTRPG-Community/dice-roller>), licensed MIT.
Copyright belongs to the upstream authors; see
`assets/web/three-dice/LICENSE.obsidian-dice-roller.txt`.

The vendored rendering and physics libraries in
`assets/web/three-dice/vendor/` are **three.js** (`three.module.js`) and
**cannon-es** (`cannon-es.js`), both MIT licensed. See
`assets/web/three-dice/LICENSE.three.txt` and
`assets/web/three-dice/LICENSE.cannon-es.txt` respectively.

The HDRI environment map lighting the dice
(`assets/web/three-dice/env/dice_studio.hdr`) is **White Chapel** from
**Poly Haven** (<https://polyhaven.com/a/white_chapel>), CC0 1.0
Universal (public domain). See
`assets/web/three-dice/LICENSE.dice_studio_hdri.txt`.

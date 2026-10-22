# License

Copyright (c) 2026 Giulio Maffei. All rights reserved.

This software, including its source code, object code, documentation, assets
and any portion thereof (the "Software"), is proprietary and confidential.

No license or right of any kind is granted to anyone, whether expressly, by
implication, by estoppel or otherwise. Without the prior written permission of
the copyright holder, no one may use, copy, modify, merge, publish, distribute,
sublicense, sell, rent, lend, reverse engineer, decompile, disassemble or
create derivative works of the Software, in whole or in part, by any means.

Access to the source code, or to a build of the Software, does not by itself
grant any right to it.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Third-party components bundled with the Software and the System Reference
Document content remain under their own licenses, listed under "Third-party
notices" below; this notice does not restrict any right those licenses grant.

---

# Third-party notices

## D&D 5e rules content (SRD 5.1 and SRD 5.2)

This work includes material taken from the System Reference Document 5.1
("SRD 5.1") by Wizards of the Coast LLC and available at
<https://dnd.wizards.com/resources/systems-reference-document>. The SRD 5.1
is licensed under the Creative Commons Attribution 4.0 International
License available at <https://creativecommons.org/licenses/by/4.0/legalcode>.

This work includes material from the System Reference Document 5.2
("SRD 5.2") by Wizards of the Coast LLC, available at
<https://www.dndbeyond.com/srd>. The SRD 5.2 is licensed under the Creative
Commons Attribution 4.0 International License, available at
<https://creativecommons.org/licenses/by/4.0/legalcode>.

The SRD datasets in `assets/dataset/` (`spells_srd`, `bestiary_srd`,
`classes_srd`, `races_srd`, `feats_srd`, `items_srd`, `rules_srd`) were
converted from the SRD 5.1 into this app's JSON format. The condition rules
text shown in Initiative (`lib/l10n/dnd_terms.dart`) is taken from the
SRD 5.2. The Italian versions of both (`*_srd_it.json` and the Italian
condition texts) are translations made for this project: they are a
modified version of that material, shared under the same CC BY 4.0 license.

Arcane Manager is unofficial fan content. It is not affiliated with,
endorsed, sponsored or approved by Wizards of the Coast. Dungeons & Dragons
and D&D are trademarks of Wizards of the Coast LLC.

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
MIT. Copyright belongs to the upstream author (Paweł Kuna); full text in
[Tabler Icons](#tabler-icons) below.

## Sidebar navigation icons

Three of the sidebar's tab icons — `party`, `items` and `generators` `.png`
in `assets/icons/` (the fill weight of `users-three`, `treasure-chest` and
`sparkle`) — are rasterized from **Phosphor Icons**
(<https://github.com/phosphor-icons/core>), licensed MIT. Copyright belongs
to Phosphor Icons; full text in [Phosphor Icons](#phosphor-icons) below.

## 3D dice roller

Portions of the 3D dice geometry and physics approach in
`assets/web/three-dice/` are adapted from **Obsidian-TTRPG-Community/dice-roller**
(<https://github.com/Obsidian-TTRPG-Community/dice-roller>), licensed MIT.
Copyright belongs to the upstream authors; see
[Obsidian dice-roller](#obsidian-dice-roller) below.

The vendored rendering and physics libraries in
`assets/web/three-dice/vendor/` are **three.js** (`three.module.js`) and
**cannon-es** (`cannon-es.js`), both MIT licensed. Full texts in [three.js](#threejs) and
[cannon-es](#cannon-es) below.

The HDRI environment map lighting the dice
(`assets/web/three-dice/env/dice_studio.hdr`) is **White Chapel** from
**Poly Haven** (<https://polyhaven.com/a/white_chapel>), CC0 1.0
Universal (public domain). See [White Chapel HDRI](#white-chapel-hdri)
below.

The impact sounds played on every die collision
(`assets/web/dice_roller/sfx/impact_01.wav`..`impact_11.wav`) are cut from
"dice_rolls_15cm" by **andresix** on freesound.org, CC0 1.0 Universal
(public domain). See [Dice impact sounds](#dice-impact-sounds) below.

## Markdown diagrams (Adventure)

The vendored diagram renderer in `assets/web/mermaid/vendor/` is
**Mermaid** (<https://github.com/mermaid-js/mermaid>), licensed MIT. Full
text in [Mermaid](#mermaid) below.

## Tavern menu font

The tavern menu card's body serif (`assets/fonts/EBGaramond-*.ttf`) is
**EB Garamond** (<https://github.com/octaviopardo/EBGaramond12>), licensed
under the SIL Open Font License 1.1. Full text in [EB Garamond](#eb-garamond)
below.

## NDI / Syphon / Spout outputs

The video and map monitors can also publish themselves as a video source
(`packages/stream_output/`):

* **Syphon** (macOS) — the server half of the Syphon framework
  (<https://github.com/Syphon/Syphon-Framework>) is compiled in from source
  under `packages/stream_output/macos/Classes/Syphon/`, licensed BSD-2-Clause.
  Full text in [Syphon](#syphon) below.
* **Spout** (Windows) — SpoutDX and its SpoutGL support files
  (<https://github.com/leadedge/Spout2>) are compiled in from source under
  `packages/stream_output/windows/spout/`, licensed BSD-2-Clause. Full text
  in [Spout](#spout) below.
* **NDI** — not bundled. The app loads the NDI runtime the user installed
  with NDI Tools (<https://ndi.video/tools>) at run time, and only offers NDI
  when it is present. NDI® is a registered trademark of Vizrt NDI AB.

---

# License texts

## Tabler Icons

```text
MIT License

Copyright (c) 2020-2026 Paweł Kuna

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Phosphor Icons

```text
MIT License

Copyright (c) 2023 Phosphor Icons

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Obsidian dice-roller

```text
Portions of the 3D dice geometry and physics approach are adapted from:

Obsidian-TTRPG-Community/dice-roller
https://github.com/Obsidian-TTRPG-Community/dice-roller

The upstream project declares the MIT license in package.json:
https://github.com/Obsidian-TTRPG-Community/dice-roller/blob/main/package.json

Copyright belongs to the upstream authors.
```

## three.js

```text
The MIT License

Copyright © 2010-2022 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## cannon-es

```text
/*
 * Copyright (c) 2015 cannon.js Authors
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
```

## White Chapel HDRI

```text
The HDRI environment map used to light the 3D dice (dice_studio.hdr) is:

White Chapel, 1k resolution
https://polyhaven.com/a/white_chapel

From Poly Haven (https://polyhaven.com), released under CC0 1.0 Universal
(public domain) — https://polyhaven.com/license. No attribution is
required, but is credited here anyway.

Original downloaded filename: white_chapel_1k.hdr, renamed to
dice_studio.hdr for clarity in this codebase; pixel data unmodified.

(Previously this was Witsand Woolshop, also Poly Haven CC0, swapped out in
a later tuning session — see git history if you need the old one back.)
```

## Dice impact sounds

```text
Dice impact sound effects (impact_01.wav .. impact_11.wav)

Source: freesound.org, sample "347807__andresix__dice_rolls_15cm"
Author: andresix (freesound.org)
License: CC0 1.0 Universal (public domain dedication)

Split into 11 short single-impact clips and renamed for use as randomized
physics-collision impact sounds in the 3D dice roller (see index.html's
Web Audio playback code). No attribution required by the license; recorded here for provenance.
```

## Mermaid

```text
The MIT License (MIT)

Copyright (c) 2014 - 2022 Knut Sveidqvist

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## EB Garamond

```text
Copyright 2017 The EB Garamond Project Authors (https://github.com/octaviopardo/EBGaramond12)

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
https://openfontlicense.org


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded, 
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.
```

## Syphon

```text
Syphon Framework License:

Copyright 2010 bangnoise (Tom Butterworth) & vade (Anton Marini).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

* Neither the name of the Syphon Project nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Spout

```text
SpoutSDK is released under the Simplified BSD licence.

Copyright (C) 2014-2022. Lynn Jarvis. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
   this list of conditions and the following disclaimer in the documentation 
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE	ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

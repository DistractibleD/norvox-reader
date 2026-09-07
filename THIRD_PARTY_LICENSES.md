# Third-party components bundled with TextReader

**TextReader itself is licensed under GPL-2.0-or-later** — see
[LICENSE](LICENSE). It's free, open-source software: anyone may use,
modify, and redistribute it (including commercially), as long as
derivative works stay under the same license and source stays available.
This page documents every third-party component it bundles.

## Why GPL-2.0-or-later specifically

TextReader bundles Tesseract OCR, which pulls in `libjbig-0.dll`
(JBIG-KIT) — licensed **GPL-2.0-only**, confirmed against the project's own
COPYING file and the author's FAQ:
https://github.com/nu774/jbigkit/blob/master/COPYING,
https://www.cl.cam.ac.uk/~mgk25/jbigkit/. It's a hard runtime dependency
(removing the DLL stops `tesseract.exe` from even starting), pulled in via
libtiff's JBIG2 codec support.

GPL requires that anything distributed combined with a GPL-covered
component be licensed under compatible terms, with no extra restrictions
layered on top. Since JBIG-KIT is GPL-2.0-*only* (not "-or-later"),
TextReader's own license has to specifically be GPL-2.0-compatible —
GPL-2.0-or-later fits and is the standard choice. This is exactly why the
earlier plan (sell it, or give it away "free but no commercial use by
others") didn't work: both add restrictions GPL doesn't allow. Fully free
and open — anyone can do anything with it, including resell it — is what
GPL actually requires, and that's the direction this project went with.

One remaining gray area worth naming honestly: Tesseract itself is
Apache-2.0, and the Free Software Foundation's own compatibility position
is that Apache-2.0 is GPLv3-compatible but *not* officially GPLv2-compatible
(a patent-clause technicality). In practice this is a pre-existing
characteristic of the official Tesseract Windows binaries themselves
(anyone bundling them inherits it), not something specific to TextReader —
noted here for completeness rather than as a new problem to solve.

## Python packages (see `requirements.txt` for pinned versions)

| Package | License | Notes |
|---|---|---|
| comtypes | MIT | Used to talk to Windows SAPI5 directly |
| pyperclip | BSD | Clipboard access |
| keyboard | MIT | Global hotkeys |
| pytesseract | Apache-2.0 | Python wrapper around the Tesseract OCR engine |
| Pillow | HPND | Image handling for screen capture |
| pystray | **LGPL-3.0** | System tray icon |
| packaging (transitive) | Apache-2.0 OR BSD-2-Clause | pytesseract dependency |
| six (transitive) | MIT | pystray dependency |

`pystray` is LGPL-3.0 — no conflict either way, but worth noting: LGPL
components don't force the *combined* work to be GPL the way JBIG-KIT
does; only modifications to the LGPL component itself would need to stay
LGPL.

We deliberately do **not** bundle `pyttsx3` (GPLv3) — the app talks to
Windows SAPI5 directly via `comtypes` instead (see `app/sapi5.py`), so
there is no GPL-licensed code in the speech path.

## Bundled Tesseract OCR runtime (`vendor/tesseract/`)

Sourced from the official Windows build published at
https://github.com/UB-Mannheim/tesseract/wiki (itself a packaging of the
upstream https://github.com/tesseract-ocr/tesseract project). Every DLL in
the bundle was individually researched against its upstream project's own
license file — not assumed.

- **Tesseract OCR** (`tesseract.exe`, `libtesseract-5.dll`) — Apache-2.0
- **Language data** (`tessdata/*.traineddata`) — `eng` and `osd` from the
  official Tesseract installer, `nor` from
  https://github.com/tesseract-ocr/tessdata_fast — all Apache-2.0

### Permissive — no copyleft concern

| Project | DLL(s) | License |
|---|---|---|
| libarchive | libarchive-13.dll | BSD-3-Clause (plus some public-domain / CC0 files) |
| BLAKE2 / libb2 | libb2-1.dll | CC0-1.0 |
| Brotli (Google) | libbrotlicommon.dll, libbrotlidec.dll | MIT |
| bzip2 | libbz2-1.dll | bzip2-1.0.6 (BSD-style) |
| OpenSSL 3.x | libcrypto-3-x64.dll | Apache-2.0 |
| libdeflate | libdeflate.dll | MIT |
| Expat | libexpat-1.dll | MIT |
| libffi | libffi-8.dll | MIT |
| fontconfig | libfontconfig-1.dll | Custom permissive HPND-style license |
| giflib | libgif-7.dll | MIT |
| Graphite2 (SIL) | libgraphite2.dll | LGPL-2.1-or-later OR MPL-1.1 OR GPL-2.0-or-later (tri-licensed, pick any — treat as MPL-1.1) |
| HarfBuzz | libharfbuzz-0.dll | "Old MIT" (permissive) |
| ICU (Unicode Org) | libicudt75.dll, libicuin75.dll, libicuuc75.dll | ICU License (permissive) |
| libjpeg-turbo | libjpeg-8.dll | IJG License / BSD-3-Clause / zlib (permissive, pick any) |
| Leptonica | libleptonica-6.dll | BSD-2-Clause |
| LERC (Esri) | libLerc.dll | Apache-2.0 |
| LZ4 | liblz4.dll | BSD-2-Clause |
| XZ Utils | liblzma-5.dll | 0BSD |
| OpenJPEG | libopenjp2-7.dll | BSD-2-Clause |
| PCRE2 | libpcre2-8-0.dll | BSD-3-Clause |
| Pixman | libpixman-1-0.dll | MIT |
| libpng | libpng16-16.dll | libpng License (permissive) |
| libwebp (Google) | libsharpyuv-0.dll, libwebp-7.dll, libwebpmux-3.dll | BSD-3-Clause |
| libtiff | libtiff-6.dll | libtiff License (permissive) — note: links libjbig, see blocker above |
| mingw-w64 winpthreads | libwinpthread-1.dll | MIT / BSD-3-Clause |
| Zstandard (Meta) | libzstd.dll | BSD-3-Clause OR GPL-2.0-or-later (pick BSD) |
| zlib | zlib1.dll | zlib License |

### LGPL — acceptable because dynamically linked as unmodified, separate DLLs

Each requires: including the license text, a notice that the component is
LGPL with where to get its source, and not statically merging or modifying
the DLL (shipping it as-is satisfies the relinking requirement).

| Project | DLL(s) | License |
|---|---|---|
| cairo | libcairo-2.dll | LGPL-2.1 OR MPL-1.1 (dual — rely on MPL-1.1 to sidestep LGPL entirely) |
| libdatrie | libdatrie-1.dll | LGPL-2.1-or-later |
| FriBidi | libfribidi-0.dll | LGPL-2.1-or-later |
| GLib (+GObject/GIO/GModule) | libgio-2.0-0.dll, libglib-2.0-0.dll, libgmodule-2.0-0.dll, libgobject-2.0-0.dll | LGPL-2.1-or-later |
| GNU libiconv | libiconv-2.dll | LGPL-2.1-or-later (library; the separate CLI tool is GPL but isn't shipped) |
| GNU gettext (libintl runtime) | libintl-8.dll | LGPL (runtime only; gettext tools are GPL but aren't shipped) |
| Pango | libpango-1.0-0.dll, libpangocairo-1.0-0.dll, libpangoft2-1.0-0.dll, libpangowin32-1.0-0.dll | LGPL-2.0-or-later |
| libthai | libthai-0.dll | LGPL-2.1 (treat as "-only"; upstream is ambiguous about "-or-later", see https://github.com/tlwg/libthai/issues/34) |

### GPL with a linking exception — safe, but must be documented as such

| Project | DLL(s) | License |
|---|---|---|
| GCC runtime (MinGW-w64 SEH build) | libgcc_s_seh-1.dll, libstdc++-6.dll | GPL-3.0-only **WITH GCC-runtime-library-exception-3.1** — the exception (https://www.gnu.org/licenses/gcc-exception-3.1.en.html) specifically permits combining compiled output with proprietary code. Document with the exception named, not as bare GPL-3.0. |

### Dual-licensed — we rely on the permissive option

| Project | DLL(s) | License |
|---|---|---|
| FreeType | libfreetype-6.dll | FTL (FreeType License, permissive, BSD-style with a mild attribution clause) OR GPL-2.0-only — rely on FTL |

### GPL — the component that determines TextReader's own license

| Project | DLL(s) | License |
|---|---|---|
| JBIG-KIT | libjbig-0.dll | GPL-2.0-only, no linking exception |

## What this means practically

TextReader is free, source-available, GPL-2.0-or-later software — anyone
can use, modify, resell, or redistribute it, as long as they keep it under
the same license terms and make source available. That's fully compatible
with everything bundled here, including JBIG-KIT. Keep this file (and
LICENSE) shipped alongside the app, and keep it updated as dependencies
change — this document was put together by an AI assistant, not a lawyer,
so treat it as a solid starting point rather than a final legal sign-off.

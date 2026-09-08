<img src="assets/logo.svg" alt="Norvox Reader logo" width="100" height="60">

# Norvox Reader

**v0.2.0**

A standalone Windows app that reads text out loud in **English and Norwegian**.
The interface itself is available in both languages too.

It covers four ways to get text read aloud:

1. **Type or paste text** into the app and press Read.
2. **Capture a region of the screen and OCR it** — for text that's locked
   behind a login and can't be copied (e.g. a scanned or DRM-protected
   schoolbook page). Drag a box around the text; it's recognized and read.
   Tesseract OCR is bundled in `vendor/tesseract` — no separate install.
3. **Read whatever is currently selected/highlighted** in *any* other
   window (browser, PDF reader, Word) — press a global hotkey
   (default `Ctrl+Alt+S`) after highlighting text anywhere, no need to
   switch to the app first.
4. A dedicated hotkey (default `Ctrl+Alt+D`) jumps straight to screen
   capture from anywhere, too.

## Download

Two ready-to-run options — pick whichever suits the PC you're installing
on (see [Releases](https://github.com/DistractibleD/norvox-reader/releases)):

- **`NorvoxReaderSetup-X.Y.Z.exe`** — a normal installer with a Start Menu
  shortcut and an uninstaller. It's still a "real" installer, just one
  that **needs no administrator rights at all** — it installs to your own
  user folder and never triggers a UAC prompt. Good default choice.
- **`NorvoxReader-vX.Y.Z-portable.zip`** — no installer whatsoever. Extract
  it anywhere you have write access (Desktop, a USB stick, etc.) and run
  `Norvox Reader.exe` inside. Use this on a machine where even running an
  installer is restricted (e.g. some school/work PCs).

Both include everything needed to run — Tesseract OCR and every Python
dependency are already bundled inside. The one thing neither can bundle is
the **Norwegian voice** itself (see step 3 below) — that's a Windows
component, not something any app installer can ship.

## Setup (running from source, for development)

### 1. Install Python

Python 3.10+ is required. Get it from https://python.org (check "Add
python.exe to PATH" during install).

### 2. Install the app's dependencies

```bash
pip install -r requirements.txt
```

### 3. Add a Norwegian voice to Windows (for Norwegian speech)

Windows ships English voices by default; Norwegian needs to be added once
per machine. Norvox Reader has a **Settings > "Install Norwegian voice…"**
button that does this for you — it triggers a Windows admin-approval (UAC)
prompt (unavoidable, only you can click that), then downloads and installs
the voice. Approve the prompt, wait a few minutes, then click **"Refresh
voice list"** in Settings.

If you'd rather do it by hand, or the button's install fails:

1. Open **Settings > Time & Language > Speech**.
2. Under "Manage voices", click **+ Add voices**, search for **Norwegian**,
   and install it (e.g. "Norwegian (Bokmål)" — gives you a voice like
   "Microsoft Jon").

#### If neither of those installs anything (silent failure)

On some machines the Settings UI's voice download silently fails — it just
returns to the same screen with nothing installed, no error shown. If that
happens, install the voice directly via an **elevated** PowerShell
(right-click Start > Terminal (Admin)):

```powershell
Get-WindowsCapability -Online | Where-Object Name -like "Language.TextToSpeech*nb-NO*"
```

If that shows `State : NotPresent` or `State : Staged`, run:

```powershell
Add-WindowsCapability -Online -Name "Language.TextToSpeech~~~nb-NO~0.0.1.0"
```

This downloads and installs the voice directly (a few hundred MB, so it can
take a few minutes — the console progress bar can appear frozen at 0% even
while it's actively downloading; that's a known cosmetic bug, not a hang).
Note this is a different Windows component from `Language.Speech` (that one
is speech *recognition*, not the *voice* itself — installing only that one
won't make a voice appear). This is exactly what the in-app button runs.

### 4. Run it

```bash
python main.py
```

## Building the distributable installer/zip yourself

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

This builds the app (via PyInstaller, `--onedir` — a folder, not
`--onefile`, since re-extracting the ~175 MB bundled Tesseract on every
launch would make startup slow), then packages it two ways:

- `installer_output\NorvoxReaderSetup-X.Y.Z.exe` — built with
  [Inno Setup](https://jrsoftware.org/isinfo.php) (installed automatically
  via `winget` if missing). See `installer.iss` — `PrivilegesRequired=lowest`
  is the key setting that keeps it admin-free.
- `dist\NorvoxReader-vX.Y.Z-portable.zip` — just a zip of the built folder.

The Norwegian *voice* still can't be bundled this way — it's a proprietary
Microsoft component distributed through Windows' own update mechanism, not
a file that can ship inside your app. See the in-app installer button above.

## Licensing

Norvox Reader is free, open-source software, licensed under the
**GNU General Public License v2.0-or-later** — see [LICENSE](LICENSE).
Anyone can use, modify, and redistribute it (commercially or not), as long
as derivative works stay under the same license and the source stays
available. This license was chosen because it bundles Tesseract OCR, which
pulls in one GPL-2.0-only component (JBIG-KIT) — see
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for the full
per-component breakdown and why. That file also documents every other
bundled open-source component's license. Not legal advice — for anything
beyond hobby distribution, get a real legal review.

Not selling this — but if people want to support the project financially,
a donation link (GitHub Sponsors, Ko-fi, etc.) is a natural fit and doesn't
conflict with any of the above; that's a separate to-do, not yet set up.

## Notes & limitations

- Closing the window minimizes Norvox Reader to the system tray (so the global
  hotkeys keep working in the background). Use **Quit** on the tray icon's
  right-click menu to fully exit.
- Screen-region capture works on your **primary monitor**.
- Pause takes effect at the end of the current sentence, not instantly
  mid-sentence — this is a limitation of the underlying Windows speech API.
- The "read selected text" hotkey works by briefly copying your selection
  to the clipboard and restoring whatever was there afterwards. If your
  current app blocks Ctrl+C entirely, that hotkey won't have anything to
  read — use screen capture instead.
- Each Windows user has their own settings, stored in
  `%APPDATA%\NorvoxReader\config.json`.

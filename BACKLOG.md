# Norvox Reader — Backlog

Add anything here yourself, anytime — new line under "Planned" is enough.
Just tell me to "work on the top item" or point at a specific line whenever
you want me to pick something up.

## Done

- [x] Reading speed slider, easily accessible on the Read tab
- [x] Always-on-top mini control bar: draggable, with read selection /
  pause / resume / stop, shown automatically when the main window is
  hidden
- [x] Auto-open on a secondary monitor when one's connected, so the
  primary screen stays free
- [x] "Read this page" — reads the whole focused window via Select All
  (a button on the floating toolbar and its own hotkey, default `Ctrl+Alt+A`)
- [x] Simplified workflow: app now starts with only the floating toolbar
  visible (main window hidden by default); toolbar has a settings (⚙)
  button that opens the main window straight to Settings; toolbar buttons
  are now icons with hover tooltips; toolbar has a visible blue accent
  color. Removed the redundant "Read current selection"/"Read this page"
  buttons from the main window's Read tab (still reachable via the
  toolbar, hotkeys, or tray) — pasting text and hitting Read still works
  there as before.

- [x] Toolbar's ✕ now fully closes the program; added a separate small
  "minimize to tray" (−) button on the toolbar for the old ✕ behavior
- [x] Fixed the main window briefly flashing visible on every startup
  (it's created and shown by Tk by default, then all the slow setup work
  used to run before we hid it again — now withdrawn immediately)
- [x] Added version tracking (`app/version.py`, shown in Settings) and
  pushed the first tagged release, v0.1.0, to GitHub

- [x] Speed slider now shows 1-10 on both the toolbar and Settings,
  instead of raw words-per-minute (~80-300) — the TTS engine still works
  in WPM internally, only the displayed number changed

- [x] Two ready-to-run distribution options, both bundling everything
  needed (no separate Python/Tesseract installs): a no-admin-required
  Inno Setup installer (`installer.iss`, `PrivilegesRequired=lowest` —
  installs per-user, no UAC prompt, verified via a real silent-install
  test) and a plain portable .zip (no installer logic at all, for PCs
  where even running an installer is restricted). Both built by
  `build_exe.ps1` in one pass. The Norwegian *voice* still can't be
  bundled either way — it's a Windows component, not ours to ship — still
  need to actually test that on the school PC and find a workaround if it
  fails there.

- [x] Tagged and published v0.2.0 as an actual GitHub Release
  (https://github.com/DistractibleD/norvox-reader/releases/tag/v0.2.0)
  with both `NorvoxReaderSetup-0.2.0.exe` and
  `NorvoxReader-v0.2.0-portable.zip` attached as downloadable assets.
  Pinged the "Distracted.no" website session with both direct-download
  links so it can switch the site's CTA from "View on GitHub" to a
  direct download.

## Planned

- [ ] Auto-update: check for new releases, prompt the user, download and
  install automatically

## Ideas / someday

(nothing yet)

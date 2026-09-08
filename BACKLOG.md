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

## Planned

- [ ] Toolbar's ✕ should fully close the program (it currently just hides
  the toolbar); add a separate small "minimize to tray" button on the
  toolbar for the current ✕ behavior instead
- [ ] Change the speed slider's displayed numbers from raw words-per-minute
  (currently ~80-300) to a simpler 1-10 scale, on both the toolbar and
  Settings
- [ ] Single-file .exe installer for easier download/install (currently
  builds as a `--onedir` folder — see build_exe.ps1 and the note in
  README's "Building a standalone .exe" section for why; needs a real
  installer tool like Inno Setup rather than just switching PyInstaller
  modes, to avoid a slow re-extracting single-file build)
- [ ] Auto-update: check for new releases, prompt the user, download and
  install automatically

## Ideas / someday

(nothing yet)

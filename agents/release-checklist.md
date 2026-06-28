# Release Checklist

Use this before packaging, publishing, or attaching release artifacts.

## Source Verification

After source, data, or UI changes:

```bash
.venv/bin/python -m py_compile main.py
.venv/bin/python -m compileall src
./scripts/build_app.zsh
```

Normal app builds produce `Arcane Manager.app` only. They must not create zip
archives or leave DMG artifacts in the project folder.

## UI Smoke Checks

For UI changes, verify fullscreen and smaller windowed layouts.

Check the main surfaces touched by the change:

* Initiative Tracker: party editing, monster add/search, HP controls, status,
  turn navigation, and monster detail sheet.
* Spells: bilingual search, compact rows, spell details, and inline dice links.
* Dice Roller: formula construction, roll button, overlay, and history.
* Adventure: vault selection, tree rows, note render/edit/save, links, and file
  actions.
* Settings: theme color changes and reset behavior.

## Dice Checks

For dice changes, test:

```text
1d4+3
2d8
3d4+2d6
```

Also test at least one inline dice link from a spell or monster sheet.

## Package Checks

Before release:

* Confirm the packaged app opens.
* Confirm the 3D dice roller works.
* Confirm the app does not request microphone or speech recognition permissions.
* Publish GitHub releases with `./scripts/publish_github_release.zsh`.
* Confirm the script reads the latest GitHub Release and increments the minor
  version by default, unless a major or patch bump was explicitly requested.
* Attach the generated DMG read-only and verify it contains `Arcane Manager.app`.
* Confirm the local DMG is removed after a successful GitHub Release upload.

# Arcane Manager

Arcane Manager is a local macOS companion app for D&D 5e sessions.

It currently includes:

- an initiative tracker with parties, player characters, monsters, HP controls, and turn navigation
- a bilingual spell browser with English and Italian search
- clickable dice expressions inside spell and monster text
- a 3D dice roller with mixed dice pools such as `3d4+2d6`
- bundled SRD spell and monster data

## Installation

To use the app, copy `Arcane Manager.app` to a Mac and open it.

Note: the current local build is arm64, so it is intended for Apple Silicon Macs.

## Build

The repository tracks source files and assets, not compiled `.app`, `.zip`, or `.dmg` artifacts.

Build the standalone app locally with:

```bash
./scripts/build_app.zsh
```

The script keeps `.venv` for future development, signs the app ad-hoc, and creates:

```text
Arcane Manager.app
Arcane Manager.zip
```

For GitHub distribution, attach release builds to GitHub Releases instead of committing them to the repository.

Security hardening notes live in [SECURITY.md](SECURITY.md). The build uses `requirements.lock.txt` when present so packaged releases are not rebuilt against surprise dependency versions.

## Launch

Recommended:

```bash
open -n "Arcane Manager.app"
```

You can also double-click `ArcaneManager.command` or `Arcane Manager.app`.

If the app gets stuck or cannot be closed from the menu:

```bash
./ArcaneManager.command stop
```

## Development

Run directly from the local environment:

```bash
.venv/bin/python main.py
```

## Data

Arcane Manager uses local JSON files:

- `spells.json`
- `bestiary_srd.json`

Only put content in those files that you can use and redistribute.

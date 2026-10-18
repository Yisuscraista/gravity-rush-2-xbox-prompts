# Gravity Rush 2 — Xbox Button Prompts

Version **1.0.0** · **CUSA03694** · Update **01.11** · **Python 3.10+**

An unofficial visual mod replacing selected PlayStation button prompt artwork with Xbox-style icons. **This changes prompt art, not controller bindings or input behavior.** Configure your controller in your emulator separately.

## Compatibility and requirements

- An extracted/decrypted copy of **Gravity Rush 2, CUSA03694, update 01.11**, obtained legally by you.
- The game folder must contain `eboot.bin`, `sce_sys/param.sfo`, `Gravite2_Chunk0.psarc`, and `Gravite2_Patch_Chunk0.psarc`.
- Intended for shadPS4 and compatible derivatives that read these archives. This is **not a PS4 PKG** or a folder to drop into `-mods`.
- Python **3.10 or newer**, using only the standard library. No native dependencies or third-party Python packages are needed.
- The installer checks the title ID, update version, and resource hashes. Other regions/versions and incompatible UI mods are rejected; do not bypass these checks.
- Linux portable-tool tests have been exercised. **Windows runtime behavior and Windows launchers have not been tested on Windows.**

Close the game and emulator before installing or uninstalling. Automatic process detection is a precaution, not a substitute for closing them yourself. Keep an independent backup of your game and enough free disk space for appended patches and transaction metadata.

## What changes

The manifest describes **27 differential resource patches** across the base and update archives:

- A/B/X/Y in place of cross/circle/square/triangle, keeping their physical positions (cross → A, circle → B, square → X, triangle → Y).
- LB/RB, LT/RT, and LS/RS prompts, including normal and highlighted variants.
- Embedded control-settings artwork, including DLC control diagrams and Xbox letters on the central controller drawing.
- An Xbox three-line Menu icon replacing OPTIONS in the return-to-game prompt.

The scope consists of four font/common resources, twenty standalone menu textures, two embedded settings containers, and one additional standalone OPTIONS texture. Exact archive member names are retained in `manifest.json`.

**No bindings, saves, emulator settings, graphics configuration, or networking are changed.** The central controller silhouette remains DualShock-shaped; touchpad and D-pad icons remain. This does not promise replacement of every illustration or tutorial in the game.

The source package reports in-game verification of the main control-settings screen. The final OPTIONS replacement was verified in the generated/installed resource, **but its in-game appearance remains unverified**. Packaging tests are not new gameplay or rendering tests.

## Install on Windows

1. Close the game and emulator.
2. Extract the entire ZIP; do not run files from inside the ZIP viewer.
3. Make sure Python 3.10+ is available through `py -3` or `python`.
4. Open `Install-Windows.bat` and enter the game folder when prompted, or pass it as an argument.
5. Wait for `Installation verified`. Hashing large archives can take time.

From a terminal in this package folder:

```text
py -3 mod.py install "D:\Games\GRAVITY RUSH 2"
py -3 mod.py check "D:\Games\GRAVITY RUSH 2"
```

Use `python` instead of `py -3` if that is how your Python installation is available. The batch wrappers try `py -3` first and fall back to `python` when the launcher is absent. Verify the interpreter version yourself.

## Install on Linux

From a terminal in the extracted package folder:

```bash
bash Install-Linux.sh
```

Enter the game folder when prompted, or provide it directly:

```bash
bash Install-Linux.sh "/path/to/GRAVITY RUSH 2"
python3 mod.py check "/path/to/GRAVITY RUSH 2"
```

The direct installer command is `python3 mod.py install "/path/to/GRAVITY RUSH 2"`.

## Backups and uninstall

Each installation transaction stores original archive tables, sizes, and hashes under:

```text
GAME_FOLDER/.gr2-xbox-backups/TIMESTAMP/
```

**Keep this folder while the mod is installed.** Original payload bytes remain in the archives; the installer appends patched resources and updates the tables. Uninstall restores the original tables and truncates appended data, avoiding a second full copy of the multi-GB archives. Do not move the game folder before uninstalling: transaction receipts are tied to its absolute path.

Close the game and emulator, then open `Uninstall-Windows.bat` or run:

```bash
bash Uninstall-Linux.sh "/path/to/GRAVITY RUSH 2"
```

Direct commands (on Windows, replace `python3` with `py -3` or `python`):

```bash
python3 mod.py uninstall "/path/to/GRAVITY RUSH 2"
python3 mod.py uninstall "/path/to/GRAVITY RUSH 2" --backup "/path/to/transaction"
```

Without `--backup`, the latest active transaction is selected. Uninstall verifies each installed archive's **full SHA-256** and refuses to truncate archives changed by another mod or game update. Do not delete backups or bypass safety checks to force restoration.

Reinstalling over the same mod does not duplicate its patches. A compatible partial installation can be completed; uninstalling a transaction restores only changes made in that transaction. Multiple transactions may require uninstalling the newest first.

## Validation and development

The installer validates supported metadata, original/target member hashes, delta integrity, and reconstructed sizes/hashes. It prepares all affected archives before writing, reads back patched resources, and attempts rollback if an installation write fails. Reversible transactions are not a guarantee against interrupted power or storage failure.

Run the portable tests without supplying a game:

```bash
python3 test_mod.py
python3 -m py_compile mod.py psarc.py test_mod.py
python3 mod.py --help
```

The included unittest suite uses **synthetic two-archive fixtures**, testing install/check, idempotency, byte-exact uninstall, unknown-resource rejection before writing, wrong-version rejection, and rollback when the second archive fails. It does not contain original game assets or independently test all 27 real resource transformations or rendering. Delta payloads and manifest hashes are preserved from the source release.

`SHA256SUMS.txt` lists every distributable file except itself. On Linux, verify it from this folder with:

```bash
sha256sum -c SHA256SUMS.txt
```

The package contains installer source, differential patches, manifest, wrappers, and tests only. It does not include whole game archives, original fonts/textures, saves, credentials, or personal machine paths. Do not add these to a public repository or bug report. When reporting an issue, include your Python version, OS, title/update version, command, and error text with personal paths removed.

## Credits and AI assistance

- **Yisuscraista** — project creator, direction, controller-layout decisions, and in-game testing.
- **Hermes Agent (Nous Research), also known as Jarvis** — AI assistant used to help develop the Xbox-style prompt modifications, resource-patching tools, installer, tests, and documentation.

This mod was created with AI assistance. Yisuscraista directed the work and tested the mod; Hermes/Jarvis is an AI tool, not a human collaborator or a GitHub account with repository access.

**AI model used for the original mod development:** `gpt-6.1-sol`, accessed through the `openai-codex` provider in Hermes Agent. This is the model identifier recorded in the development session; it is distinct from Hermes/Jarvis, the agent framework.

## Legal and attribution notice

This is an unofficial community modification, not affiliated with or endorsed by Sony Interactive Entertainment, PlayStation, Microsoft, or Xbox. Gravity Rush 2, PlayStation, DualShock, Xbox, and related names and marks belong to their respective owners. All third-party game content and marks remain the property of their owners. You must supply your own legally obtained game files.

No license was supplied with the source package, and this distribution does **not** invent or grant a new software or asset license. Public availability does not itself grant reuse, redistribution, or sublicensing rights; obtain permission from the relevant rights holders where required.

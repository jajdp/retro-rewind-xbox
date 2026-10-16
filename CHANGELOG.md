# Changelog

All notable changes to this repository. Dates are `YYYY-MM-DD`.

The versions here are **the repository's**, not the package's. The package version lives in
`package/Package.appxmanifest` and has to go up on every package you install, because the console
will not replace a package with one of the same version.

## [1.0.1] — 2026-10-13

### Fixed

- **`tools/compile-check.py` no longer carries the author's own disk path.** `BUILDWORKSPACE` was a
  constant holding the full path to Wiicompiled's `Install\BuildWorkspace` **on the machine this
  was built on** — which was both a leak of nothing useful and, more to the point, a path that
  could never match yours: with `--overlay=` the script would have looked for the UWP entry point
  somewhere that does not exist on your disk. It is now worked out from the paths inside the
  `compile_commands.json` you pass in, and `MKW_BUILDWORKSPACE` overrides it if that ever fails.
  The install guide used to claim that "the scripts carry no machine's paths inside them"; now it
  is true.

Found by an audit of all eleven published repositories, over their whole history, looking for
secrets and personal data. It was the only live finding.

## [1.0.0] — 2026-10-13

First publication. The UWP side of the Wiicompiled port that runs Mario Kart Wii and Retro Rewind
on an Xbox Series X at 58 FPS.

### Added

- **`patches/aurora-uwp.patch`** — 22 files of [Aurora](https://github.com/encounter/aurora) (MIT):
  the CMake side, the Dawn provider, the SDL3 provider, the GX layer and the card paths, so that
  Aurora builds and runs inside an App Container.
- **`tools/parche-aurora.py`** — the seven Aurora changes that came later, while making the game
  actually boot on the console: the CoreWindow surface for Dawn, input, logging without a console.
  As a script rather than a diff, because each change checks its anchor before writing.
- **`tools/compilar.cmd` and `tools/compile-check.py`** — the compile pass, inside Visual Studio's
  **store** environment. It has to run twice; the second pass (`--solo=deps`) brings ImGui, and
  without it the link leaves 20 ImGui symbols unresolved.
- **`tools/enlazar.cmd` and `tools/enlazar-uwp.py`** — the link, with `ld.lld` in `link` flavour.
  This is where the port's two sharpest traps live: `/subsystem:windows,10.0` (lld defaults to 6.0
  and the UWP activator then answers `0x8027025B` with no explanation) and the fact that the build
  produces **two products at once** — the base game and Retro Rewind — whose objects share
  everything but three groups, so each executable has to leave the other's out.
- **`tools/empaquetar-uwp.py`** — lays out the package, runs `makeappx` and signs with `signtool`.
- **`package/`** — the manifest, with `CHANGE-ME` where your publisher goes, and the runtime
  `Config.toml`.
- **Documentation in both languages**, including the twelve changes Wiicompiled's own runtime needs,
  described one by one — see below for why they are described and not shipped.

### Not included, and why

- **No patch for Wiicompiled's runtime.** Wiicompiled ships no license of its own (only those of
  the third-party code it bundles), so this repository carries **no line of it** — the same rule
  applied in the other ports of this catalogue to projects that grant no permission. The twelve
  changes it needs are described in `docs/HOW-IT-WORKS.md`, file by file and reason by reason;
  that is information, not code.
- No disc, no mod payload, no executable, no `.msix`, no tiles, and none of the UWP dependency
  bundles (Dawn, SDL3, `libuwp`), which are other people's binaries.

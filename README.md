# Mario Kart Wii and Retro Rewind on Xbox — the UWP port

How to take what **Wiicompiled** produces from your own *Mario Kart Wii* disc — a native
executable, not an emulator — and run it **on an Xbox Series X in Developer Mode**, as a UWP package
you build and sign yourself. With or without
[Retro Rewind](https://github.com/RetroRewind-Team), the fan track and character distribution.

*(Español: [README.es.md](README.es.md))*

It is not a theory: both products boot, draw, play sound and take controller input on the console at
**58 FPS**, with their saves in the package's `LocalState`.

## Which console this was tested on

**An Xbox Series X**, in Developer Mode. Both of the consoles this was built and tested on are Series X,
so that is the only hardware anything claimed here covers.

**A Series S has never been tried — not once.** It is a different machine: less memory available to a
game and a weaker GPU. This may work on one, it may run slower, or it may not start at all; nothing here
has been measured on it. If you run it on a Series S, what you get is not what this README reports, and
none of the numbers here are a promise about that console.

## What this repository is

**The UWP half of that port, and the tools that apply it.** Wiicompiled builds for the desktop;
this is what has to change, and how to compile, link and package, so the result lives inside an Xbox
App Container.

| Piece | What it is |
|---|---|
| `patches/aurora-uwp.patch` | 22 files of [Aurora](https://github.com/encounter/aurora) (MIT), the layer that stands in for GX, input and the window: its CMake, the Dawn provider, the SDL3 provider, the GX layer and the card paths |
| `tools/parche-aurora.py` | The seven Aurora changes that came later, while making the game actually boot: the CoreWindow surface for Dawn, input, and logging with no console |
| `tools/compilar.cmd` + `compile-check.py` | The compile pass, inside Visual Studio's **store** environment. **It has to run twice** |
| `tools/enlazar.cmd` + `enlazar-uwp.py` | The link, with `ld.lld`. The port's two most expensive traps live here |
| `tools/empaquetar-uwp.py` | The package layout, `makeappx` and `signtool` |
| `package/` | The manifest, with `CHANGE-ME` where your identity goes, and the runtime's `Config.toml` |

## What it is not, and one thing said plainly

There is no **disc, no mod payload, no executable, no `.msix`, no tiles and none of the UWP
libraries** (Dawn, SDL3, `libuwp`) here — those are other people's binaries.

And above all: **there is no patch here for Wiicompiled's runtime.** Wiicompiled ships no license of
its own — only those of the third-party code it bundles — so **not one line of it** is copied here,
the same rule this catalogue's other ports apply to projects that grant no permission. The **twelve
changes** its runtime needs are **described one by one** in
[`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md): which file, what to do to it, and why. That is
information, not code.

In practice: if you have Wiicompiled, this documentation and these tools are the port. What is
missing is a button that does the part which is not ours to publish.

## What you need first

| | |
|---|---|
| **Wiicompiled** | This was done with **0.2.31**. It compiles your disc to native code; without it there is nothing to port |
| **Your own disc** | *Mario Kart Wii* PAL `RMCP01`, which is what Wiicompiled accepts |
| **Retro Rewind** (optional) | Its `Code.pul` is the only part that gets compiled; tracks and menus are read live at startup |
| **Visual Studio 2022** | With the **C++ UWP component**: its `store` environment is needed (`vcvarsall x64 store`), plus `makeappx`/`signtool` from the Windows SDK |
| **Wiicompiled's llvm-mingw** | clang 22 and `ld.lld` with the MSVC ABI, which is what compiles and links here |
| **The UWP bundle** | Dawn, `nod`, `libuwp`, libpng and zlib built for UWP — and **a separate SDL3 for UWP**: the one in the main bundle is a desktop build (see the guide) |
| **Python 3** and **an Xbox in Developer Mode** | The scripts, and the console. Plus a certificate to sign with |

## How it goes

```powershell
# 1. Aurora: the big patch and the seven later changes
git apply --directory=<path to aurora-main> patches\aurora-uwp.patch
python tools\parche-aurora.py <path to aurora-main>

# 2. Wiicompiled's runtime: the twelve changes in docs/HOW-IT-WORKS.md, by hand

# 3. compile, TWICE (the second pass brings ImGui)
tools\compilar.cmd <compile_commands.json> C:\mkw\obj      --overlay=C:\mkw\port
tools\compilar.cmd <compile_commands.json> C:\mkw\obj-deps --overlay=C:\mkw\port --solo=deps

# 4. link whichever product you want
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\RetroRewind.exe retro

# 5. package and sign
python tools\empaquetar-uwp.py C:\mkw\build\RetroRewind.exe C:\mkw\build\RetroRewind.msix package
```

Step by step, including the console side: **[`docs/INSTALL.md`](docs/INSTALL.md)**.

## What it had to solve

The detail, with what the log said in each case, is in
**[`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md)**.

| | Symptom | Fix |
|---|---|---|
| 1 | Activation answers `0x8027025B` and says nothing else | `lld` writes subsystem version 6.0 into the PE header, and an App Container requires 6.2 or above: `/subsystem:windows,10.0` |
| 2 | Boots, draws the UWP splash and exits **without writing a single log line** | The build leaves both products' objects in the same folder, and each carries its own `indirect_dispatch` with a hash in the name. Keeping both is not a link error: it just kills the game at startup |
| 3 | The link leaves 20 ImGui symbols unresolved | The compile pass has to run **twice**; the second one (`--solo=deps`) is what brings ImGui |
| 4 | SDL3 will not load | The main bundle carries a **desktop** `SDL3.dll` (it imports `MSVCP140.dll` without `_APP`), which an App Container will not load. The UWP SDL3 goes separately |
| 5 | No console, so nothing can be seen | `stdout` and `stderr` are redirected into a file in `LocalState`. It is the first thing to do, because without it none of the other failures is visible |
| 6 | The runtime saves data where the App Container does not allow | `SHGetKnownFolderPath` does not exist in UWP: data goes to the package's `LocalState`, through `SDL_GetPrefPath` |
| 7 | Twelve more places in the runtime | Fibers, the exception handler, `MessageBox`, pipes, `DbgHelp`, Schannel, Discord, and an `stdext` clang does not have. All described in the guide |

## Credits and license

The tools and the recipe are **Recompilaciones**', under the [MIT](LICENSE) — the same license as
Aurora, which is the third-party code this repository patches. Aurora is © 2022 Luke Street.
*Mario Kart Wii* is © Nintendo; Retro Rewind belongs to its own team; Wiicompiled to its author.
This project is not affiliated with any of them, nor with Microsoft, and distributes nothing that
belongs to them: the detail is in [`NOTICE.md`](NOTICE.md). Rights holders can write to
**jajdpmail@gmail.com**.

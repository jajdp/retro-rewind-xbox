# How it works, and why each piece is there

*(Español: [HOW-IT-WORKS.es.md](HOW-IT-WORKS.es.md))*

## Where it starts from

**Wiicompiled does not emulate: it recompiles.** Out of your *Mario Kart Wii* disc it produces a
native Windows executable, and to stand in for the Wii's hardware it uses
[Aurora](https://github.com/encounter/aurora) — the GX, input, memory card and window layer, on
WebGPU (Dawn) and SDL3.

Retro Rewind enters that recompilation through **one single file**, its `Code.pul`; the tracks, the
menus and the translations are read **live at startup** from its folder. That is why the mod can
change without recompiling anything, and why one port here covers both products.

What this repository adds is the UWP half: making all of that fit inside an App Container.

## The two traps that cost the port

### `0x8027025B`, and the subsystem version

Activating a package can fail with `0x8027025B` **and not one word more**. There are two causes, and
it is worth holding both in mind because the message is the same:

1. **The VCLibs dependency is missing** from the manifest. Putting the DLLs inside the package does
   not replace it.
2. **The PE header says the subsystem is 6.0.** `lld` writes that by default, and an App Container
   requires **6.2 or above**. The fix is `/subsystem:windows,10.0` on the link — one option, and two
   days of looking for it.

### Two products, two `indirect_dispatch`

The build leaves the base game's objects and Retro Rewind's **in the same folder**: they share the
runtime, Aurora, the libraries and the common shards, and differ in only three groups. Among those
groups there is, per product, an `indirect_dispatch` object **whose name carries a hash**, so it
does not stand out.

Linking both is **not an error**: the symbols do not clash. What happens is that the game boots,
draws the UWP splash and exits **without writing a single log line**. That cost the whole first
round.

Hence the last argument of `tools/enlazar.cmd`, and hence the fact that the exclusion lists come
from the **PC build's actual link command** (`build.ninja`), which is the only reliable source of
which object belongs to which product.

## The other three, in linking and compiling

- **Compilation runs in two passes.** The second (`--solo=deps`) brings ImGui; without it 20 ImGui
  symbols are left unresolved.
- **The main bundle's `SDL3.dll` is a desktop build**: it imports `MSVCP140.dll` without `_APP`, and
  an App Container will not load it. The UWP SDL3 lives in its own folder, and the link takes
  `SDL3.lib` from there.
- **Aurora and the dependencies go into static archives**, as in the PC build, rather than object by
  object: that way the linker takes only what the runtime uses. Aurora's `dvd` and `gd` modules, for
  instance, demand symbols that are never linked on the PC.

## First of all: being able to see anything

**There is no console in UWP**, and that is where the runtime writes its errors. Until that was
fixed, every failure above looked like "it boots and exits".

The change is to redirect `stdout` and `stderr` to a file in `LocalState`
(`WiiCompiled\Logs\uwp-console.txt`), unbuffered. It is the first thing to do, and the one that
turns the rest of the work into something measurable.

## The twelve changes in Wiicompiled's runtime

They are not a patch here: Wiicompiled publishes no license of its own, so this repository **copies
no line of its code** ([`NOTICE.md`](../NOTICE.md)). What follows is the description of what to
change and why, file by file. It is 29 changes across 10 files, grouped by the problem they solve;
all of them sit behind `MKW_UWP`, so the same tree still builds for the PC.

| File | What happens, and what the change does |
|---|---|
| `include/runtime_config.h` | Asks for the user data folder with `SHGetKnownFolderPath`, which **does not exist in UWP**. It returns the application's data folder instead |
| `src/platform/host_platform.cpp` (2) | That is what resolves the folder: inside an App Container the only writable one **that the Device Portal can see** is the package's `LocalState`, which comes from `SDL_GetPrefPath`. SDL's headers have to be included for it |
| `src/main.cpp` (14) | The bulk. The entry point becomes the WinRT one (a `uwp_main.cpp` of our own, which is what SDL3 starts); out go the console and the pipes — UWP's CRT does not expose `_pipe()`; out go the error `MessageBox`es, which nobody sees on a console; out goes `DbgHelp`; and logging goes to the file in `LocalState`. `SDL_Init` is also asked **without haptics**, which this SDL does not carry |
| `src/host_context.cpp` (2) | Fibers: in the UWP family the variants that exist are the **`Ex`** ones (`CreateFiberEx`, `ConvertThreadToFiberEx`), not the plain ones |
| `src/guest_flat_memory.cpp` | The SDK **does not declare** the vectored exception handlers for the app family, even though `kernel32` exports them: they have to be declared by hand. Without them there is no way to trap guest memory accesses |
| `src/memory.cpp` | The same, on the memory map side |
| `src/host_cpu_baseline.cpp` (4) | The processor and environment checks the startup does, with calls that are not available in UWP |
| `src/hle/net/network_ssl.cpp` | The network layer uses **Schannel**, which an App Container does not have: replaced with stubs. The game needs no internet locally |
| `src/discord_presence.cpp` | Talks over a **named pipe**, and that does not exist inside an App Container: out |
| `third_party/cryptopp/zdeflate.cpp` (2) | Uses `stdext`, an MSVC extension **clang does not have** — and clang is what compiles here |

## Aurora, which does go here

Two pieces, because they were done at two different times:

- **`patches/aurora-uwp.patch`** (22 files): the CMake, the Dawn provider, the SDL3 one, the `nod`
  one, the runtime DLL copying, the GX layer and the card paths. This is what makes Aurora *compile*
  for `WindowsStore`.
- **`tools/parche-aurora.py`** (7 changes): what it took to make it *boot*. The most interesting is
  the drawing surface — **SDL3's window on UWP is a `CoreWindow`, and Dawn (D3D12) accepts it
  directly**, so nothing has to be invented: it just has to be handed over. The others are input and
  logging without a console.

Both sit behind `AURORA_WINDOWS_STORE`.

## What is not solved

- **Developer Mode suspension**: coming back from Home, the game starts over. Solving it means
  saving and restoring the whole state, and that is not here.
- The measured frame rate is **58 FPS** on an Xbox Series X, against 60 on the PC. The difference
  has not been chased.

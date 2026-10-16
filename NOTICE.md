# Notice

*(Español: [NOTICE.es.md](NOTICE.es.md))*

## Not affiliated

This is an unofficial, noncommercial fan project. It is **not affiliated with, endorsed by or
connected to Nintendo or Microsoft**, nor to the Retro Rewind team, nor to the author of
Wiicompiled, nor to the author of [Aurora](https://github.com/encounter/aurora). *Mario Kart Wii*,
*Xbox* and all related names and marks are the property of their respective owners, and are used
here only to say what this works with.

Nothing here is for sale, and nothing here is monetized.

## What this repository does not distribute

No disc image. No game or mod data — no `Code.pul`, no tracks, no menus, no `.szs`. No built
executable. No `.msix`. No save data. No package tiles (`package/Assets/` is empty, and
[`docs/ASSETS.md`](docs/ASSETS.md) asks you to supply your own).

**And none of the UWP libraries**: Dawn, SDL3, `nod`, `libuwp`, libpng and zlib are other people's
binaries. The guide says where they come from.

## What it does contain of other people's work

**Patches against Aurora.** `patches/aurora-uwp.patch` (22 files) and `tools/parche-aurora.py`
(7 changes) modify [Aurora](https://github.com/encounter/aurora), which is **MIT licensed**,
© 2022 Luke Street. MIT permits modified versions; this repository is released under
[that same license](LICENSE), and Aurora's own copyright notice travels with it.

**Nothing of Wiicompiled.** Wiicompiled publishes no license of its own — the `licenses/` folder it
installs holds only those of the third-party code it bundles (Aurora, CppWinRT, nodtool, the VC
runtime, portable build tools). With no licence granting it, **no part of its source is reproduced
here**: not as a diff, not as patch anchors, not as quoted lines. The twelve changes its runtime
needs to work inside an App Container are *described* in `docs/HOW-IT-WORKS.md` — which file, what
the problem is, and what the change does. That is a technical description, the same kind any report
about someone else's software contains, and it carries none of their code.

The tooling in `tools/` is first-party: it works with object-file names, library names and linker
options, and quotes no source at all.

**There are no screenshots here.** A screenshot of this running would be mostly Nintendo's artwork.

## Takedown and contact

If you hold rights in this material and want something here removed or changed, write to
**jajdpmail@gmail.com**, saying what you object to and in what capacity you are writing.

Requests from rights holders are honoured: the disputed part is removed, or the repository is taken
down, without argument, and you will get a reply confirming it. No notice or legal process beyond
that email is needed to reach the person who maintains this.

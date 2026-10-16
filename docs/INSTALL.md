# Building the port and getting it onto the console

*(Español: [INSTALL.es.md](INSTALL.es.md))*

Eight steps. The first four are done once.

## 0. Before you start: where the commands go

Everything here goes in **PowerShell**, the ordinary Windows terminal: press the **Windows** key,
type `powershell` and press **Enter** on *Windows PowerShell*. A window opens with a line ending in
`>`; that is where you type the command and press **Enter**.

Use `cd` with the path, in quotes if it has spaces. A shortcut that saves mistakes: open the folder
in File Explorer, click the address bar, type `powershell` over whatever is there and press
**Enter**.

**No administrator is needed** anywhere here. And in one step it actively breaks things: the
certificate in §5 is created in the store of whoever runs the command, so elevated it would land in
the administrator's store and `signtool`, running as you, would not find it. The only thing that
asks for administrator is the Visual Studio installer.

**PowerShell 7 is not needed**: the one Windows ships is enough.

---

## 1. What you need first

| | What for |
|---|---|
| **Wiicompiled** (0.2.31 is what this was done with) | Compiles your disc to native code. Without it there is nothing to port |
| **Your Mario Kart Wii disc**, PAL `RMCP01` | That is what Wiicompiled accepts |
| **Retro Rewind** (optional) | Its `Code.pul` is the only part compiled; tracks and menus are read at startup |
| **Visual Studio 2022** with the **C++ UWP component** | Its `store` environment (`vcvarsall x64 store`), and `makeappx`/`signtool` from the Windows SDK |
| **Wiicompiled's llvm-mingw** | clang and `ld.lld` with the MSVC ABI |
| **The UWP bundle**, and **a separate UWP SDL3** | Dawn, `nod`, `libuwp`, libpng, zlib — and SDL3, which goes separately for the reason in §4 |
| **Python 3** | The scripts |
| **An Xbox in Developer Mode** and a certificate | Installing, and signing |

### The environment variables

The scripts carry no machine's paths inside them: they read these five variables, set once per
terminal session.

```powershell
$env:MKW_TOOLKIT  = "C:\mkw\Toolkit\llvm-mingw\bin"   # Wiicompiled's clang and ld.lld
$env:MKW_UWP_DEP  = "C:\mkw\uwp-dep\x64"               # the bundle (has include\ and lib\)
$env:MKW_UWP_SDL  = "C:\mkw\uwp-dep-sdl\x64"           # the UWP SDL3, separately
$env:MKW_XBOX     = "C:\mkw\xbox"                       # where package\ and the output live
$env:MKW_BASE_PC  = "C:\mkw\Install\Base"              # Wiicompiled's Base folder
```

If one is missing, the script stops saying **which** and what it is for, instead of failing later
with something unreadable.

There is a sixth, `MKW_BUILDWORKSPACE`, which **you normally do not set**: the
`Install\BuildWorkspace` folder is worked out from the paths inside step 2's
`compile_commands.json`. Set it only if the script says it could not work it out.

---

## 2. Build the PC product first

That is where the port's input comes from: the `build.ninja` of whichever profile you want — the
base game, Retro Rewind, or both — and its compilation database.

```powershell
# in Wiicompiled's native build folder
ninja -t compdb > compile_commands.json
```

That **compilation database** is the input to everything below: nothing has to be reconfigured with
CMake, because the PC build already carries the rules.

⚠ **Build it and test it on the PC before going on.** If it does not run there, it will not run on
the console.

---

## 3. The patches

**Aurora** (MIT), both parts:

```powershell
git apply --directory=C:\mkw\port\aurora-main patches\aurora-uwp.patch
python tools\parche-aurora.py C:\mkw\port\aurora-main
```

The script is idempotent and all-or-nothing: each change checks its anchor before writing, and if
one does not match it says so without leaving the file half done.

**Wiicompiled's runtime**: the twelve changes are described one by one in
[`HOW-IT-WORKS.md`](HOW-IT-WORKS.md) — which file, what happens, and what to do. They are not a
patch here because Wiicompiled publishes no license that would allow it; that section *is* the
recipe.

All of the delta sits behind `MKW_UWP` (runtime) and `AURORA_WINDOWS_STORE` (Aurora), so the same
tree **still builds for the PC**.

---

## 4. The UWP SDL3, which goes separately

The main bundle carries a **desktop** `SDL3.dll`: it imports `MSVCP140.dll` without the `_APP`
suffix, and an App Container will not load it. You need an SDL3 built for UWP, in its own folder
(`MKW_UWP_SDL`), and the link takes `SDL3.lib` from there and nowhere else.

---

## 5. A certificate, and your identity in the manifest

```powershell
$c = New-SelfSignedCertificate -Type Custom -Subject "CN=YourName" `
       -KeyUsage DigitalSignature -FriendlyName "UWP signing" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$c.Thumbprint
```

And in `package\Package.appxmanifest`, the `CHANGE-ME`s: `Identity Name`, `Publisher` (**identical**
to the certificate's subject), `PublisherDisplayName` and `PhoneProductId` (`[guid]::NewGuid()`).

⚠ **The package version is set by this manifest by hand**, not by the packer, and it has to go up
for every new package: the console will not replace a package with one of the same version.

---

## 6. Compile, link, package

**Compile, twice.** The second pass is not optional: it brings ImGui, and without it the link leaves
20 symbols unresolved.

```powershell
tools\compilar.cmd C:\mkw\compile_commands.json C:\mkw\obj      --overlay=C:\mkw\port
tools\compilar.cmd C:\mkw\compile_commands.json C:\mkw\obj-deps --overlay=C:\mkw\port --solo=deps
```

**Link**, saying which product you want:

```powershell
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\RetroRewind.exe retro
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\WiiCompiled.exe  base
```

⚠ That last argument is not decorative: the build leaves **both products'** objects in the same
folder, and the other one's have to be left out. If they are not, the game boots, draws the splash
and exits without writing anything ([`HOW-IT-WORKS.md`](HOW-IT-WORKS.md)).

**Package and sign:**

```powershell
python tools\empaquetar-uwp.py C:\mkw\build\RetroRewind.exe C:\mkw\build\RetroRewind.msix package
```

---

## 7. Installing it on the console

### Before touching anything: how the console has to be

- **In Developer Mode**, with Dev Home installed.
- **On, and with your profile signed in.** ⚠ With no user signed in the console **will not launch
  apps**: the package installs, shows up in the list, and launching it does nothing.
- **On the same network as your PC**, with its address at hand (Dev Home shows it). The Device
  Portal listens on port **11443** over HTTPS and asks for the username and
  password you set in Dev Home.

Open `https://<ip>:11443`. ⚠ The browser will warn that the site's certificate is not trusted: it is
the console's own. Go in anyway — in Edge and Chrome, **Advanced** → **Continue to … (unsafe)**; in
Firefox, **Advanced** → **Accept the Risk and Continue**.

In **My games & apps → Add**: your `.msix`, and under **Dependency** the Windows SDK's
`Microsoft.VCLibs.x64.14.00.appx` the first time (the manifest declares it, and without it
activation fails with `0x8027025B`). **Certificate** is not needed: Developer Mode accepts any
signed package.

If it says `There is not enough space on the disk`, it is not full: the first install of a family
goes to `D:\DevelopmentFiles`, about 5 GB. Install a *seed* first — same identity, lower version.

---

## 8. The game and the mod, inside the package

The data goes into the app's `LocalState`, through the Device Portal's **File explorer**. The first
launch creates the folders; upload before that and the portal says it cannot find the path.

- the game content Wiicompiled expects, as it leaves it on the PC;
- and, for Retro Rewind, its whole `RetroRewind6\` folder: tracks, menus and translations are read
  **live at startup**, so changing the mod does not mean recompiling anything.

The log is at `LocalState\WiiCompiled\Logs\uwp-console.txt`. On a console it is all you have.

---

## If something goes wrong

| Symptom | Cause |
|---|---|
| The package installs and launching does nothing | Is a **profile signed in**? And read the log: the first launch with no data does nothing visible |
| Activation fails with `0x8027025B` | The VCLibs dependency is missing, **or** the `.exe` was linked without `/subsystem:windows,10.0` |
| Boots, splash, exits with no log | Both `indirect_dispatch` objects in the same link (§6) |
| 20 unresolved ImGui symbols | The second compile pass is missing (§6) |
| "cannot load SDL3", or an `MSVCP140.dll` error | The `SDL3.dll` is the desktop one (§4) |
| `vcvarsall fallo`, or `'m' is not recognized` | A `.cmd` saved with Unix line endings. They have to be CRLF; this repository's `.gitattributes` pins that |
| A missing environment variable | The script says which one and what it is for (§1) |

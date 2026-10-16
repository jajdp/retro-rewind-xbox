"""Fase 1: arma el paquete .msix del port UWP de Mario Kart Wii y lo firma.

Uso:  python empaquetar-uwp.py <exe enlazado> <salida.msix> [carpeta_package] [huella]

La huella es la de TU certificado de firma (40 digitos hexadecimales); tambien se puede dar
en la variable de entorno MKW_CERT. La ves con:
    Get-ChildItem Cert:\\CurrentUser\\My | Format-List Subject, Thumbprint

`carpeta_package` (por defecto `xbox\\package`) es la que aporta el `Package.appxmanifest` y
los mosaicos `Assets\\`. Se parametrizo el 2026-09-20 para poder empaquetar **Retro Rewind**
con su propia identidad (`WiiCompiled-RetroRewind`) sin tocar la del juego base: son paquetes
distintos, asi que conviven en la consola y cada uno tiene su LocalState.

Necesita makeappx.exe y signtool.exe del Windows SDK (se buscan) y un certificado de firma en
Cert:\\CurrentUser\\My con clave privada. Uno autofirmado sirve: docs/INSTALL.es.md §5.

Contenido del paquete: el exe, las DLL de uwp-dep (SDL3, Dawn, nod, dxcompiler, dxil, libpng,
zlib, libuwp), los recursos que el runtime lee junto al ejecutable (dsp_coef.bin,
initial_pipeline_cache.db, wii_bootstrap\\), el manifiesto y los mosaicos. Los assets del juego
(2,6 GB) NO van dentro: se suben a LocalState por el Device Portal.
"""
import shutil
import subprocess
import os
import re
import sys
from pathlib import Path

# Las tres rutas que esto necesita vienen por variable de entorno, porque los .cmd de la tuberia
# se llaman en cadena y asi se ponen una sola vez (docs/INSTALL.es.md §2):
#
#   MKW_TOOLKIT   el llvm-mingw que trae Wiicompiled (clang y ld.lld con el ABI de MSVC)
#   MKW_UWP_DEP   el bundle de dependencias de UWP, carpeta x64 (Dawn, nod, libuwp, libpng, zlib)
#   MKW_UWP_SDL   el SDL3 para UWP, carpeta x64 (va aparte: ver docs/HOW-IT-WORKS.es.md)


def _entorno(nombre, que):
    """La ruta que dice la variable de entorno `nombre`, o un error que explica cual falta."""
    import os
    v = os.environ.get(nombre)
    if not v:
        raise SystemExit('falta la variable de entorno %s (%s). docs/INSTALL.es.md §2.'
                         % (nombre, que))
    p = Path(v)
    if not p.exists():
        raise SystemExit('%s apunta a algo que no existe: %s' % (nombre, p))
    return p

# El Windows SDK, buscado y no fijado a una version: una ruta a mano es la forma mas rapida de que
# esto deje de funcionar en la maquina de al lado.
def _sdk_bin():
    kits = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")
    if kits.is_dir():
        for d in sorted(kits.iterdir(), reverse=True):
            if (d / "x64" / "makeappx.exe").is_file():
                return d / "x64"
    raise SystemExit('no encuentro makeappx.exe en ninguna version del Windows SDK bajo %s' % kits)


SDK_BIN = _sdk_bin()
MAKEAPPX = SDK_BIN / "makeappx.exe"
SIGNTOOL = SDK_BIN / "signtool.exe"

# La huella SHA-1 de TU certificado de firma, en tu almacen personal. Se da por variable de entorno
# o por el cuarto argumento; aqui no va ninguna, porque un certificado es de quien lo crea.
#   Get-ChildItem Cert:\CurrentUser\My | Format-List Subject, Thumbprint
HUELLA = None  # se resuelve en main()

XBOX = _entorno('MKW_XBOX', 'la carpeta del lane Xbox, con package\\ y uwp-dep\\')
BASE_PC = _entorno('MKW_BASE_PC', 'la carpeta Base de Wiicompiled')
UWP_DEP_BIN = XBOX / "uwp-dep" / "x64" / "bin"
DLLS = ["SDL3.dll", "webgpu_dawn.dll", "nod.dll", "dxcompiler.dll", "dxil.dll", "libpng16.dll", "z.dll", "libuwp.dll"]
RECURSOS = ["dsp_coef.bin", "initial_pipeline_cache.db"]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    exe = Path(sys.argv[1])
    salida = Path(sys.argv[2])
    paquete = Path(sys.argv[3]) if len(sys.argv) > 3 else (XBOX / "package")
    global HUELLA
    HUELLA = (sys.argv[4] if len(sys.argv) > 4 else os.environ.get("MKW_CERT", "")).strip()
    HUELLA = HUELLA.replace(" ", "").replace(":", "")
    if not re.fullmatch(r"[0-9A-Fa-f]{40}", HUELLA):
        raise SystemExit(
            "falta la huella de tu certificado: cuarto argumento o variable MKW_CERT, 40\n"
            "digitos hexadecimales. La ves con: Get-ChildItem Cert:\\CurrentUser\\My | "
            "Format-List Subject, Thumbprint  (docs/INSTALL.es.md §5)")
    raiz = salida.parent / "contenido"
    if raiz.exists():
        shutil.rmtree(raiz)  # carpeta de trabajo propia, regenerable
    raiz.mkdir(parents=True)
    shutil.copy2(exe, raiz / "WiiCompiled.exe")
    for d in DLLS:
        # SDL3.dll: build UWP de verdad (commit ae39aa0 de uwp-dep, el de Dusklight); la de la rama
        # dawnlight es de escritorio y no carga en AppContainer.
        origen = (XBOX / "uwp-dep-sdl" / "x64" / "bin" / d) if d == "SDL3.dll" else (UWP_DEP_BIN / d)
        shutil.copy2(origen, raiz / d)
    for r in RECURSOS:
        shutil.copy2(BASE_PC / r, raiz / r)
    shutil.copytree(BASE_PC / "wii_bootstrap", raiz / "wii_bootstrap")
    shutil.copytree(paquete / "Assets", raiz / "Assets")
    shutil.copy2(paquete / "Package.appxmanifest", raiz / "AppxManifest.xml")
    print(f"manifiesto: {paquete / 'Package.appxmanifest'}")
    total = sum(p.stat().st_size for p in raiz.rglob("*") if p.is_file())
    print(f"contenido: {sum(1 for p in raiz.rglob('*') if p.is_file())} archivos, {total/1048576:.1f} MB")

    if salida.exists():
        salida.unlink()
    p = subprocess.run([str(MAKEAPPX), "pack", "/o", "/d", str(raiz), "/p", str(salida)], capture_output=True, text=True, errors="replace")
    print(p.stdout[-1500:], p.stderr[-1500:])
    if p.returncode != 0:
        return p.returncode
    p = subprocess.run([str(SIGNTOOL), "sign", "/fd", "SHA256", "/sha1", HUELLA, "/s", "My", str(salida)], capture_output=True, text=True, errors="replace")
    print(p.stdout[-800:], p.stderr[-800:])
    if p.returncode == 0:
        print(f"OK: {salida} ({salida.stat().st_size:,} bytes)")
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())

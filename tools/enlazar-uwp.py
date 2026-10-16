"""Fase 1: enlaza los objetos compilados por compile_check.py (modo --overlay) en un
WiiCompiled.exe para UWP/Xbox (AppContainer) con el lld de llvm-mingw en modo link.

Uso:  python enlazar_uwp.py <obj_runtime> <obj_deps> <salida.exe> [--excluir=a,b,c]
Hay que lanzarlo con el entorno «store» de Visual Studio (LIB apuntando a las bibliotecas
de la tienda): ver lanzar.cmd / enlazar.cmd.

`--excluir=` aparta los objetos cuyo nombre contenga alguno de esos textos. Hace falta
desde el 2026-09-20, cuando la compilacion pasó a traer DOS productos a la vez (el juego
base y Retro Rewind) en la misma carpeta de objetos: comparten runtime, aurora y los
shards `base_common`, y solo se diferencian en tres grupos. Enlazarlos todos juntos
duplica simbolos, asi que cada ejecutable aparta los del otro:

    Retro Rewind  --excluir=shards_base_portable_sensitive_,shards_base_registration_
    juego base    --excluir=shards_retro_mod_,shards_retro_portable_sensitive_,shards_retro_rewind_registration_

(Los grupos salen de la orden de enlazado real del build de PC, en `build.ninja`.)
"""
import os
import subprocess
import sys
import time
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

TOOLKIT = _entorno('MKW_TOOLKIT', 'el llvm-mingw de Wiicompiled')
LLD = TOOLKIT / "ld.lld.exe"
UWP_DEP = _entorno('MKW_UWP_DEP', 'el bundle de dependencias de UWP')

# Objetos que no van al ejecutable: pruebas, el main() de aurora (el runtime trae el suyo) y
# el escritorio de aurora que no aplica.
EXCLUIR = ("runtime_tests_", "aurora-main_lib_main.cpp", "aurora-main_examples_")

LIBS_UWP_DEP = ["SDL3.lib", "webgpu_dawn.lib", "nod.lib", "libuwp.lib", "libpng16.lib", "z.lib", "dxcompiler.lib"]
LIBS_SISTEMA = ["WindowsApp.lib", "OneCore.lib", "ntdll.lib", "dxgi.lib", "ws2_32.lib", "msvcrt.lib", "msvcprt.lib", "vcruntime.lib", "ucrt.lib"]


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    dirs = [Path(sys.argv[1]), Path(sys.argv[2])]
    salida = Path(sys.argv[3])
    excluir = EXCLUIR + tuple(
        x for a in sys.argv[4:] if a.startswith("--excluir=")
        for x in a.split("=", 1)[1].split(",") if x)
    if len(excluir) > len(EXCLUIR):
        print("excluidos ademas: " + ", ".join(excluir[len(EXCLUIR):]))
    salida.parent.mkdir(parents=True, exist_ok=True)
    objetos = []
    vistos = set()
    apartados = 0
    for d in dirs:
        for o in sorted(d.glob("*.obj")):
            if any(x in o.name for x in excluir):
                apartados += 1
                continue
            # zlib y libpng los aporta uwp-dep (z.lib, libpng16.lib): sus objetos propios duplican símbolos
            if o.name.startswith(("Dependencies_zlib_", "Dependencies_png_", "Dependencies_libpng", "Dependencies_SDL_", "Dependencies_libusb")):
                continue
            if o.name in vistos:  # el mismo TU compilado en las dos carpetas (uwp_main.cpp)
                continue
            vistos.add(o.name)
            objetos.append(str(o))
    # Aurora y las dependencias van en archivos estáticos, como en el build de PC: el enlazador
    # toma solo lo que el runtime usa (los módulos dvd/gd de Aurora, por ejemplo, reclaman
    # OSPanic/DCFlushRange y en PC nunca se enlazan).
    directos, en_aurora, en_deps = [], [], []
    for o in objetos:
        n = Path(o).name
        if "_port_aurora-main_" in n:
            en_aurora.append(o)
        elif n.startswith("Dependencies_") or n.startswith("native-build_"):
            en_deps.append(o)
        else:
            directos.append(o)
    AR = TOOLKIT / "llvm-ar.exe"
    libs_propias = []
    for nombre, miembros in (("aurora_uwp.lib", en_aurora), ("deps_uwp.lib", en_deps)):
        lib = salida.parent / nombre
        if lib.exists():
            lib.unlink()
        rsp_ar = salida.parent / (nombre + ".rsp")
        rsp_ar.write_text("\n".join(f'"{m}"' for m in miembros), encoding="utf-8")
        p = subprocess.run([str(AR), "rcs", str(lib), f"@{rsp_ar}"], capture_output=True, text=True, errors="replace")
        if p.returncode != 0:
            print("llvm-ar falló:", p.stderr[-500:])
            return 3
        libs_propias.append(str(lib))
    objetos = directos
    print(f"objetos directos: {len(directos)}  aurora_uwp.lib: {len(en_aurora)}  "
          f"deps_uwp.lib: {len(en_deps)}  apartados: {apartados}")
    rsp = salida.with_suffix(".rsp")
    lineas = [f'"{o}"' for o in objetos] + [f'"{l}"' for l in libs_propias]
    # SDL3: la rama dawnlight de uwp-dep trae un SDL3.dll de ESCRITORIO (importa MSVCP140.dll sin
    # _APP) que no carga en AppContainer; se usa el del commit ae39aa0, el mismo de Dusklight.
    SDL_UWP = UWP_DEP.parent.parent / "uwp-dep-sdl" / "x64"
    lineas += [f'"{(SDL_UWP if l == "SDL3.lib" else UWP_DEP) / "lib" / l}"' for l in LIBS_UWP_DEP]
    lineas += LIBS_SISTEMA
    rsp.write_text("\n".join(lineas), encoding="utf-8")
    # /subsystem:windows,10.0: un AppContainer exige versión de subsistema/OS >= 6.2 en la cabecera
    # PE; lld pone 6.0 por defecto y el activador de UWP responde 0x8027025B sin más explicación.
    cmd = [str(LLD), "-flavor", "link", "/nologo", "/machine:x64", "/subsystem:windows,10.0", "/appcontainer",
           "/dynamicbase", "/nxcompat", "/largeaddressaware", "/opt:ref", "/opt:icf",
           "/nodefaultlib:libcmt", "/nodefaultlib:libcpmt", "/nodefaultlib:libvcruntime", "/nodefaultlib:libucrt",
           f"/libpath:{UWP_DEP / 'lib'}", f"/out:{salida}", f"@{rsp}"]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    err = p.stderr + p.stdout
    (salida.parent / "enlace.log").write_text(err, encoding="utf-8")
    faltan = sorted(set(l.split("undefined symbol:", 1)[-1].strip() for l in err.splitlines() if "undefined symbol:" in l))
    print(f"lld rc={p.returncode} en {time.time() - t0:.1f} s; símbolos sin resolver: {len(faltan)}")
    for s in faltan[:60]:
        print("  ", s[:160])
    if p.returncode == 0 and salida.exists():
        print(f"OK: {salida} ({salida.stat().st_size:,} bytes)")
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())

"""Genera los mosaicos PNG que exige el manifiesto UWP a partir del icono extraído
del ejecutable de Wiicompiled (pc\\mkw.ico). Fondo azul oscuro, icono centrado al 80 %."""
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

from PIL import Image

BASE = _entorno('MKW_PROYECTO', 'la raiz del proyecto')
SALIDA = BASE / "xbox" / "package" / "Assets"

TILES = {
    "Square44x44Logo.scale-200.png": (88, 88),
    "Square44x44Logo.targetsize-24_altform-unplated.png": (24, 24),
    "Square150x150Logo.scale-200.png": (300, 300),
    "Wide310x150Logo.scale-200.png": (620, 300),
    "StoreLogo.png": (50, 50),
    "SplashScreen.scale-200.png": (1240, 600),
    "LockScreenLogo.scale-200.png": (48, 48),
    # Sin calificador de escala: makeappx sin resources.pri exige el nombre exacto del manifiesto
    "Square44x44Logo.png": (88, 88),
    "Square150x150Logo.png": (300, 300),
    "Wide310x150Logo.png": (620, 300),
    "SplashScreen.png": (1240, 600),
    "LockScreenLogo.png": (48, 48),
}


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    ico = Image.open(BASE / "pc" / "mkw.ico")
    try:
        ico.size = max(ico.ico.sizes())  # la variante mas grande que traiga el .ico
    except Exception:
        pass
    origen = ico.convert("RGBA")
    print("icono origen", origen.size)
    for nombre, (w, h) in TILES.items():
        lienzo = Image.new("RGBA", (w, h), (24, 24, 40, 255))
        lado = int(min(w, h) * 0.8)
        icono = origen.resize((lado, lado), Image.LANCZOS)
        lienzo.alpha_composite(icono, ((w - lado) // 2, (h - lado) // 2))
        lienzo.save(SALIDA / nombre)
        print("  ", nombre, w, h)


if __name__ == "__main__":
    main()

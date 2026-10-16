# -*- coding: utf-8 -*-
"""Los cambios de UWP en Aurora que no van en patches/aurora-uwp.patch.

`patches/aurora-uwp.patch` es el parche grande de Aurora para UWP: 22 archivos, sobre todo CMake,
el proveedor de Dawn y la capa de GX. Estos 7 cambios de aqui son los que salieron despues, al
hacer que el juego arrancara de verdad en la consola, y van como script en vez de diff porque cada
uno comprueba su ancla antes de escribir: asi te dicen que no cuadra en vez de dejar el arbol a
medias.

Todo el delta queda bajo `AURORA_WINDOWS_STORE`, asi que el mismo arbol sigue compilando para PC.
Idempotente: si el texto nuevo ya esta, no toca nada.

    python tools/parche-aurora.py <ruta de aurora-main>

Aurora es MIT, (c) 2022 Luke Street: https://github.com/encounter/aurora

Recompilaciones - https://github.com/jajdp/retro-rewind-xbox
"""
import sys
from pathlib import Path

libres = [a for a in sys.argv[1:] if not a.startswith('-')]
if not libres:
    sys.exit('uso: parche-aurora.py <ruta de aurora-main>')
AURORA = Path(libres[0]).resolve()
for sena in ('CMakeLists.txt', 'lib/aurora.cpp'):
    if not (AURORA / sena).exists():
        sys.exit('no es la raiz de aurora-main (falta %s): %s' % (sena, AURORA))

P = []  # (archivo relativo, viejo, nuevo, veces)

P.append(("lib/logging.cpp",
r'''#if defined(_WIN32)
    ::MessageBoxA(nullptr, body.c_str(), "Aurora fatal error",''',
r'''#if defined(_WIN32) && !defined(AURORA_WINDOWS_STORE)
    ::MessageBoxA(nullptr, body.c_str(), "Aurora fatal error",''', 1))

P.append(("lib/window.cpp",
r'''#if defined(_WIN32)
WNDPROC g_prevWindowProc = nullptr;''',
r'''#if defined(_WIN32) && !defined(AURORA_WINDOWS_STORE)
WNDPROC g_prevWindowProc = nullptr;''', 1))

P.append(("lib/window.cpp",
r'''#if defined(_WIN32)
  const uint64_t cached = g_nativeClientSize.load(std::memory_order_acquire);''',
r'''#if defined(_WIN32) && !defined(AURORA_WINDOWS_STORE)
  const uint64_t cached = g_nativeClientSize.load(std::memory_order_acquire);''', 1))

P.append(("lib/window.cpp",
r'''#if defined(_WIN32)
  install_window_proc_hook();''',
r'''#if defined(_WIN32) && !defined(AURORA_WINDOWS_STORE)
  install_window_proc_hook();''', 1))

P.append(("lib/window.cpp",
r'''#if defined(_WIN32)
  uninstall_window_proc_hook();''',
r'''#if defined(_WIN32) && !defined(AURORA_WINDOWS_STORE)
  uninstall_window_proc_hook();''', 1))

P.append(("lib/dawn/BackendBinding.cpp",
r'''#elif defined(SDL_PLATFORM_WIN32)
  std::shared_ptr<wgpu::SurfaceSourceWindowsHWND> desc = std::make_shared<wgpu::SurfaceSourceWindowsHWND>();''',
r'''#elif defined(SDL_PLATFORM_WINRT)
  // UWP/Xbox: la ventana de SDL3-uwp es una CoreWindow; Dawn (D3D12) la acepta directamente.
  std::shared_ptr<wgpu::SurfaceDescriptorFromWindowsCoreWindow> desc =
      std::make_shared<wgpu::SurfaceDescriptorFromWindowsCoreWindow>();
  desc->coreWindow = SDL_GetPointerProperty(props, SDL_PROP_WINDOW_WINRT_WINDOW_POINTER, nullptr);
  return std::move(desc);
#elif defined(SDL_PLATFORM_WIN32)
  std::shared_ptr<wgpu::SurfaceSourceWindowsHWND> desc = std::make_shared<wgpu::SurfaceSourceWindowsHWND>();''', 1))

P.append(("lib/input.cpp",
r'''  ASSERT(SDL_Init(SDL_INIT_HAPTIC | SDL_INIT_JOYSTICK | SDL_INIT_GAMEPAD), "Failed to initialize SDL subsystems: {}",
         SDL_GetError());''',
r'''#if defined(AURORA_WINDOWS_STORE)
  ASSERT(SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMEPAD), "Failed to initialize SDL subsystems: {}", SDL_GetError());
#else
  ASSERT(SDL_Init(SDL_INIT_HAPTIC | SDL_INIT_JOYSTICK | SDL_INIT_GAMEPAD), "Failed to initialize SDL subsystems: {}",
         SDL_GetError());
#endif''', 1))


def main():
    hechos, saltados = [], 0
    for archivo, viejo, nuevo, veces in P:
        p = AURORA / archivo
        if not p.is_file():
            sys.exit('no existe %s' % p)
        crudo = p.read_bytes().decode('utf-8')
        eol = '\r\n' if '\r\n' in crudo else '\n'
        texto = crudo.replace('\r\n', '\n')
        if nuevo in texto:
            saltados += 1
            continue
        n = texto.count(viejo)
        if n != veces:
            sys.exit('%s: %d apariciones de %r (esperaba %d). El arbol no es el que este parche\n'
                     'espera: comprueba que aurora-main sale de la copia de Wiicompiled y que\n'
                     'patches/aurora-uwp.patch ya esta aplicado.' % (archivo, n, viejo[:70], veces))
        texto = texto.replace(viejo, nuevo)
        tmp = p.with_suffix(p.suffix + '.tmp')
        tmp.write_bytes(texto.replace('\n', eol).encode('utf-8'))
        tmp.replace(p)
        hechos.append(archivo)
    if hechos:
        print('puestos: %s' % ', '.join(sorted(set(hechos))))
    if saltados:
        print('ya estaban: %d de %d' % (saltados, len(P)))
    if not hechos and not saltados:
        print('nada que hacer')
    return 0


if __name__ == '__main__':
    sys.exit(main())

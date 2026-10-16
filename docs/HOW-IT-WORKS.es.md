# Cómo funciona, y por qué cada cosa está ahí

*(English: [HOW-IT-WORKS.md](HOW-IT-WORKS.md))*

## De dónde sale

**Wiicompiled no emula: recompila.** De tu disco de *Mario Kart Wii* saca un ejecutable nativo de
Windows, y para dar el papel del hardware de la Wii usa [Aurora](https://github.com/encounter/aurora)
—la capa de GX, mando, tarjeta de memoria y ventana, sobre WebGPU (Dawn) y SDL3—.

Retro Rewind entra en esa recompilación por **un solo archivo**, su `Code.pul`; las pistas, los
menús y las traducciones se leen **en vivo al arrancar** desde su carpeta. Por eso el mod se cambia
sin recompilar nada, y por eso aquí hay un solo port que vale para los dos productos.

Lo que este repositorio añade es la mitad de UWP: que todo eso quepa dentro de un App Container.

## Las dos trampas que costaron el port

### `0x8027025B`, y la versión del subsistema

La activación de un paquete puede fallar con `0x8027025B` **sin una palabra más**. Hay dos causas, y
conviene tener las dos en la cabeza porque el mensaje es el mismo:

1. **Falta la dependencia de VCLibs** en el manifiesto. Meter las DLL dentro del paquete no la
   sustituye.
2. **La cabecera PE dice que el subsistema es 6.0.** `lld` lo pone así por defecto, y un App
   Container exige **6.2 o más**. El arreglo es `/subsystem:windows,10.0` en el enlazado — una
   opción, y dos días de buscar.

### Dos productos, dos `indirect_dispatch`

La compilación deja en **la misma carpeta** los objetos del juego base y los de Retro Rewind:
comparten el runtime, Aurora, las librerías y los shards comunes, y solo se diferencian en tres
grupos. Entre esos grupos hay, por producto, un objeto `indirect_dispatch` **cuyo nombre lleva un
hash**, así que no salta a la vista.

Enlazar los dos **no da error**: los símbolos no chocan. Lo que pasa es que el juego arranca, pinta
el splash de UWP y se cierra **sin escribir ni una línea de registro**. Eso costó la primera tanda
entera.

De ahí el último argumento de `tools/enlazar.cmd`, y de ahí que las listas de lo que se aparta salgan
de la **orden de enlazado real del build de PC** (`build.ninja`), que es la única fuente fiable de
qué objeto pertenece a qué producto.

## Las otras tres del enlazado y la compilación

- **La compilación va en dos pasadas.** La segunda (`--solo=deps`) aporta ImGui; sin ella quedan 20
  símbolos de ImGui sin resolver.
- **El `SDL3.dll` del bundle principal es de escritorio**: importa `MSVCP140.dll` sin `_APP`, y un
  App Container no lo carga. El SDL3 de UWP va en su propia carpeta, y el enlazado toma `SDL3.lib`
  de ahí.
- **Aurora y las dependencias van en archivos estáticos**, como en el build de PC, en vez de objeto
  a objeto: así el enlazador toma solo lo que el runtime usa. Los módulos `dvd` y `gd` de Aurora, por
  ejemplo, reclaman símbolos que en PC nunca se enlazan.

## Lo primero de todo: poder ver algo

**En UWP no hay consola**, y ahí es donde el runtime escribe sus errores. Mientras eso no se
arreglara, todos los fallos de arriba eran «arranca y se cierra».

El cambio es redirigir `stdout` y `stderr` a un archivo del `LocalState`
(`WiiCompiled\Logs\uwp-console.txt`), sin búfer. Es el primero que hay que hacer y el que convierte
el resto del trabajo en algo medible.

## Los doce cambios del runtime de Wiicompiled

Aquí no van como parche: Wiicompiled no publica licencia propia, así que este repositorio **no
copia ni una línea de su código** ([`NOTICE.es.md`](../NOTICE.es.md)). Lo que sigue es la
descripción de qué hay que cambiar y por qué, archivo por archivo. Son 29 cambios en 10 archivos,
agrupados por el problema que resuelven; todos van detrás de `MKW_UWP`, de modo que el mismo árbol
siga compilando para PC.

| Archivo | Qué pasa, y qué hace el cambio |
|---|---|
| `include/runtime_config.h` | Pide la carpeta de datos del usuario con `SHGetKnownFolderPath`, que **en UWP no existe**. En su lugar devuelve la carpeta de datos de la aplicación |
| `src/platform/host_platform.cpp` (2) | Es quien resuelve esa carpeta: dentro de un App Container la única escribible **y visible por el Device Portal** es el `LocalState` del paquete, que se obtiene con `SDL_GetPrefPath`. Hay que incluir las cabeceras de SDL para eso |
| `src/main.cpp` (14) | El grueso. El punto de entrada pasa a ser el de WinRT (un `uwp_main.cpp` propio, que es el que SDL3 arranca); fuera la consola y las tuberías —la CRT de UWP no expone `_pipe()`—; fuera los `MessageBox` de error, que en una consola nadie ve; fuera `DbgHelp`; y el registro al archivo del `LocalState`. Además, `SDL_Init` se pide **sin háptica**, que ese SDL no trae |
| `src/host_context.cpp` (2) | Las fibras: en la familia UWP la variante que existe es la **`Ex`** (`CreateFiberEx`, `ConvertThreadToFiberEx`), no la de siempre |
| `src/guest_flat_memory.cpp` | El SDK **no declara** los manejadores vectoriales de excepciones para la familia de aplicaciones, aunque `kernel32` sí los exporta: hay que declararlos a mano. Sin ellos no hay forma de atrapar los accesos a la memoria del invitado |
| `src/memory.cpp` | Lo mismo, del lado del mapa de memoria |
| `src/host_cpu_baseline.cpp` (4) | La comprobación del procesador y del entorno que hace el arranque, con llamadas que en UWP no están disponibles |
| `src/hle/net/network_ssl.cpp` | La capa de red usa **Schannel**, que un App Container no tiene: se sustituye por stubs. El juego no usa internet en local |
| `src/discord_presence.cpp` | Habla por una **tubería con nombre**, y eso no existe dentro de un App Container: fuera |
| `third_party/cryptopp/zdeflate.cpp` (2) | Usa `stdext`, una extensión de MSVC que **clang no tiene**, y aquí se compila con clang |

## Aurora, que sí va aquí

Dos piezas, porque se hicieron en dos momentos:

- **`patches/aurora-uwp.patch`** (22 archivos): el CMake, el proveedor de Dawn, el de SDL3, el de
  `nod`, la copia de las DLL, la capa de GX y las rutas de tarjeta. Es lo que hace que Aurora
  *compile* para `WindowsStore`.
- **`tools/parche-aurora.py`** (7 cambios): lo que hizo falta para que *arrancara*. El más
  interesante es la superficie de dibujo — **la ventana de SDL3 en UWP es una `CoreWindow`, y Dawn
  (D3D12) la acepta directamente**, así que no hay que inventar nada: solo pasársela. Los otros son
  la entrada y el registro sin consola.

Los dos van detrás de `AURORA_WINDOWS_STORE`.

## Lo que no está resuelto

- **La suspensión del modo desarrollador**: al volver de Home, el juego empieza de nuevo. Resolverlo
  exige guardar y restaurar el estado entero, y eso aquí no está.
- El rendimiento medido es **58 FPS** en la Xbox Series X, contra 60 en PC. No se ha perseguido la
  diferencia.

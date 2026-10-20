# Mario Kart Wii y Retro Rewind en la Xbox — el port UWP

Cómo coger lo que **Wiicompiled** produce a partir de tu disco de *Mario Kart Wii* —un ejecutable
nativo, no un emulador— y hacerlo correr **en una Xbox Series X en modo desarrollador**, como un
paquete UWP que compilas y firmas tú. Con o sin
[Retro Rewind](https://github.com/RetroRewind-Team), la distribución de pistas y personajes de
fans.

*(English: [README.md](README.md))*

No es una teoría: los dos productos arrancan, se ven, suenan y se juegan con mando en la consola, a
**58 FPS**, con sus partidas en el `LocalState` del paquete.

## En qué consola se probó

**En una Xbox Series X**, en modo desarrollador. Las dos consolas en las que se construyó y se probó esto
son Series X, así que es el único hardware al que se refiere cualquier cosa que se afirme aquí.

**En una Series S no se ha probado nunca, ni una vez.** Es otra máquina: menos memoria disponible para un
juego y una GPU más floja. Puede que funcione en una, puede que vaya más despacio, o puede que no
arranque; nada de aquí se ha medido en ella. Si lo ejecutas en una Series S, lo que obtengas no es lo que
dice este README, y ninguna de las cifras de aquí es una promesa sobre esa consola.

## Qué es este repositorio

**La mitad de UWP de ese port, y las herramientas que la aplican.** Wiicompiled compila para
escritorio; esto es lo que hay que cambiar y cómo hay que compilar, enlazar y empaquetar para que el
resultado viva dentro de un App Container de Xbox.

| Pieza | Qué es |
|---|---|
| `patches/aurora-uwp.patch` | 22 archivos de [Aurora](https://github.com/encounter/aurora) (MIT), la capa que hace de GX, mando y ventana: su CMake, el proveedor de Dawn, el de SDL3, la capa de GX y las rutas de tarjeta |
| `tools/parche-aurora.py` | Los siete cambios de Aurora que salieron después, haciendo que el juego arrancara de verdad: la superficie de CoreWindow para Dawn, la entrada y el registro sin consola |
| `tools/compilar.cmd` + `compile-check.py` | La pasada de compilación, dentro del entorno **store** de Visual Studio. **Hay que llamarla dos veces** |
| `tools/enlazar.cmd` + `enlazar-uwp.py` | El enlazado con `ld.lld`. Aquí viven las dos trampas más caras del port |
| `tools/empaquetar-uwp.py` | El layout del paquete, `makeappx` y `signtool` |
| `package/` | El manifiesto, con `CHANGE-ME` donde va tu identidad, y el `Config.toml` del runtime |

## Qué **no** es, y una cosa que hay que decir de frente

Aquí no hay **disco, ni contenido del mod, ni ejecutable, ni `.msix`, ni mosaicos, ni las
bibliotecas de UWP** (Dawn, SDL3, `libuwp`), que son binarios de otros.

Y, sobre todo: **aquí no hay ningún parche para el runtime de Wiicompiled.** Wiicompiled no publica
ninguna licencia propia —solo las del código de terceros que incluye—, así que de su código no se
copia **ni una línea**, igual que en los otros ports de este catálogo con los proyectos que no dan
permiso. Los **doce cambios** que su runtime necesita están **descritos uno a uno** en
[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md): qué archivo, qué hay que hacerle y por qué.
Eso es información, no código.

En la práctica: si tienes Wiicompiled, con esta documentación y estas herramientas tienes el port.
Lo que no hay es un botón que lo haga solo en la parte que no nos corresponde publicar.

## Qué hace falta antes

| | |
|---|---|
| **Wiicompiled** | La versión con la que se hizo esto es la **0.2.31**. Él compila tu disco a código nativo; sin él no hay nada que portar |
| **Tu propio disco** | *Mario Kart Wii* PAL `RMCP01`, que es el que Wiicompiled acepta |
| **Retro Rewind** (opcional) | Su `Code.pul` es lo único que se compila; las pistas y los menús se leen en vivo al arrancar |
| **Visual Studio 2022** | Con el componente de **UWP para C++**: hace falta su entorno `store` (`vcvarsall x64 store`), y el `makeappx`/`signtool` del Windows SDK |
| **El llvm-mingw de Wiicompiled** | clang 22 y `ld.lld` con el ABI de MSVC, que es con lo que se compila y se enlaza |
| **El bundle de UWP** | Dawn, `nod`, `libuwp`, libpng y zlib compilados para UWP, y **un SDL3 para UWP aparte** (el del bundle principal es de escritorio: ver la guía) |
| **Python 3** y **una Xbox en modo desarrollador** | Los scripts, y la consola. Más un certificado para firmar |

## Cómo va

```powershell
# 1. Aurora: el parche grande y los siete cambios de después
git apply --directory=<ruta de aurora-main> patches\aurora-uwp.patch
python tools\parche-aurora.py <ruta de aurora-main>

# 2. el runtime de Wiicompiled: los doce cambios de docs/HOW-IT-WORKS.es.md, a mano

# 3. compilar, DOS veces (la segunda trae ImGui)
tools\compilar.cmd <compile_commands.json> C:\mkw\obj      --overlay=C:\mkw\port
tools\compilar.cmd <compile_commands.json> C:\mkw\obj-deps --overlay=C:\mkw\port --solo=deps

# 4. enlazar el producto que quieras
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\RetroRewind.exe retro

# 5. empaquetar y firmar
python tools\empaquetar-uwp.py C:\mkw\build\RetroRewind.exe C:\mkw\build\RetroRewind.msix package
```

Paso a paso, con el lado de la consola: **[`docs/INSTALL.es.md`](docs/INSTALL.es.md)**.

## Qué hubo que resolver

El detalle, con lo que decía el registro en cada caso, está en
**[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md)**.

| | Síntoma | Arreglo |
|---|---|---|
| 1 | La activación responde `0x8027025B` y no dice más | `lld` pone versión de subsistema 6.0 en la cabecera PE, y un App Container exige 6.2 o más: `/subsystem:windows,10.0` |
| 2 | Arranca, pinta el splash de UWP y se cierra **sin escribir un solo registro** | La compilación deja en la misma carpeta los objetos de los **dos productos**, y cada uno trae su propio `indirect_dispatch` con un hash en el nombre. Tener los dos no da error de enlazado: solo mata el juego al arrancar |
| 3 | El enlazado deja 20 símbolos de ImGui sin resolver | La pasada de compilación hay que hacerla **dos veces**; la segunda (`--solo=deps`) es la que trae ImGui |
| 4 | No carga el SDL3 | El bundle principal trae un `SDL3.dll` **de escritorio** (importa `MSVCP140.dll` sin `_APP`), que un App Container no carga. El SDL3 de UWP va aparte |
| 5 | No hay consola, así que no hay forma de ver nada | `stdout` y `stderr` se redirigen a un archivo del `LocalState`. Es lo primero que hay que hacer, porque sin eso ninguno de los demás fallos se ve |
| 6 | El runtime guarda los datos donde el AppContainer no deja | `SHGetKnownFolderPath` no existe en UWP: los datos van al `LocalState` del paquete, por `SDL_GetPrefPath` |
| 7 | Doce sitios más del runtime | Fibras, el manejador de excepciones, `MessageBox`, tuberías, `DbgHelp`, Schannel, Discord y un `stdext` que clang no tiene. Todos descritos en la guía |

## Créditos y licencia

Las herramientas y la receta son de **Recompilaciones**, bajo la [MIT](LICENSE) —la misma de Aurora,
que es el código de terceros que este repositorio parchea—. Aurora es
© 2022 Luke Street. *Mario Kart Wii* es © Nintendo; Retro Rewind es de su propio equipo; Wiicompiled
es de su autor. Este proyecto no está afiliado a ninguno de ellos, ni a Microsoft, y no distribuye
nada que les pertenezca: el detalle está en [`NOTICE.es.md`](NOTICE.es.md). Quien tenga derechos
sobre este material puede escribir a **jajdpmail@gmail.com**.

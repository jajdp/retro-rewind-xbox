# Construir el port y meterlo en la consola

*(English: [INSTALL.md](INSTALL.md))*

Ocho pasos. Los cuatro primeros se hacen una vez.

## 0. Antes de empezar: dónde se escriben las órdenes

Todo lo de esta guía va en **PowerShell**, la terminal normal de Windows: pulsa la tecla
**Windows**, escribe `powershell` y pulsa **Enter** sobre *Windows PowerShell*. Se abre una ventana
con una línea que acaba en `>`; ahí escribes la orden y pulsas **Enter**.

Para ir a una carpeta se usa `cd` con la ruta entre comillas si tiene espacios. Un atajo que ahorra
errores: abre la carpeta en el Explorador, haz clic en la barra de direcciones, escribe `powershell`
encima y pulsa **Enter**.

**No hace falta administrador** en ningún paso de aquí. Y en uno concreto, usarlo lo estropea: el
certificado del §5 se crea en el almacén del usuario que ejecuta la orden, así que elevado acabaría
en el del administrador y `signtool`, corriendo como tú, no lo encontraría. Lo único que pide
administrador es el instalador de Visual Studio, que lo pide él solo.

**PowerShell 7 no hace falta**: con la que trae Windows basta. Los `.cmd` de la tubería se llaman
igual en las dos.

---

## 1. Lo que hace falta antes

| | Para qué |
|---|---|
| **Wiicompiled** (0.2.31 es con la que se hizo esto) | Compila tu disco a código nativo. Sin él no hay nada que portar |
| **Tu disco de Mario Kart Wii** PAL `RMCP01` | Es el que Wiicompiled acepta |
| **Retro Rewind** (opcional) | Su `Code.pul` es lo único que se compila; las pistas y los menús se leen al arrancar |
| **Visual Studio 2022** con el componente de **UWP para C++** | Su entorno `store` (`vcvarsall x64 store`), y el `makeappx`/`signtool` del Windows SDK |
| **El llvm-mingw de Wiicompiled** | clang y `ld.lld` con el ABI de MSVC |
| **El bundle de UWP**, y **un SDL3 de UWP aparte** | Dawn, `nod`, `libuwp`, libpng, zlib — y el SDL3, que va aparte por lo que dice el §4 |
| **Python 3** | Los scripts |
| **Una Xbox en modo desarrollador** y un certificado | Instalar y firmar |

### Las variables de entorno

Los scripts no llevan ninguna ruta de ninguna máquina dentro: las toman de estas cinco variables,
que se ponen una vez por sesión de terminal.

```powershell
$env:MKW_TOOLKIT  = "C:\mkw\Toolkit\llvm-mingw\bin"   # clang y ld.lld de Wiicompiled
$env:MKW_UWP_DEP  = "C:\mkw\uwp-dep\x64"               # el bundle (tiene include\ y lib\)
$env:MKW_UWP_SDL  = "C:\mkw\uwp-dep-sdl\x64"           # el SDL3 de UWP, aparte
$env:MKW_XBOX     = "C:\mkw\xbox"                       # donde viven package\ y las salidas
$env:MKW_BASE_PC  = "C:\mkw\Install\Base"              # la carpeta Base de Wiicompiled
```

Si falta una, el script se detiene diciendo **cuál** y para qué sirve, en vez de fallar más adelante
con un error que no se entiende.

Hay una sexta, `MKW_BUILDWORKSPACE`, que **normalmente no hay que poner**: la carpeta
`Install\BuildWorkspace` se deduce de las rutas que trae el `compile_commands.json` del paso 2.
Solo se declara si el script dice que no ha podido deducirla.

---

## 2. Compilar el producto para PC primero

De ahí sale lo que necesita el port: el `build.ninja` del perfil que te interese —el juego base,
Retro Rewind, o los dos— y su base de compilación.

```powershell
# en la carpeta de compilación nativa de Wiicompiled
ninja -t compdb > compile_commands.json
```

Esa **base de compilación** es la entrada de todo lo que viene: no hay que reconfigurar nada con
CMake, porque el build de PC ya trae sus reglas.

⚠ **Compílalo y pruébalo en PC antes de seguir.** Si no corre ahí, no va a correr en la consola.

---

## 3. Los parches

**Aurora** (MIT), las dos partes:

```powershell
git apply --directory=C:\mkw\port\aurora-main patches\aurora-uwp.patch
python tools\parche-aurora.py C:\mkw\port\aurora-main
```

El script es idempotente y todo-o-nada: cada cambio comprueba su ancla antes de escribir, y si una
no cuadra te lo dice sin dejar el archivo a medias.

**El runtime de Wiicompiled**: los doce cambios están descritos uno a uno en
[`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md) —qué archivo, qué pasa y qué hay que hacer—. Aquí no van
como parche porque Wiicompiled no publica licencia que lo permita; esa sección es la receta.

Todo el delta queda detrás de `MKW_UWP` (runtime) y `AURORA_WINDOWS_STORE` (Aurora), así que el
mismo árbol **sigue compilando para PC**.

---

## 4. El SDL3 de UWP, que va aparte

El bundle principal trae un `SDL3.dll` **de escritorio**: importa `MSVCP140.dll` sin el sufijo
`_APP`, y un App Container no lo carga. Hace falta un SDL3 compilado para UWP, en su propia carpeta
(`MKW_UWP_SDL`), y el enlazado toma de ahí `SDL3.lib` y de ningún otro sitio.

---

## 5. Un certificado, y tu identidad en el manifiesto

```powershell
$c = New-SelfSignedCertificate -Type Custom -Subject "CN=TuNombre" `
       -KeyUsage DigitalSignature -FriendlyName "Firma UWP" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$c.Thumbprint
```

Y en `package\Package.appxmanifest`, los `CHANGE-ME`: `Identity Name`, `Publisher` (**idéntico** al
sujeto del certificado), `PublisherDisplayName` y el `PhoneProductId` (`[guid]::NewGuid()`).

⚠ **La versión del paquete la pone este manifiesto a mano**, no el empaquetador, y tiene que subir en
cada paquete nuevo: la consola no reemplaza un paquete por otro de la misma versión.

---

## 6. Compilar, enlazar, empaquetar

**Compilar, dos veces.** La segunda no es opcional: trae ImGui, y sin ella el enlazado deja 20
símbolos sin resolver.

```powershell
tools\compilar.cmd C:\mkw\compile_commands.json C:\mkw\obj      --overlay=C:\mkw\port
tools\compilar.cmd C:\mkw\compile_commands.json C:\mkw\obj-deps --overlay=C:\mkw\port --solo=deps
```

**Enlazar**, diciendo qué producto quieres:

```powershell
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\RetroRewind.exe retro
tools\enlazar.cmd C:\mkw\obj C:\mkw\obj-deps C:\mkw\build\WiiCompiled.exe  base
```

⚠ Ese último argumento no es decorativo: la compilación deja los objetos de **los dos productos** en
la misma carpeta, y hay que apartar los del otro. Si no, el juego arranca, pinta el splash y se
cierra sin escribir nada ([`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md)).

**Empaquetar y firmar:**

```powershell
python tools\empaquetar-uwp.py C:\mkw\build\RetroRewind.exe C:\mkw\build\RetroRewind.msix package
```

---

## 7. Instalarlo en la consola

### Antes de tocar nada: cómo tiene que estar la consola

- **En modo desarrollador**, con Dev Home instalado.
- **Encendida y con tu perfil iniciado.** ⚠ Sin un usuario conectado, la consola **no abre
  aplicaciones**: el paquete se instala, aparece en la lista y al lanzarlo no pasa nada.
- **En la misma red que tu PC**, y con su dirección a mano (la dice Dev Home). El Device Portal
  escucha en el puerto **11443** por HTTPS y pide el usuario y la contraseña
  que definiste en Dev Home.

Abre `https://<ip>:11443`. ⚠ El navegador avisará de que el certificado del sitio no es de
confianza: es el de la propia consola. Entra igual —en Edge y Chrome, **Avanzado** → **Continuar
a … (no seguro)**; en Firefox, **Avanzado** → **Aceptar el riesgo y continuar**.

En **My games & apps → Add**: tu `.msix`, y en **Dependency** el
`Microsoft.VCLibs.x64.14.00.appx` del Windows SDK la primera vez (el manifiesto lo declara, y sin
él la activación falla con `0x8027025B`). **Certificate** no hace falta: el modo desarrollador
acepta cualquier paquete firmado.

Si sale `There is not enough space on the disk`, no está llena: la primera instalación de una
familia va a `D:\DevelopmentFiles`, de unos 5 GB. Se arregla instalando primero una *semilla* con la
misma identidad y versión más baja.

---

## 8. El juego y el mod, dentro del paquete

Los datos van al `LocalState` de la aplicación, por el **File explorer** del Device Portal. El
primer arranque crea las carpetas; si subes antes, el portal dice que no encuentra la ruta.

- el contenido del juego que Wiicompiled espera, tal como lo deja en PC;
- y, para Retro Rewind, su carpeta `RetroRewind6\` entera: las pistas, los menús y las traducciones
  se leen **en vivo al arrancar**, así que cambiar el mod no obliga a recompilar nada.

El registro está en `LocalState\WiiCompiled\Logs\uwp-console.txt`. En una consola es lo único que
tienes.

---

## Si algo no sale bien

| Síntoma | Causa |
|---|---|
| El paquete instala y al abrirlo no pasa nada | ¿Hay un **perfil iniciado**? Y mira el registro: el primer arranque sin datos no hace nada visible |
| La activación falla con `0x8027025B` | Falta la dependencia de VCLibs, **o** el `.exe` se enlazó sin `/subsystem:windows,10.0` |
| Arranca, splash, y se cierra sin registro | Los dos `indirect_dispatch` en el mismo enlazado (§6) |
| 20 símbolos de ImGui sin resolver | Falta la segunda pasada de compilación (§6) |
| «no carga SDL3» o un error de `MSVCP140.dll` | El `SDL3.dll` es el de escritorio (§4) |
| `vcvarsall fallo`, o `'m' is not recognized` | Un `.cmd` guardado con saltos de línea de Unix. Tienen que ir en CRLF; el `.gitattributes` de este repositorio lo fija |
| Falta una variable de entorno | El script dice cuál y para qué es (§1) |

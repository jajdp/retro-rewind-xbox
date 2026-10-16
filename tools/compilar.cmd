@echo off
rem ============================================================================================
rem Fase 1 de dos: compila los objetos del port, entrando antes al entorno «store» de Visual
rem Studio. Sin ese entorno, INCLUDE y LIB apuntan al escritorio y nada de esto sirve.
rem
rem Uso:  tools\compilar.cmd <compile_commands.json> <carpeta de salida> [--jobs N] [--solo=deps]
rem
rem HAY QUE LLAMARLO DOS VECES, y la segunda no es opcional:
rem   tools\compilar.cmd <compdb> C:\mkw\obj       --overlay=C:\mkw\port
rem   tools\compilar.cmd <compdb> C:\mkw\obj-deps  --overlay=C:\mkw\port --solo=deps
rem La segunda aporta ImGui; sin ella el enlazado deja 20 simbolos de ImGui sin resolver.
rem
rem Antes: las variables de entorno de docs/INSTALL.es.md §2 (MKW_TOOLKIT, MKW_UWP_DEP,
rem MKW_UWP_SDL). Este archivo tiene que estar en CRLF: con saltos de linea de Unix, cmd parte
rem mal las lineas y vcvarsall falla con mensajes que despistan («'m' is not recognized»).
rem
rem Recompilaciones - https://github.com/jajdp/retro-rewind-xbox
rem ============================================================================================
setlocal

rem El vcvarsall de la instalacion mas nueva, buscado y no fijado: una ruta a mano es la forma mas
rem rapida de que esto deje de funcionar en la maquina de al lado.
set VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe
if not exist "%VSWHERE%" (echo no encuentro vswhere.exe: hace falta Visual Studio ^(docs/INSTALL.es.md §1^) & exit /b 1)
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -property installationPath`) do set VSDIR=%%i
if not defined VSDIR (echo vswhere no encontro ninguna instalacion de Visual Studio & exit /b 1)
call "%VSDIR%\VC\Auxiliary\Build\vcvarsall.bat" x64 store >nul
if errorlevel 1 (echo vcvarsall x64 store fallo: ¿esta instalado el componente de UWP para C++? & exit /b 1)

echo INCLUDE=%INCLUDE%
echo LIB=%LIB%
py -3 -X utf8 "%~dp0compile-check.py" %*

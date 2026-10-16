@echo off
rem ============================================================================================
rem Fase 2 de dos: enlaza los objetos en un .exe de UWP/Xbox.
rem
rem Uso:  tools\enlazar.cmd <obj> <obj-deps> <salida.exe> [retro^|base]
rem
rem El ultimo argumento dice QUE PRODUCTO se enlaza, y no es un detalle: la compilacion deja en
rem la MISMA carpeta los objetos de los dos productos de Wiicompiled --el juego base y Retro
rem Rewind--, porque comparten runtime, Aurora, las librerias y los shards comunes. Lo exclusivo
rem de cada uno se aparta aqui:
rem
rem   retro : aparta los del juego base   (shards_base_portable_sensitive_, shards_base_registration_,
rem                                        shards_base_dispatch_, _product_base_product.cpp)
rem   base  : aparta los de Retro Rewind  (shards_retro_mod_, shards_retro_portable_sensitive_,
rem                                        shards_retro_rewind_registration_)
rem
rem ⚠ OJO CON indirect_dispatch: hay uno por producto y su nombre lleva un hash, asi que no salta
rem a la vista. Dejar los dos NO da error de enlazado --los simbolos no chocan-- pero el juego
rem arranca, pinta el splash de UWP y se cierra sin escribir ni un registro. Eso costo la primera
rem tanda entera.
rem
rem Este archivo tiene que estar en CRLF (ver tools\compilar.cmd).
rem
rem Recompilaciones - https://github.com/jajdp/retro-rewind-xbox
rem ============================================================================================
setlocal

if "%~3"=="" (
  echo uso: tools\enlazar.cmd ^<obj^> ^<obj-deps^> ^<salida.exe^> [retro^|base]
  exit /b 2
)
set PRODUCTO=%~4
if "%PRODUCTO%"=="" set PRODUCTO=retro
if /i "%PRODUCTO%"=="retro" (
  set APARTAR=shards_base_portable_sensitive_,shards_base_registration_,shards_base_dispatch_,_product_base_product.cpp
) else if /i "%PRODUCTO%"=="base" (
  set APARTAR=shards_retro_mod_,shards_retro_portable_sensitive_,shards_retro_rewind_registration_
) else (
  echo el cuarto argumento tiene que ser «retro» o «base» ^(es: %PRODUCTO%^)
  exit /b 2
)
echo producto: %PRODUCTO%

set VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe
if not exist "%VSWHERE%" (echo no encuentro vswhere.exe: hace falta Visual Studio & exit /b 1)
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -property installationPath`) do set VSDIR=%%i
call "%VSDIR%\VC\Auxiliary\Build\vcvarsall.bat" x64 store >nul
if errorlevel 1 (echo vcvarsall x64 store fallo & exit /b 1)

py -3 -X utf8 "%~dp0enlazar-uwp.py" "%~1" "%~2" "%~3" --excluir=%APARTAR%

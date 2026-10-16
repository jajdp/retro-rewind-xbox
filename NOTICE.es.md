# Aviso

*(English: [NOTICE.md](NOTICE.md))*

## Sin afiliación

Esto es un proyecto de aficionado, no oficial y sin ánimo de lucro. **No está afiliado a Nintendo ni
a Microsoft**, ni cuenta con su respaldo o aprobación, ni lo está con el equipo de Retro Rewind, ni
con el autor de Wiicompiled, ni con el de [Aurora](https://github.com/encounter/aurora). *Mario Kart
Wii*, *Xbox* y todos los nombres y marcas relacionados son de sus respectivos propietarios, y aquí
se usan solo para decir con qué funciona esto.

Aquí no se vende nada, y nada de esto está monetizado.

## Qué no distribuye este repositorio

Ni imagen del disco. Ni datos del juego o del mod: ni `Code.pul`, ni pistas, ni menús, ni `.szs`. Ni
ejecutable compilado. Ni `.msix`. Ni partidas. Ni mosaicos del paquete (`package/Assets/` está
vacía, y [`docs/ASSETS.es.md`](docs/ASSETS.es.md) te pide los tuyos).

**Ni ninguna de las bibliotecas de UWP**: Dawn, SDL3, `nod`, `libuwp`, libpng y zlib son binarios de
otros. La guía dice de dónde salen.

## Qué contiene de trabajo de otros

**Parches contra Aurora.** `patches/aurora-uwp.patch` (22 archivos) y `tools/parche-aurora.py`
(7 cambios) modifican [Aurora](https://github.com/encounter/aurora), que es **MIT**,
© 2022 Luke Street. La MIT permite versiones modificadas; este repositorio se publica bajo
[esa misma licencia](LICENSE), y el aviso de copyright de Aurora viaja con él.

**Nada de Wiicompiled.** Wiicompiled no publica ninguna licencia propia —la carpeta `licenses/` que
instala solo tiene las del código de terceros que incluye (Aurora, CppWinRT, nodtool, el runtime de
VC, las herramientas portables de compilación)—. Sin una licencia que lo permita, **aquí no se
reproduce nada de su código**: ni como diff, ni como anclas de parche, ni como líneas citadas. Los
doce cambios que su runtime necesita para funcionar dentro de un App Container están *descritos* en
`docs/HOW-IT-WORKS.es.md` —qué archivo, cuál es el problema y qué hace el cambio—. Eso es una
descripción técnica, del mismo tipo que cualquier informe sobre el software de otro, y no lleva
código suyo.

Las herramientas de `tools/` son propias: trabajan con nombres de objetos, de bibliotecas y opciones
del enlazador, y no citan código de nadie.

**Aquí no hay capturas de pantalla.** Una captura de esto funcionando sería casi toda arte de
Nintendo.

## Retirada y contacto

Si tienes derechos sobre este material y quieres que algo de aquí se quite o se cambie, escribe a
**jajdpmail@gmail.com** diciendo a qué te opones y en calidad de qué escribes.

Las peticiones de quien tiene los derechos se atienden: se quita la parte en disputa, o se retira el
repositorio, sin discutir, y recibirás una respuesta confirmándolo. No hace falta ningún aviso ni
proceso legal más allá de ese correo.

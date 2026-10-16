# The package tiles

*(Español: [ASSETS.es.md](ASSETS.es.md))*

The manifest names four images, and **this repository ships none of them**: the ones in the real
package were made from the game's own artwork. You supply your own.

| File | Size |
|---|---|
| `StoreLogo.png` | 50 × 50 |
| `Square150x150Logo.png` | 150 × 150 |
| `Square44x44Logo.png` | 44 × 44 |
| `SplashScreen.png` | 620 × 300 |

PNG, 32-bit with alpha. `tools/generar-assets.py` can produce them from a source image, and
`tools/empaquetar-uwp.py` stops if any is missing.

> **Where to type this:** in **PowerShell**, in an **ordinary** window (no administrator), from
> this repository's folder.

```powershell
$tiles = @{ 'StoreLogo.png' = '50x50'; 'Square150x150Logo.png' = '150x150'
            'Square44x44Logo.png' = '44x44'; 'SplashScreen.png' = '620x300' }
foreach ($t in $tiles.GetEnumerator()) {
  magick -size $t.Value xc:"#1b1b1f" (Join-Path 'package\Assets' $t.Key)
}
```

Keep whatever art you make yours: screenshots, logos and character art from the game belong to
their owners, and a package that carries them is a package you cannot share.

# Paystreak Data logo, three versions

Open `preview.html` to see every file on light and dark backgrounds, and at 16, 24 and 32px.

| Version | Mark | Wordmark |
|---|---|---|
| `v1-strata` | Four horizontal rock beds cut by one gold seam at a low angle | Libre Caslon Text (serif, the site's current heading face) |
| `v2-fault` | The beds step down across the seam, the way a real vein offsets rock | Inter Tight SemiBold (grotesque) |
| `v3-core` | A round core sample, which also reads as a seal | Source Serif 4, PAYSTREAK over DATA in spaced capitals |

Each folder has:

- `lockup-light` / `lockup-dark`: mark plus wordmark, for light or dark backgrounds
- `mark-light` / `mark-dark`: the mark alone
- `lockup-mono-black` / `lockup-mono-white`, `mark-mono-black` / `mark-mono-white`: one-colour versions
- `favicon`: the mark on a charcoal tile, so it reads on light and dark browser tabs

Each folder also has a `png/` subfolder with the same files as transparent PNGs: lockups at 8x their SVG size (about 3,000px wide), marks at 1024px square, favicons at 512px.

The wordmarks are converted to outlines, so the SVGs don't need any fonts installed. The files have transparent backgrounds.

Colours: charcoal `#1B1915`, gold `#C9A227`, off-white `#F6F3EC`.

Gold is used only for the seam, never for text: on off-white it is too low-contrast to read as type.

`build.py` regenerates every file. Its docstring lists the fonts it needs.

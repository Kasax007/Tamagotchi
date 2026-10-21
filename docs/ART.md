# Art style guide

Goal: **sweet, readable, vanilla-compatible pixel art**. Everything should look like it could be a
Minecraft update, only a bit cuter. Young audience: friendly faces, soft colours, clear silhouettes.

## Density and sizes

* 16 texels per block, never mixed densities. Block textures 16×16 (per face), item sprites 16×16,
  particle sprites 8×8 (emote bubbles 16×16 shown at small size), entity textures 64×64 (128×64 if needed).
* Models are built from boxes on a 1-px grid (no half pixels except for flat planes).

## Colour

* Every material gets a **ramp of 4–5 shades** (highlight, light, base, shadow, deep shadow). Hue-shift
  the ramp: shadows a little cooler/more saturated, highlights a little warmer. Never shade with pure black
  or lighten with pure white.
* Light comes from the **top-left**. Top faces lightest, front faces base, sides and bottoms darker.
* Low-contrast texture noise (1 shade apart) on large areas so faces never look flat; no random
  full-contrast speckle.
* Outlines: no black outlines on entity/block textures (vanilla doesn't use them). Item sprites get a
  **dark hue-tinted outline** (like vanilla items), never pure black.
* Accent colours sparingly: one accent per object (gem, flower, scarf, glowing spots).

## Faces (pets)

* Big eyes (2×2 or 2×3) with a 1-px white catch-light in the upper corner; pupils dark but tinted.
* Optional blush (1–2 px pink) under the eyes; small mouths (1–2 px) or none.
* Expressions are full texture variants: `normal`, `blink`, `happy` (^ ^), `sleep`, `sad`, `angry`, `love` (heart eyes).
* Emissive bits (lava cracks, sculk spots, glowing eyes) live in a separate `_glow` texture.

## Files

* `assets/tamagotchi/textures/entity/<pet>/<pet>.png` (+ `_<expression>.png`, `_glow*.png`)
* `assets/tamagotchi/textures/block/*.png`, `textures/item/*.png`, `textures/particle/*.png`, `textures/gui/*.png`
* Sources (generators, pixel maps) live in `tools/` so every asset can be regenerated and tweaked.

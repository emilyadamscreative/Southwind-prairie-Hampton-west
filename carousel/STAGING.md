# Staging the Hampton West photos

ChatGPT can't be reached from the cloud session that built this carousel, so staging is a drop-in step.
Everything else (polish, layout, caption, disclaimer) is automated.

## Which photos to stage

| Photo | Slide(s) | Stage? | Why |
|---|---|---|---|
| `edited/IMG_0611.jpg` (living room and fireplace) | 3 and 10 | Recommended | The largest empty room, and it sells the open plan. |
| `edited/IMG_0637.jpg` (bedroom) | 6 | Recommended | An empty bedroom reads smaller than it is. |
| `edited/IMG_0616.jpg` (kitchen, cover) | 1 | Optional, decor only | Already finished. Add counter decor only: no stools unless the island has a seating overhang. |
| All others | | No | Baths, closet, laundry, and door read fine empty, and every staged photo adds the disclaimer. |

Start from the `edited/` versions, not the raw `.jpeg` files.

## Steps

1. Open ChatGPT, upload the photo, and paste the prompt below (or Emily's usual prompt, once it is saved here).
2. Download the result and save it into `carousel/staged/` with the **same base name**, for example `staged/IMG_0611.png`. PNG, JPG, or WEBP all work.
3. Re-render:
   ```
   cd carousel
   python3 -I render.py
   ```
   Slides that use a staged photo get the disclaimer printed on them automatically, and `CAPTION.md` gets the disclaimer line.
   To undo a staging, delete the file from `staged/` and re-render.

Before posting, check each staged photo against the original: same windows, same fireplace, same cabinets, and same flooring.
If ChatGPT changed the architecture, regenerate it. The disclaimer says the photo is real, so the room itself has to be.

## Emily's usual prompt

> _Not saved yet. Paste it here once and it never has to be dug out of ChatGPT history again._

## Fallback prompt (used until the usual one is saved)

```
Virtually stage this real photo of an empty apartment for a rental listing.
Add furniture and decor only. Keep every architectural element exactly as it is:
walls, ceiling, windows, doors, trim, flooring, fireplace, cabinets, countertops,
appliances, light fixtures, ceiling fans, outlets, and vents. Do not change the
camera angle, perspective, crop, paint colors, or the view through the windows.
Style: warm modern transitional, uncluttered, neutral palette of cream, oatmeal,
and warm wood with a few soft slate blue accents. Scale every piece realistically
for the room. Match the existing light sources with realistic shadows.
Photorealistic, same aspect ratio as the original.

Room: <paste one line from below>
```

Room lines:

- **IMG_0611, living room:** A sofa facing the fireplace, two accent chairs, a round wood coffee table, a large neutral area rug, a floor lamp, and a dining table for four in the open space toward the kitchen. Keep the walkway to the kitchen clear.
- **IMG_0637, bedroom:** A queen bed with neutral linens against the left wall, two nightstands with lamps, a bench at the foot of the bed, a neutral rug, and one piece of simple framed art. Keep the window and blinds unchanged.
- **IMG_0616, kitchen (decor only):** A bowl of lemons on the island, a small vase of greenery, and a wood cutting board near the range. Do not add stools or change any cabinet, counter, backsplash, appliance, or light fixture.

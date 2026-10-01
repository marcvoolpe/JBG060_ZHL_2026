# Labelling guide

The full rules are in `METHODOLOGY.md` section 4. This page is the short version for labellers.

## Start

1. `git pull`. Once: unzip `cropland_images.zip` (from Matteo) inside `cropland/label_tool/`, so the images end up in `cropland/label_tool/img/`. Then from `group_repo` run **`python cropland/label_server.py`** and open **http://localhost:8765**. (Python only, no extra packages.)
2. Choose the set (`pilot` first, then `sample`) and your name. The header says "auto-saving to disk".
3. **Never open a cropland map** (WorldCover, GLAD, ASAP...) while labelling, and don't look at anyone else's labels.
4. Every saved point is written straight to `cropland/labels/<set>_labels_<name>.csv`. Close the browser any time; it picks up where you left off. At the end of a session, commit **only your own file**:
   `git add cropland/labels/*_<name>.csv && git commit -m "labels: <name>" && git pull --rebase && git push`

Without the server (double-clicking `index.html`) the tool still works, but labels stay in the browser until you press **Export CSV**.

## Where the point is matters

The box under the coordinates says which area the point is in and what farming looks like there. **Aweil** is rain-fed sorghum near homesteads, harvested Sep–Oct. **Bor South** is the Nile floodplain: crops on higher ground, plus **flood-recession plots** that are planted when the water drops (Nov–Feb). A field that is under water in Aug–Oct and green in Dec–Feb can be crop there.

## Per point (about 1 minute)

You label the **10 m pixel in the yellow square, for 2025**. 2024 is shown only to recognise fallow.

1. **What covers most of the pixel?** `W` water · `B` buildings/road · `T` trees/shrub · `O` open land.
   Water, buildings and trees end the point: the label fills in as "not crop". Press `Enter`.
2. **Open land:** answer the cues with `Y` yes, `N` no, `K` can't tell. The highlighted question is the next one.
   - a. bare, tilled soil in Apr–May
   - b. green-up Jun–Aug
   - c. browns or is cleared Aug–Nov earlier than the grass around
   - d. field shape (edges, rectangles, patchwork)
   - e. cropped in 2024 (only asked if a–d don't already say crop)
3. The **label fills in by itself**. If you disagree, press `C` crop, `F` fallow, `X` not crop or `U` unsure, and write why in the notes. `1` `2` `3` set confidence.
4. `Enter` saves and moves on. `←` `→` move between points, `V` switches true/false colour, `R` resets the point.

## The labels

| label | means |
|---|---|
| crop | sown and grown in 2025 (sorghum, groundnut, sesame, maize, rice, home gardens) |
| fallow | a field (edges, or cropped in 2024) that looks like grass all of 2025 |
| not crop | grass, bush, trees, water, settlement |
| unsure | images missing or unreadable; say why |

Crop season in Northern Bahr el Ghazal (FEWS NET): sowing done by late May; groundnuts and sesame harvested from August; short-cycle sorghum in September–October.

## Traps

- **Burned grass** looks like bare soil. Burns are dark and irregular, in the dry season (Nov–Feb); tilled fields are lighter and have edges.
- **Wild grass** greens up with the crops. The difference is the early brown-down at harvest, and the shapes.
- **The high-resolution image has an unknown date.** Check it in Wayback before trusting a field shape.

When unsure, say `unsure`. That is useful information, not a failure.

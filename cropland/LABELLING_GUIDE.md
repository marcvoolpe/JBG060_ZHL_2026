# Labelling guide

The full rules are in `METHODOLOGY.md` section 4. This page is the short version for labellers.

## Start

1. `git pull`. Once: unzip `cropland_images.zip` (from Matteo) inside `cropland/label_tool/`, so the images end up in `cropland/label_tool/img/`. Then from `group_repo` run **`python cropland/label_server.py`** and open **http://localhost:8765**. (Python only, no extra packages.)
2. Choose the set **`sample`** and your name (the `pilot` set holds the old 10 m pilot: don't label there). The header says "auto-saving to disk". You see only your 180 points. One other person labels each of them too, and you never see each other's labels, so don't discuss points before both of you are done. When you two disagree, nobody overrules anyone: both labels are kept and reported. So label what **you** see, and use `unsure` honestly.
3. **Never open a cropland map** (WorldCover, GLAD, ASAP...) while labelling, and don't look at anyone else's labels.
4. Every saved point is written straight to `cropland/labels/<set>_labels_<name>.csv`. Close the browser any time; it picks up where you left off. At the end of a session, commit **only your own file**:
   `git add cropland/labels/*_<name>.csv && git commit -m "labels: <name>" && git pull --rebase && git push`

Without the server (double-clicking `index.html`) the tool still works, but labels stay in the browser until you press **Export CSV**.

## Where the point is matters

The box under the coordinates says which area the point is in and what farming looks like there. **Aweil** is rain-fed sorghum near homesteads, harvested Sep–Oct. **Bor South** is the Nile floodplain: crops on higher ground, plus **flood-recession plots** that are planted when the water drops (Nov–Feb). A field that is under water in Aug–Oct and green in Dec–Feb can be crop there.

## Per point (about 1 minute)

You label the **210 m × 210 m yellow box, for 2025**. The box is **crop if there is cropland anywhere in it**, even one small field or home garden. 2024 is shown only to recognise fallow.

What you see: the greenness chart splits the box into up to 3 patches whose curves differ, with a small map of where each is. A field in a box of grass gets its own line: bare in Apr–May, dropping before the others in Sep–Oct. A patch is only "different", not "crop": trees (green all year) and bare ground also make patches. The radar curve sees through clouds (rises as a crop grows, drops at harvest, very low = water). The high-resolution image shows its capture date: **green** if it shows the 2025 season (taken in 2025, or Jan–Mar 2026 just after the harvest), **orange** if it is from another year (use it for field shapes only). **Click a month** to see it large, 2025 next to 2024.

1. **Is there open land (field or grass) anywhere in the box?** `O` yes. If not, what is the box mostly: `W` water · `B` buildings/road · `T` trees/shrub.
   Water, buildings and trees end the point: the label fills in as "not crop". Press `Enter`.
2. **Open land:** answer the cues for the **most field-like patch in the box** with `Y` yes, `N` no, `K` can't tell. The highlighted question is the next one.
   - a. bare, tilled soil in Apr–May
   - b. green-up Jun–Aug
   - c. browns or is cleared Aug–Nov earlier than the grass around
   - d. field shape (edges, rectangles, patchwork)
   - e. cropped in 2024 (only asked if a–d don't already say crop)
3. The **label fills in by itself**. If you disagree, press `C` crop, `F` fallow, `X` not crop or `U` unsure, and write why in the notes. `1` `2` `3` set confidence.
   For crop or fallow, say **about how much of the box is cropland** (crop and fallow fields together): `6` under 10% · `7` 10–25% · `8` 25–50% · `9` over 50%. A rough guess is fine; the patch shares in the greenness chart help. "Not crop" sets it to `0` by itself. This answer is what makes the area estimate right.
4. `Enter` saves and moves on. `L` marks a hard point to come back to later (orange in the list). `←` `→` move between points, `V` switches true/false colour, `R` resets the point.

## The labels

| label | means |
|---|---|
| crop | at least one field in the box sown and grown in 2025 (sorghum, groundnut, sesame, maize, rice, home gardens) |
| fallow | the box has a field (edges, or cropped in 2024) but none was cropped in 2025 |
| not crop | no field anywhere in the box: grass, bush, trees, water, settlement |
| unsure | images missing or unreadable; say why |

Crop season in Northern Bahr el Ghazal (FEWS NET): sowing done by late May; groundnuts and sesame harvested from August; short-cycle sorghum in September–October.

## Traps

- **Burned grass** looks like bare soil. Burns are dark and irregular, in the dry season (Nov–Feb); tilled fields are lighter and have edges.
- **Wild grass** greens up with the crops. The difference is the early brown-down at harvest, and the shapes.
- **The high-resolution image has an unknown date.** Check it in Wayback before trusting a field shape.
- **Small fields count.** One small cropped plot in a box of grass makes the box **crop**. Look at the edges of the box too, not only the centre. A cropped field and a fallow one in the same box: **crop**.

When unsure, say `unsure`. That is useful information, not a failure.

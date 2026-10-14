# 8. Poster plan (poster session, 21 Oct 2026)

Rewritten 14 Oct 2026 against the official requirements (Canvas, pasted by Yassin) and the results we have now. Numbers trace to `cropland/results/` and `notes/07` section 7.0.

## 8.1 What is asked (keep this in view)

**Audience: the stakeholders**, the experts of ZOA and ZHL. They want **insights that help them improve their approach** to the case, not every implementation detail. The poster is a **high-level visual overview of context, motivation and outcomes**.

| requirement | what it means for us |
|---|---|
| one PDF, **A0 portrait** (841 x 1189 mm) | build at final size from the start (PowerPoint/Keynote custom size 84.1 x 118.9 cm, or LaTeX `tikzposter`/`baposter` a0paper portrait) |
| **minimum font size 20 pt** | this includes **text inside figures** (axis labels, legends). Our report figures use 9 pt at about 25 cm wide: printed 40 cm wide that is about 14 pt, too small. **Re-export every poster figure at its printed size with 20-24 pt text** (section 8.5) |
| readable, professional, sufficient contrast | dark text on a light background; our palette (blue `#2a78d6`, orange `#eb6834`, grays) passes contrast on white; no text on photos or coloured fills |
| empty space, clear large headings | 3 columns with wide gutters; headings 60-80 pt, title 100-140 pt, body 26-32 pt |
| as little text as needed | **aim for 300-400 words in total**; short sentences, bullets, numbers |

**Rubric (20% of the grade):**

| criterion | points | where the poster earns it |
|---|---|---|
| motivation and research objective stated clearly | contents 10 (shared) | panel A (problem) and B (objective, one sentence) |
| overview of the approach at the stakeholder's level | | panel C: one diagram, no formulas |
| concise but complete conclusions and insights | | panels D-G (results) and H (what ZOA can do) |
| well-designed figures at good sizes | design 6 (shared) | 5 figures, each at least a quarter of a column wide |
| clear structure: headings, colour, empty space | | letters A-I as reading order, one background colour for "what ZOA can do" |
| colour supports content | | one blue for public maps, one orange for our results, everywhere |
| text limited to what is needed | | 300-400 words |
| clear oral presentation; everyone can answer questions | presentation 4 | 90-second pitch (8.3), question list (8.4); **every group member rehearses both** |

## 8.2 Layout: A0 portrait, three columns, read top to bottom

**Title (full width):** *Which cropland is under water? Checking the maps behind ZOA's flood trigger in Aweil and Bor South*
**One-line message under the title:** *Public cropland maps miss most fields in Aweil, so a "flood inundates cropland" trigger built on them stays silent in big floods. A small labelled sample fixes the number and tells which map to trust.*
Group 1 (names), TU/e JBG060, with ZOA and Zero Hunger Lab `[logos only with permission]`.

| | left column | middle column | right column |
|---|---|---|---|
| **row 1: why** | **A. The problem.** Small diagram: trigger = flood forecast x cropland map. ZOA's trigger idea: "a flood which inundates cropland" (Q&A 2). Seven free maps exist; ZOA cannot tell which is right. | **B. Our objective** (one sentence): measure the cropland in ZOA's two areas with an error bar that does not depend on any map, score every map against it, and show what that changes for a flood trigger. | **C. What we did** (diagram, no formulas): maps disagree -> 450 random points in strata -> 2 people label each one blind from satellite images (85.6% agree) -> area with 95% interval, score of every map, a 2-question map of our own -> laid over 26 years of floods. |
| **row 2: what we found** | **D. The maps under-count cropland.** Figure: our estimate with interval vs every map (new figure 14). "Aweil: 3.8% of the land is cropland (2.5-5.9%); every public map shows 0.2-1.9%." | **E. Which map to trust?** Scorecard (new figure 15): F1 per map with intervals; line at 0.84 = how well two people agree. "Esri and Dynamic World find 2-3% of the fields; WorldCereal 41%; our 2-question map 75%." | **F. Same flood, different answer.** Figure 13 (before/after map, Aweil 2022): "WorldCereal shows crop in 1,646 flooded cells; our map adds 3,627." |
| **row 3: what it means** | **G. Missed triggers.** Figure 12 (26 years): "In big floods the sample puts 4-16 times more cropland under water than the median map. A 500 ha trigger would have stayed silent in 2022 with Esri, GLAD or WorldCover." | **H. What ZOA can do** (coloured box, the take-away): 1. never pick a map by overall accuracy; in Aweil use WorldCereal or our map, avoid Esri and Dynamic World; in Bor South avoid Dynamic World. 2. base the trigger's cropland on a labelled sample with its interval, with extra points on flood-prone land. 3. repeat a check each season: about 150 points, a few hours per person. 4. our kit runs for other areas and years. | **I. Limits and next steps.** Labels from images, no field visit; one season (2025); Bor South has almost no cropland in the sample; flooded-cropland intervals are wide. Next: ZOA field points, a flood-prone stratum, crop stage and flood duration. QR code -> repository and interactive map. |

**Figures on the poster (5):** 14 (area vs maps), 15 (scorecard), 13 (before/after flood map), 12 (26-year flood history), method diagram (to draw). Optional if space: figure 1 (seven maps, seven answers) in panel A. Everything else stays in the report.

## 8.3 90-second pitch (everyone learns it)

1. "ZOA wants to act **before** floods destroy harvests. Their trigger idea: a flood that inundates cropland. That needs a map of cropland." (A)
2. "There are seven free maps. In Aweil they say 0.2 to 1.9% of the land is cropland, and they hardly overlap. Which one is right?" (A, D)
3. "We did not trust any of them. We drew 450 random points, two of us labelled each one blind from satellite images, and from that we measured the cropland with an error bar: 3.8%, two to seventeen times more than the maps show." (C, D)
4. "We scored every map on those points. Esri and Dynamic World find only 2-3% of the fields; our own two-question map, 'a building nearby and field edges', finds three quarters." (E)
5. "Then we laid 26 years of floods over today's cropland. In big floods the maps show four to sixteen times less cropland under water, and a 500-hectare trigger would have stayed silent in 2022." (F, G)
6. "So for ZOA: check the map before you trust it, use the sample's number with its interval, and repeat a small check each season. It takes a few hours per person." (H)

## 8.4 Questions to expect (with short answers and numbers)

| question | answer |
|---|---|
| "How do you know your labels are right?" | Two people labelled every point blind; they agreed on 85.6% (kappa 0.70). Disagreements are kept, not settled, and count half. No field visit: our main limit; ZOA field points would be the best check. |
| "Why should we believe your map more than Google's or ESA's?" | We do not ask you to: the **sample** gives the area, whatever the maps say. Our map (F1 0.72) and WorldCereal (0.55) cannot be ranked against each other with 95% confidence; both clearly beat Esri (0.06) and Dynamic World (0.03) in Aweil. |
| "Why is Esri at 97% accuracy in other studies but useless here?" | Accuracy counts the empty land too. When 96% of the land is not cropland, a map that says "no crop" everywhere is 96% accurate. Precision and recall show it misses the fields (Kerner et al. found the same in Mali: 0.97 accuracy, F1 = 0). |
| "What about Bor South?" | Almost no cropland in the sample (0.4% of the land; no agreed crop point among the test points), so no recall there. But Dynamic World calls crop on 44 of 74 boxes where the labellers saw none: open grassland called crop. |
| "Can ZOA run this itself?" | The labelling, yes: a laptop and a browser, a few hours per person for about 150 points (our labellers needed 2.7-7.3 hours for 180). The image and map steps need Google Earth Engine, so a partner like ZHL. The kit has a config file for new areas. |
| "Does this forecast floods?" | No. It fixes the cropland side of the trigger; a flood forecast multiplies with it. |
| "Your flooded-cropland intervals are wide. Why?" | Random points over the whole area rarely land on the 0.3-2% of the land that floods (1 point in 2025, 11 in 2022). Next time: extra points on flood-prone land. |
| "Is this fair to farmers the maps miss?" | That is the point: recall is the share of real fields, and so of farmers, a map can see. Missed fields are missed households (SLE essay). |
| "Logistic regression or trees?" | Both, chosen on the calibration points only: they score the same within the error bars. We keep the 2-question tree because ZOA staff can read and check it. |

## 8.5 Making the figures poster-ready

- Each poster figure is re-exported **at its printed size** (A0 column about 25-26 cm wide; a full-width figure about 78 cm) with **text 20-24 pt**: in `eda_figures.py`, set `figsize` in inches to the printed size (cm / 2.54) and `plt.rcParams["font.size"] = 22` before drawing; save as PDF or SVG (vector, sharp at any size) instead of PNG.
- Keep the colours: public maps blue, our results orange, flooded land without crop gray, text in dark gray. No red/green pairs.
- Direct labels instead of legends where possible (fewer things to read).
- Check by printing one A4 page at 25% scale: if the A4 text is readable at arm's length, the A0 is fine.

## 8.6 Before submitting (checklist)

- [ ] PDF, A0 portrait, fonts embedded; all text 20 pt or larger, figures included
- [ ] title, message, objective, approach, results, what ZOA can do, limits: all present (rubric "contents")
- [ ] 300-400 words; no paragraph longer than 3 lines
- [ ] every number matches `notes/07` 7.0 (Results) and the CSVs
- [ ] logos only with permission; image credits (Esri imagery, OpenStreetMap) in small print
- [ ] QR code tested (repository branch or interactive map)
- [ ] everyone has rehearsed the pitch and the questions

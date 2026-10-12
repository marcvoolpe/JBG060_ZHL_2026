# 8. Poster outline (poster session, 21 Oct 2026)

11 Oct 2026. Format, size and grading criteria are on Canvas (not on this machine): check them and adjust. ZOA and ZHL attend the poster session (kick-off slides), so the poster speaks to them first: one message, three numbers, one recommendation. The report and the poster have different jobs (the report justifies, the poster convinces in 30 seconds), so reuse figures but rewrite the text.

**One-line message (top of the poster):** *Whether a "flood inundating cropland" trigger fires in ZOA's areas depends more on which public cropland map you pick than on the flood. We measured the cropland, with an error bar, and scored the maps.*

## Layout (portrait, three columns; adapt to the Canvas format)

| row | left column | middle column | right column |
|---|---|---|---|
| top | **Title** + one-line message + group, ZHL and ZOA logos `[check permission to use logos]` | | |
| 1 | **The problem.** Trigger = flood map x cropland map (small diagram). ZOA quote: the data "might not capture agricultural land" (Q&A 2). | **Seven maps, seven answers.** Figure 4 (county maps, South Sudan) or figure 1 (crop share per map). Caption: "0.2% to 1.9% of the Aweil counties; all seven agree on half a hectare." | **The map decides the trigger.** Figure 7, Aweil 2022 panel only: "432 or 5,805 ha flooded cropland, same flood. A 1,000 ha trigger fires under 4 of 8 maps." |
| 2 | **What we did.** Method diagram: agreement strata -> 450 random points -> two blind labels each -> (area with interval; scores of every map; our readable map). One line on why: "maps disagree too much to trust or average them". | **How much cropland?** `[area result]`: bar or dot of our estimate with interval next to each map and CFSAM. | **Which map to trust?** `[scorecard]`: recall (and precision) per map with intervals, Aweil and Bor South. Rule 1 printed as 3-4 if-then lines. |
| 3 | **Where maps fail.** `[error analysis]`: two image strips with a one-line label each (e.g. "wetland grass called crop", "field next to a homestead missed"). | **What ZOA can do.** Three recommendations (file 07, 7.3), each with its evidence in four words. | **Limits + next steps.** Labels from imagery, one season, two areas; next: crop stage and flood duration. QR code to the repo or dashboard `[link]`. |

Colour and figures: reuse `deliverables/cropland_report/figures/` at full resolution (PNG at 200 dpi; export again at 300 dpi for print if needed: `fig.savefig(..., dpi=300)` in `eda_figures._save`). Keep the same colours as the report (one blue for maps; orange only for a second series).

## 90-second pitch (for the poster session)

1. "ZOA wants to act before floods destroy harvests. Their example trigger: a flood that inundates cropland." (show row 1 left)
2. "That needs a cropland map. There are seven public ones, and in Aweil they disagree by a factor nine and hardly overlap." (row 1 middle)
3. "So for the same 2022 flood, flooded cropland is 432 or 5,805 hectares depending on the map, and a trigger fires or not." (row 1 right)
4. "We did not trust any map. We drew 450 random points, two of us labelled each blind from satellite images, and from that we estimate the cropland with an error bar and score every map." (row 2)
5. "Result: `[area]`, and `[map]` finds the most of it. Our own readable rules `[do / do not]` beat the public maps." (row 2)
6. "For ZOA: use `[map]` in `[area]`, base a trigger on our estimate with its interval, and repeat a small check each season; it takes about a day." (row 3)

## Questions to expect (with short answers)

| question | answer |
|---|---|
| "Why not just train a better map?" | We did (Rule 1), but a map is only as good as its check; the sample gives the area even if every map is wrong. |
| "How do you know your labels are right?" | Two people, blind, agreed on [x]% (kappa [k]); every disagreement is kept and counted half. No field visits: that is our main limit. |
| "Why 2025, why these two areas?" | ZOA works there; 2025 is the latest full season; the code reruns for any year and area. |
| "Can ZOA run this itself?" | Labelling, yes (about a day per check, laptop and browser). The image and map steps need Earth Engine, so a partner like ZHL. |
| "Does this predict floods?" | No: it fixes the cropland side of the trigger. A flood forecast multiplies with it; our earlier work on upstream lakes is the other side. |
| "What would make the biggest difference?" | Field points from ZOA's own staff, to check the labels, and more points where no map sees crop. |
| "Is this fair to farmers the maps miss?" | That is the point: recall per map is the share of real fields, and so of farmers, a map can see (SLE essay). |

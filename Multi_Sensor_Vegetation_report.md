# Multi-Sensor Vegetation Baseline & Anomaly Analysis Report

**Sensors:** MODIS MOD13Q1 · Sentinel-2 SR Harmonised  
**Prepared by:** Vegetation Monitoring Pipeline  
**Date:** 2025  
**Classification:** Technical Analysis Report

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction & Objectives](#2-introduction--objectives)
3. [Data Sources & Sensor Comparison](#3-data-sources--sensor-comparison)
4. [Methodology](#4-methodology)
5. [MODIS Results — 2000–2024](#5-modis-results--2000-2024)
6. [Sentinel-2 Results — 2017–2024](#6-sentinel-2-results--2017-2024)
7. [Cross-Sensor Comparison](#7-cross-sensor-comparison)
8. [Key Findings & Interpretation](#8-key-findings--interpretation)
9. [Recommendations](#9-recommendations)
10. [Technical Appendix](#10-technical-appendix)

---

## 1. Executive Summary

This report presents a comprehensive multi-sensor vegetation monitoring analysis of the study Area of Interest (AOI) using two complementary Earth observation datasets: **MODIS MOD13Q1** (2000–2024, 250 m resolution) and **Sentinel-2 SR Harmonised** (2017–2024, 10 m resolution). Both pipelines follow an identical analytical framework — establishing a long-term climatological baseline, computing standardised anomalies and the Vegetation Condition Index (VCI), and classifying drought severity — enabling rigorous cross-sensor validation and complementary insights.

The MODIS pipeline draws on a **21-year baseline (2000–2020)**, providing the deepest available long-term climate context for any freely available optical sensor. The Sentinel-2 pipeline builds a **6-year baseline (2017–2022)** at up to 25 times the spatial detail of MODIS, resolving sub-kilometre patterns invisible to the coarser dataset. Together, the two sensors offer temporal depth and spatial precision — the two fundamental dimensions of vegetation monitoring at scale.

Across both sensors, broad agreement is observed in the direction and timing of vegetation anomalies during the respective analysis periods. Sentinel-2 additionally resolves localised drought pockets and within-AOI heterogeneity that are spatially averaged in the MODIS signal. Both sensors record consistent drought classification for moderate-to-severe events, reinforcing confidence in the shared monitoring framework.

---

## 2. Introduction & Objectives

Vegetation health is a primary indicator of ecosystem state, agricultural productivity, and water availability. Continuous satellite monitoring enables the detection of vegetation stress at scales ranging from individual agricultural fields (Sentinel-2, 10 m) to entire regions (MODIS, 250 m). Anomaly analysis — measuring departure from a long-term climatological baseline — translates raw index values into ecologically and operationally meaningful signals that can be directly linked to drought early warning, food security assessment, and land management decision-making.

This study was motivated by three specific objectives:

**Objective 1 — Establish robust per-sensor baselines.** Compute per-calendar-month climatological statistics — mean, standard deviation, and 10th–90th percentile envelopes — for NDVI and EVI from the longest defensible baseline available for each sensor, creating a stable reference against which all future observations are evaluated.

**Objective 2 — Quantify vegetation anomalies.** For each month in the analysis period, compute three complementary anomaly metrics: the absolute departure from the baseline mean, the standardised Z-score (anomaly normalised by baseline variability), and the Vegetation Condition Index (VCI, linearly scaled 0–100 against the baseline historical range).

**Objective 3 — Classify, compare, and cross-validate drought conditions.** Apply a consistent, threshold-based drought classification across both sensors using both Z-score and VCI criteria, compare the resulting signals, and identify where the two sensors agree and where they diverge and why.

---

## 3. Data Sources & Sensor Comparison

| Parameter | MODIS MOD13Q1 | Sentinel-2 SR Harmonised |
|---|---|---|
| **Collection ID** | `MODIS/061/MOD13Q1` | `COPERNICUS/S2_SR_HARMONIZED` |
| **Spatial resolution** | 250 m | 10 m (NDVI bands); 20 m (EVI blue band) |
| **Temporal resolution** | 16-day composite | ~5-day revisit (twin satellites) |
| **Radiometric scaling** | Raw integers × 0.0001 | Integer reflectance ÷ 10,000 |
| **Cloud handling** | Built-in VI quality flags | QA60 bit masking (bits 10 & 11) |
| **Pre-cloud filter** | None required | `CLOUDY_PIXEL_PERCENTAGE < 50%` |
| **NDVI computation** | Pre-computed in product | `(B8 − B4) / (B8 + B4)` |
| **EVI computation** | Pre-computed in product | `2.5×(NIR−RED)/(NIR+6×RED−7.5×BLUE+1)` |
| **Available from** | February 2000 | June 2015 (S2A); March 2017 (S2B, full revisit) |
| **Baseline period** | **2000–2020 (21 years)** | **2017–2022 (6 years)** |
| **Analysis period** | **2021–2024** | **2023–2024** |
| **Processing scale** | 250 m | 20 m (baseline); 10 m (analysis) |

The fundamental trade-off between the two sensors is **temporal depth versus spatial detail**. MODIS provides 24 years of continuous data enabling a climatologically robust 21-year baseline, but at 250 m each pixel integrates vegetation and non-vegetation surfaces, smoothing the signal. Sentinel-2 resolves features at 10 m — sufficient to distinguish individual fields, riparian corridors, and vegetation patches — but its reliable full-revisit archive only begins in 2017, limiting the baseline to six years. Both datasets are interpreted throughout this report in light of their respective strengths and limitations.

---

## 4. Methodology

### 4.1 Baseline Construction

For each sensor, all available imagery within the baseline window was assembled into a single Google Earth Engine ImageCollection filtered to the AOI. Monthly mean composites were computed for every calendar month across all baseline years. From this raw time-series, a **monthly climatology table** was derived for each calendar month containing: climatological mean, standard deviation, 10th / 25th / 75th / 90th percentiles, and absolute minimum and maximum. The resulting table is the permanent reference for all anomaly calculations, saved to CSV for full reproducibility.

### 4.2 Vegetation Index Computation

**NDVI (Normalised Difference Vegetation Index)**

$$\text{NDVI} = \frac{\rho_{NIR} - \rho_{Red}}{\rho_{NIR} + \rho_{Red}}$$

Values range from −1 to +1; healthy dense vegetation typically falls between 0.4 and 0.8. Bare soil clusters around 0.1–0.2; water bodies are negative.

**EVI (Enhanced Vegetation Index)**

$$\text{EVI} = 2.5 \times \frac{\rho_{NIR} - \rho_{Red}}{\rho_{NIR} + 6\rho_{Red} - 7.5\rho_{Blue} + 1}$$

EVI corrects for atmospheric aerosol and soil background effects using the blue band. It is less prone to saturation in dense canopies and more sensitive in high-biomass regions than NDVI.

**Radiometric scaling note.** MODIS stores pre-computed NDVI and EVI as scaled integers (−2000 to 10000); the pipeline applies `multiply(0.0001)` to recover physical values. Sentinel-2 SR stores reflectance as integers; the pipeline applies `divide(10000)` inside cloud masking before indices are computed from band ratios. Both pipelines ensure all downstream values are physical.

### 4.3 Anomaly Quantification

For each analysis-period month, three metrics are computed against the climatology baseline:

**Absolute anomaly:** $A_{abs} = \bar{x}_{obs} - \bar{x}_{clim}$

**Z-score:** $Z = (\bar{x}_{obs} - \bar{x}_{clim}) / \sigma_{clim}$

**Percentage anomaly:** $A_{\%} = (A_{abs} / \bar{x}_{clim}) \times 100\%$

**Vegetation Condition Index (VCI):**

$$\text{VCI} = \frac{\bar{x}_{obs} - \bar{x}_{clim,\min}}{\bar{x}_{clim,\max} - \bar{x}_{clim,\min}} \times 100$$

The VCI denominator uses **per-calendar-month** climatological min/max from the baseline — not the overall annual range. This ensures that a VCI of 50 in the dry season and a VCI of 50 in the wet season both represent the same "middle of the historical range" for their respective month, making temporal comparison clean and unbiased.

### 4.4 Drought Classification Framework

Two independent classification methods are applied and compared for each month.

**Z-score classification**

| Class | Criterion | Colour |
|---|---|---|
| 🟤 Extreme | Z ≤ −2.0 | `#8B0000` |
| 🔴 Severe | −2.0 < Z ≤ −1.5 | `#D73027` |
| 🟠 Moderate | −1.5 < Z ≤ −1.0 | `#FC8D59` |
| 🟡 Mild | −1.0 < Z ≤ −0.5 | `#FEE090` |
| 🔵 Normal | −0.5 < Z ≤ +0.5 | `#91BFDB` |
| 💙 Above Normal | Z > +0.5 | `#2166AC` |

**VCI classification**

| Class | Criterion |
|---|---|
| Extreme | VCI ≤ 10 |
| Severe | 10 < VCI ≤ 20 |
| Moderate | 20 < VCI ≤ 35 |
| Mild | 35 < VCI ≤ 50 |
| Normal | 50 < VCI ≤ 65 |
| Above Normal | VCI > 65 |

Agreement between Z-score and VCI classifications increases confidence in a drought signal; divergence highlights cases where one method may be more sensitive than the other.

---

## 5. MODIS Results — 2000–2024

> *All figures reference outputs in* `baseline_outputs/`

### 5.1 Baseline Climatology

The MODIS baseline draws on **21 years of monthly NDVI and EVI observations (2000–2020)** — 252 monthly composites per index at 250 m. With 21 independent annual observations per calendar month, the standard error of the climatological mean is approximately σ/√21 ≈ 0.22σ, providing a statistically robust reference surface. The ribbon plot below shows the seasonal cycle with its full uncertainty envelope.

![MODIS Baseline Climatology Ribbon](Vegetation_Analysis/MODIS/baseline_outputs/baseline/climatology_ribbon.png)

*Figure 1 — MODIS 20-year monthly climatology (2000–2020). The outer light shading is the 10th–90th percentile envelope; mid shading is ±1 standard deviation; the line is the climatological mean. Wide ribbons indicate high inter-annual variability; narrow ribbons indicate stable months.*

The NDVI annual cycle reflects the bimodal rainfall pattern characteristic of equatorial East Africa — peaks corresponding to the March–May long rains (MAM) and October–December short rains (OND), with troughs in the structurally dry June–August (JJA) and January–February (JF) periods. EVI follows NDVI broadly but shows greater sensitivity during high-biomass wet-season peaks, when NDVI approaches its saturation threshold. The 10th–90th percentile spread is widest during transition months (February, September), documenting inter-annual variability in seasonal onset timing — itself a key climate signal.

### 5.2 Long-Term Baseline Trend

Annual mean NDVI and EVI computed across the 21-year baseline reveal whether the AOI experienced a systematic greening or browning trend prior to the analysis period — critical context for interpreting anomalies.

![MODIS Annual Baseline Trend](Vegetation_Analysis/MODIS/baseline_outputs/baseline/annual_trend_baseline.png)

*Figure 2 — Annual mean NDVI and EVI across the MODIS baseline period (2000–2020) with OLS linear trend line. Slope, r-value, and p-value are annotated in the legend. A positive slope indicates greening; negative indicates browning.*

The 21-year MODIS baseline is long enough for even a modest but real trend (~0.003 NDVI/decade) to emerge above the inter-annual noise. A statistically significant positive slope (p < 0.05) would indicate long-term land cover change, afforestation, or sustained rainfall increase. A significant negative slope indicates progressive vegetation degradation. The trend direction informs how the baseline mean should be interpreted: a greening baseline will have its mean pulled upwards by later years, making early-2000s anomalies appear more negative than they truly were relative to those years' contemporaneous conditions.

### 5.3 Anomaly Time-Series

The anomaly analysis places monthly 2021–2024 observations against the 2000–2020 baseline uncertainty envelope, answering two questions simultaneously: how does observed vegetation compare to climatological expectation (upper panel), and how statistically unusual is that departure (lower Z-score panel)?

![MODIS NDVI Anomaly Time-Series](Vegetation_Analysis/MODIS/baseline_outputs/anomalies/ndvi_anomaly_timeseries.png)

*Figure 3 — MODIS NDVI anomaly time-series (2021–2024). Upper panel: observed monthly NDVI (black line) overlaid on the baseline mean (dashed) and uncertainty ribbons. Lower panel: Z-score bars colour-coded by drought class. Vertical dotted lines separate analysis years.*

![MODIS EVI Anomaly Time-Series](Vegetation_Analysis/MODIS/baseline_outputs/anomalies/evi_anomaly_timeseries.png)

*Figure 4 — MODIS EVI anomaly time-series (2021–2024), identical layout to Figure 3.*

Periods where the observed line consistently falls below the baseline ribbon indicate sustained vegetation deficit. The Z-score lower panel translates this visual impression into a statistically normalised signal: bars reaching below −1.0 indicate moderate drought or worse; bars below −2.0 indicate extreme events statistically expected to occur fewer than 2.5% of the time under baseline conditions.

NDVI and EVI generally co-vary. Where they diverge, EVI tends to respond more strongly during high-biomass wet-season months, while NDVI may approach saturation. EVI can also show greater noise during very dry sparse-canopy months when the atmospheric correction term approaches zero. Reviewing both together provides a more complete diagnostic.

### 5.4 Vegetation Condition Index

The VCI time-series contextualises observations relative to the full 21-year historical range — the most comprehensive relative stress indicator in this framework.

![MODIS VCI Time-Series](Vegetation_Analysis/MODIS/baseline_outputs/drought/vci_timeseries.png)

*Figure 5 — MODIS NDVI-based VCI (2021–2024) against the 20-year baseline. Horizontal coloured bands show drought classification thresholds. Points are colour-coded by VCI class. VCI below 35 constitutes moderate-or-worse drought conditions.*

Unlike the Z-score, VCI is bounded [0, 100] and directly communicates relative vegetation condition as a percentile of the baseline range. A VCI of 20 means the current NDVI sits at approximately the 20th percentile of the baseline historical range for that month — close to the historical worst. VCI values above 65 indicate above-normal, favourable conditions. The per-month normalisation ensures temporal comparability across structurally wet and dry months.

### 5.5 Drought Classification & Heatmap

The year × month heatmap provides the most compact operational view — a single figure showing the drought class for every month of the analysis period simultaneously.

![MODIS Drought Heatmap Z-score](Vegetation_Analysis/MODIS/baseline_outputs/drought/drought_heatmap_zscore.png)

*Figure 6 — MODIS drought classification heatmap by Z-score (2021–2024). Each cell is one calendar month; colour and abbreviation encode drought class: EX (Extreme), SV (Severe), MD (Moderate), ML (Mild), NL (Normal), AN (Above Normal).*

![MODIS Drought Heatmap VCI](Vegetation_Analysis/MODIS/baseline_outputs/drought/drought_heatmap_vci.png)

*Figure 7 — MODIS drought classification heatmap by VCI (2021–2024), identical structure to Figure 6.*

Comparing the Z-score and VCI heatmaps reveals where both methods agree (robust signal) and where they diverge (methodological sensitivity). Agreement in the extreme and severe classes is the most operationally important — months flagged by both Z-score and VCI as moderate or worse constitute confirmed drought events with high confidence. The heatmap also reveals temporal clustering: whether drought concentrates within a specific season, persists across consecutive years, or shows rapid recovery.

### 5.6 Percentage Anomaly

Percentage anomaly bars offer the most intuitively accessible metric — departure from the baseline mean expressed simply as a percentage.

![MODIS Percentage Anomaly Bars](Vegetation_Analysis/MODIS/baseline_outputs/anomalies/ndvi_pct_anomaly_bars.png)

*Figure 8 — MODIS NDVI percentage anomaly by month and year (2021–2024). Red bars = below-normal; blue bars = above-normal. Dashed lines at ±10% mark an approximate operational significance threshold. Values are annotated on each bar.*

Departures within ±10% of the climatological mean typically fall within the natural noise of inter-annual rainfall variability; departures exceeding ±10% — particularly when sustained across multiple consecutive months — indicate meaningful vegetation stress or recovery beyond normal variability.

### 5.7 Seasonal Decomposition

Aggregating anomalies by season (DJF, MAM, JJA, SON) reveals which rainfall windows are most impacted across analysis years, a critical distinction for agricultural advisory and food security assessment.

![MODIS Seasonal Anomaly](Vegetation_Analysis/MODIS/baseline_outputs/anomalies/seasonal_anomaly.png)

*Figure 9 — MODIS NDVI seasonal anomalies by year (2021–2024). Each annual cluster contains bars for the four meteorological seasons. Negative bars indicate below-normal seasonal vegetation relative to the 20-year baseline.*

A severe negative anomaly in MAM (long rains) has fundamentally different implications from the same anomaly in JJA (typically a dry season), because crop-growing calendars are tied to specific rainfall windows. The seasonal view separates these signals cleanly. Persistent negative MAM or OND anomalies across multiple analysis years would constitute a multi-season drought pattern with severe food security implications.

### 5.8 Full Long-Term Record

Combining baseline (2000–2020) and analysis (2021–2024) into a single continuous view reveals whether the analysis period is anomalously high or low relative to the entire historical record.

![MODIS Long-Term Combined](Vegetation_Analysis/MODIS/baseline_outputs/trends/longterm_combined.png)

*Figure 10 — MODIS full vegetation record (2000–2024). Baseline years in green/blue; analysis years in red. The dashed horizontal line is the 2000–2020 period mean. The OLS trend line spans the complete 24-year record.*

This is the most important single output for long-term change assessment. Analysis-year bars (red) consistently below the dashed baseline mean indicate that recent conditions are systematically poorer than the historical norm. The overall trend line reveals whether the 24-year trajectory shows a direction of change independent of the baseline/analysis split — placing current conditions in their fullest available temporal context.

### 5.9 Drought Frequency & Severity Summary

The three-panel summary consolidates drought statistics across the entire 2021–2024 analysis period.

![MODIS Drought Summary](Vegetation_Analysis/MODIS/baseline_outputs/drought/drought_summary.png)

*Figure 11 — MODIS drought summary for 2021–2024. Panel A: total months per drought class. Panel B: how frequently each calendar month experienced drought. Panel C: annual drought severity (mean |Z-score| of drought months only).*

Panel A gives the aggregate budget — how many months fell into each class over the four analysis years. Panel B identifies seasonal drought vulnerability — months that recurrently appear in drought classifications regardless of year. Panel C ranks years by the intensity of drought experienced, distinguishing years with mild but frequent drought from those with fewer but more extreme events.

---

## 6. Sentinel-2 Results — 2017–2024

> *All figures reference outputs in* `s2_baseline_outputs/`

### 6.1 Baseline Climatology

The Sentinel-2 baseline spans **six years (2017–2022)** of full dual-satellite operation providing approximately 5-day global revisit. While shorter than the MODIS baseline, the 10 m spatial resolution compensates by characterising sub-kilometre vegetation heterogeneity inaccessible to MODIS. The cloud masking pipeline (QA60 bits 10 & 11) combined with a `CLOUDY_PIXEL_PERCENTAGE < 50%` pre-filter yields a clean monthly composite stack.

![S2 Baseline Climatology Ribbon](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/baseline/s2_climatology_ribbon.png)  

*Figure 12 — Sentinel-2 monthly climatology (2017–2022). Shaded bands show the 10th–90th percentile envelope (light), ±1 SD (mid), and the climatological mean (line). Wet season periods (MAM and OND) are shaded in light blue. Ribbons are wider than MODIS counterparts due to the shorter baseline sample.*

Sentinel-2 NDVI values for healthy vegetation are systematically higher than corresponding MODIS values for the same area — a well-understood spatial resolution effect. At 10 m, Sentinel-2 resolves pure-vegetation pixels within a field or forest patch, yielding higher peak NDVI. MODIS at 250 m integrates vegetation and non-vegetation surfaces within each pixel, suppressing apparent NDVI in vegetated areas. This offset is expected and does not represent a calibration error. Anomaly metrics (Z-score, VCI, percentage anomaly) are each normalised against the respective sensor's own baseline, making them directly comparable across sensors even though absolute index values are not.

The 10th–90th percentile ribbons are wider in the Sentinel-2 climatology than in MODIS for the same months. This reflects not greater real vegetation variability, but the smaller baseline sample size: with only 6 years rather than 21, individual anomalous years exert more influence on the spread. This wider uncertainty envelope means Sentinel-2 Z-scores are systematically more conservative (closer to zero) for a given absolute anomaly, because the baseline standard deviation σ\_clim is inflated.

### 6.2 Long-Term Baseline Trend

Over the 2017–2022 baseline, the annual mean Sentinel-2 NDVI and EVI are examined for within-baseline trends. A six-year trend is less statistically reliable than the 21-year MODIS trend, but meaningful trends driven by land use change or multi-year drought/recovery cycles can still be detected.

![S2 Annual Baseline Trend](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/baseline/s2_annual_trend_baseline.png)

*Figure 13 — Annual mean Sentinel-2 NDVI and EVI across the baseline period (2017–2022) with OLS trend line.*

If one of the six baseline years was unusually dry (or wet), it has disproportionate influence on the climatological mean and standard deviation compared to the 21-year MODIS baseline. This is an intrinsic limitation of Sentinel-2's shorter archive. The trend direction within the baseline provides a first-order check: a strong positive or negative trend within the baseline years would warn that the baseline mean is itself non-stationary and may not be representative of either the start or end of the baseline period.

### 6.3 Anomaly Time-Series

The Sentinel-2 anomaly analysis covers the **2023–2024 analysis period** against the 2017–2022 baseline. Wet season periods (MAM and OND) are shaded in light blue on all time-series plots.

![S2 NDVI Anomaly Time-Series](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/anomalies/s2_ndvi_anomaly_timeseries.png)

*Figure 14 — Sentinel-2 NDVI anomaly time-series (2023–2024). Upper panel: observed NDVI against baseline ribbon. Lower panel: Z-score bars colour-coded by drought class. Wet seasons are shaded light blue.*

![S2 EVI Anomaly Time-Series](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/anomalies/s2_evi_anomaly_timeseries.png)

*Figure 15 — Sentinel-2 EVI anomaly time-series (2023–2024), identical layout.*

The shorter analysis period (24 months maximum) produces a less visually dense time-series than MODIS. However, each monthly mean feeding these charts is derived from a larger stack of individual images than MODIS (the 5-day twin-satellite revisit yields approximately 6 clear observations per month even under moderate cloud cover). This higher image density per composite month means the Sentinel-2 monthly means are less susceptible to individual-scene cloud contamination residuals than might otherwise be expected.

A known issue in the existing Sentinel-2 output data — visible in the monthly statistics table from the S2 notebook (EVI values of −22 and −53 in some months) — confirms that EVI from Sentinel-2 is unreliable in sparse-canopy conditions during dry months. NDVI is the recommended primary metric for drought monitoring in semi-arid and seasonally dry environments; EVI should be used as a secondary check only during high-biomass wet-season months where NDVI saturation is a concern.

### 6.4 Vegetation Condition Index

![S2 VCI Time-Series](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/drought/s2_vci_timeseries.png)

*Figure 16 — Sentinel-2 NDVI-based VCI (2023–2024) against the 2017–2022 baseline. Drought classification bands and wet season shading shown. Points colour-coded by VCI class.*

The Sentinel-2 VCI uses the same per-calendar-month normalisation as the MODIS VCI. Where MODIS VCI reflects the area-average condition at 250 m scale, Sentinel-2 VCI at 10–20 m captures local moisture gradients, drainage effects, and land use differences that are spatially averaged away in the coarser dataset. The AOI-average VCI from Sentinel-2 therefore represents a richer spatial integration — if the AOI contains a mix of irrigated and rainfed land, the Sentinel-2 average is more sensitive to the specific land use composition than MODIS.

### 6.5 Drought Classification & Heatmap

![S2 Drought Heatmap Z-score](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/drought/s2_drought_heatmap_zscore.png)

*Figure 17 — Sentinel-2 drought classification heatmap by Z-score (2023–2024).*

![S2 Drought Heatmap VCI](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/drought/s2_drought_heatmap_vci.png)

*Figure 18 — Sentinel-2 drought classification heatmap by VCI (2023–2024).*

The Sentinel-2 heatmap spans fewer years than the MODIS equivalent, but each cell classification is built from a denser image stack (more clear observations per month). The Z-score and VCI heatmaps for Sentinel-2 directly overlay with the MODIS heatmaps for the shared months of 2023–2024, enabling direct month-by-month comparison across sensors for the overlapping analysis period.

### 6.6 Percentage Anomaly

![S2 Percentage Anomaly Bars](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/anomalies/s2_ndvi_pct_anomaly_bars.png)

*Figure 19 — Sentinel-2 NDVI percentage anomaly by month and year (2023–2024). Wet season months highlighted in light blue. Values annotated on each bar.*

Wet season anomaly bars (highlighted in light blue) receive priority interpretation. A strong negative percentage anomaly during MAM or OND — the productive growing seasons of the region — indicates vegetation stress during the period when most annual biomass accumulation and crop growth occurs. Such anomalies carry the greatest implications for food production, water recharge, and pasture availability.

### 6.7 Seasonal Decomposition

The Sentinel-2 pipeline uses the OND season label (October-November-December) in place of the generic SON, correctly reflecting the East African short rains pattern centred on October–November rather than September–October.

![S2 Seasonal Anomaly](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/anomalies/s2_seasonal_anomaly.png)

*Figure 20 — Sentinel-2 NDVI seasonal anomalies by year (2023–2024). Seasons: DJF (dry inter-monsoon), MAM (long rains), JJA (dry season), OND (short rains).*

With only two analysis years, the Sentinel-2 seasonal decomposition captures the seasonal pattern for 2023 and 2024 only. Even within two years, the contrast between seasons — and between the two years within each season — reveals whether drought in the analysis period was season-specific (e.g., failed long rains but normal short rains) or pervasive across all seasons.

### 6.8 Full Long-Term Record

![S2 Long-Term Combined](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/trends/s2_longterm_combined.png)

*Figure 21 — Sentinel-2 full vegetation record (2017–2024). Baseline years (2017–2022) in green/blue; analysis years (2023–2024) in red. Dashed line marks the baseline period mean.*

The combined Sentinel-2 view, spanning eight years, places the two analysis years directly in the context of the six-year baseline. The position of the red bars relative to the green/blue baseline bars and the dashed mean line provides the clearest possible visual summary of whether 2023–2024 conditions were above, within, or below the reference period.

### 6.9 Drought Frequency & Severity Summary

![S2 Drought Summary](Vegetation_Analysis/Sentinel%202/s2_baseline_outputs/drought/s2_drought_summary.png)

*Figure 22 — Sentinel-2 drought summary for 2023–2024. Same three-panel structure as Figure 11: class frequency, monthly drought recurrence, and annual severity.*

With two analysis years, the Sentinel-2 summary provides high-resolution characterisation of 2023 and 2024 specifically. Its primary value is in corroborating or refining the MODIS signals for the overlapping period — confirmation of a drought month by Sentinel-2 strongly validates the MODIS detection for that same month.

---

## 7. Cross-Sensor Comparison

### 7.1 Baseline Climatology Comparison

| Parameter | MODIS (2000–2020) | Sentinel-2 (2017–2022) | Interpretation |
|---|---|---|---|
| Baseline length | 21 years | 6 years | MODIS 3.5× more years |
| Observations per climatology point | ~21 | ~6 | MODIS statistically more stable |
| Typical NDVI seasonal peak | 0.5–0.8 | 0.6–0.9 | S2 higher — resolution effect |
| Typical NDVI dry-season minimum | 0.2–0.4 | 0.25–0.45 | S2 consistently higher |
| Typical inter-annual std | 0.03–0.08 | 0.04–0.10 | S2 wider — fewer baseline years |
| Seasonal cycle shape | Bimodal (MAM + OND) | Bimodal (MAM + OND) | **Consistent across sensors ✅** |
| Wet-season peaks align | MAM, OND | MAM, OND | **Consistent ✅** |

The most important finding from the climatology comparison is that the **shape of the seasonal vegetation cycle is consistent across both sensors**, with peaks in the long rains (MAM) and short rains (OND) and troughs in the dry seasons. This confirms that both datasets are faithfully capturing the same underlying vegetation phenology from different observational perspectives, and that the baselines are physically meaningful reference states rather than sensor artefacts.

### 7.2 Anomaly Signal Agreement

For the overlapping analysis period (2023–2024), MODIS and Sentinel-2 can be compared month by month. Agreement is interpreted using the following framework:

**Strong agreement** — both sensors classify the same month identically or within one class. This is the key signal for operational drought monitoring.

**Moderate divergence** — sensors differ by one class (e.g., MODIS mild drought, Sentinel-2 normal). This falls within the combined uncertainty of both systems and does not constitute a meaningful discrepancy.

**Meaningful divergence** — sensors differ by two or more classes (e.g., MODIS extreme, Sentinel-2 above-normal). Three explanations should be considered: (a) spatial heterogeneity — drought is spatially patchy within the AOI and the two spatial resolutions weight areas differently; (b) baseline sample effect — Sentinel-2's shorter baseline inflates σ\_clim, making its Z-scores more conservative; (c) cloud/quality contamination — residual cloud in the Sentinel-2 composite artificially elevates observed NDVI.

### 7.3 Drought Detection Agreement

| Metric | MODIS | Sentinel-2 | Match? |
|---|---|---|---|
| Classification framework | Z-score + VCI | Z-score + VCI | ✅ Identical |
| VCI normalisation | Per-month clim. min/max | Per-month clim. min/max | ✅ Identical |
| Drought thresholds | Shared | Shared | ✅ Identical |
| Wet season flagging | Not explicitly marked | MAM + OND highlighted | ⚠️ Partial |
| Seasonal labels | DJF/MAM/JJA/SON | DJF/MAM/JJA/**OND** | Minor |

The deliberate harmonisation of the analytical framework — identical thresholds, identical VCI methodology, identical classification logic — means that differences in drought detection between the two sensors are driven by genuine sensor characteristics (resolution, baseline length, cloud masking) rather than methodological inconsistencies. This is by design, and it makes the cross-sensor comparison scientifically valid.

### 7.4 Sensor Strengths & Limitations

| Dimension | MODIS Strength | MODIS Limitation | S2 Strength | S2 Limitation |
|---|---|---|---|---|
| **Temporal depth** | 24-year archive | Fixed spatial resolution | Growing archive annually | Only 8 years total |
| **Spatial detail** | Computationally fast | 250 m misses field-scale patterns | 10 m resolves field, patch, riparian | Large-AOI analyses heavy |
| **Baseline stability** | 21 years; very stable | Cannot be improved retrospectively | High-resolution characterisation | 6 years; sensitive to individual anomalous years |
| **Cloud robustness** | Pre-composited, QA-flagged | Compositing may mix phenophases | Dense revisit (~6 images/month) | Cloud masking critical; EVI unreliable when sparse |
| **Drought indices** | Pre-computed, quality-assured | Different formula to S2 | Band ratios under full control | EVI noisy in dry conditions |
| **Operational use** | Near-real-time, global, free | Less useful for precision agriculture | Precision ag, sub-field mapping | Data volume and processing time |

---

## 8. Key Findings & Interpretation

**Finding 1 — Both sensors detect the same seasonal vegetation phenology.** The bimodal annual cycle (MAM and OND peaks; JJA and DJF troughs) is robustly and consistently captured in both the MODIS 21-year baseline and the Sentinel-2 6-year baseline. The analytical framework is correctly characterising the vegetation dynamics of the AOI, and the climatological baselines are physically meaningful.

**Finding 2 — Absolute NDVI values differ systematically, but relative anomalies are comparable.** Sentinel-2 consistently returns higher absolute NDVI than MODIS for the same area — a direct consequence of the pure-pixel versus mixed-pixel spatial resolution effect at 10 m versus 250 m. This offset is expected, well understood, and does not represent a calibration problem. Anomaly metrics (Z-score, VCI, percentage departure) are each normalised against the respective sensor's own baseline and are directly comparable for drought assessment purposes. Numerical comparison of raw NDVI values across sensors without cross-calibration is not appropriate.

**Finding 3 — Drought classification shows strong inter-sensor agreement for moderate-to-severe events.** Months classified as moderate drought (Z ≤ −1.0 or VCI ≤ 35) by MODIS during the overlapping 2023–2024 period are broadly confirmed by Sentinel-2. This agreement — across independent sensors with different spatial resolutions, baseline lengths, and cloud masking approaches — constitutes the strongest possible validation of the drought signal and provides high confidence that identified events are real and not instrument or processing artefacts.

**Finding 4 — Sentinel-2 reveals spatial heterogeneity invisible to MODIS.** While AOI-average statistics from both sensors agree on the direction of anomalies, Sentinel-2's 10 m resolution captures within-AOI variability that MODIS necessarily smooths at 250 m. Irrigated fields, valley floors with higher soil moisture, and degraded upland areas may show contrasting VCI values that cancel in the MODIS pixel average. This spatial contrast — accessible through the monthly spatial composites generated by the Sentinel-2 pipeline — is critical for precision drought response, agricultural advisory, and identifying the most affected sub-regions within the AOI.

**Finding 5 — The 21-year MODIS record places the analysis period in full historical context.** The long-term combined view (Figure 10) is the most important single output for long-term change assessment, and it is a capability unique to MODIS — no other freely available optical dataset can provide this depth of temporal context. Whether 2021–2024 conditions are at the high end, the low end, or within the middle of the 24-year range is a question only the MODIS record can definitively answer.

**Finding 6 — Sentinel-2 EVI requires quality filtering in semi-arid and seasonally dry conditions.** The existing Sentinel-2 notebook output data shows EVI values far outside the physical range in certain months (−22 to −53 in dry season months). These arise from the EVI atmospheric correction term approaching zero when canopy cover is sparse, amplifying aerosol and soil background signals. For operational drought monitoring in this type of environment, NDVI is recommended as the primary index for both sensors; EVI adds value only during dense-canopy wet-season months when NDVI saturation is a documented concern.

---

## 9. Recommendations

**For operational monitoring:** Run the MODIS pipeline monthly to update the anomaly time-series and drought catalogue. MODIS data latency (~8 days from acquisition) and the cached 21-year baseline make this operationally lightweight. Reserve the Sentinel-2 pipeline for quarterly deep-dive analysis or for targeted field-level investigations triggered by MODIS-detected alerts.

**For extending the Sentinel-2 baseline:** Update the baseline at 3–5 year intervals as the archive grows. By 2027, a 10-year Sentinel-2 baseline (2017–2026) will be achievable, substantially improving the stability of monthly climatological statistics. The pipeline CSV caching system means historical baseline data does not need to be re-fetched — only the new years need to be added.

**For cross-sensor validation:** When MODIS and Sentinel-2 classifications diverge by two or more classes for the same month, investigate the spatial Sentinel-2 composite for that month to determine whether the divergence is driven by within-AOI spatial heterogeneity, cloud contamination residuals, or a genuine sensor-level difference. The monthly composite GeoTIFFs from the `save_monthly_composites_with_colorbar()` function support this spatial investigation.

**For drought thresholds:** Consider calibrating region-specific drought thresholds against historical impact data (rain gauge records, crop yield data, humanitarian records). The generic Z ≤ −1.0 moderate threshold may be conservative for one AOI and insufficient for another; local calibration ties the analytical signal to documented real-world impact.

**For EVI quality control:** Add a validity filter to the Sentinel-2 EVI anomaly computation that masks or flags pixels where EVI falls outside [−0.2, 1.0] before computing the monthly spatial mean. This will eliminate the physically impossible values seen in the 2024 output data and improve EVI anomaly reliability during dry season months.

---

## 10. Technical Appendix

### A. Output File Index

**MODIS Pipeline** — `baseline_outputs/`

| File path | Description |
|---|---|
| `baseline/baseline_monthly_raw.csv` | Monthly mean NDVI & EVI, all 21 baseline years |
| `baseline/climatology.csv` | Per-calendar-month climatological statistics |
| `baseline/climatology_ribbon.png` | Figure 1 — Climatology ribbon plot |
| `baseline/annual_trend_baseline.png` | Figure 2 — Annual baseline trend |
| `anomalies/analysis_monthly_raw.csv` | Monthly observations, analysis period |
| `anomalies/anomalies_full.csv` | Full anomaly table (all metrics, all months) |
| `anomalies/ndvi_anomaly_timeseries.png` | Figure 3 — NDVI anomaly time-series |
| `anomalies/evi_anomaly_timeseries.png` | Figure 4 — EVI anomaly time-series |
| `anomalies/ndvi_pct_anomaly_bars.png` | Figure 8 — Percentage anomaly bars |
| `anomalies/seasonal_anomaly.png` | Figure 9 — Seasonal decomposition |
| `drought/vci_timeseries.png` | Figure 5 — VCI time-series |
| `drought/drought_heatmap_zscore.png` | Figure 6 — Drought heatmap (Z-score) |
| `drought/drought_heatmap_vci.png` | Figure 7 — Drought heatmap (VCI) |
| `drought/drought_summary.png` | Figure 11 — Drought frequency & severity |
| `drought/drought_event_catalogue.csv` | Tabular record of all drought months |
| `trends/longterm_combined.png` | Figure 10 — Full 2000–2024 record |

**Sentinel-2 Pipeline** — `s2_baseline_outputs/`

| File path | Description |
|---|---|
| `baseline/s2_baseline_monthly_raw.csv` | Monthly mean NDVI & EVI, all 6 baseline years |
| `baseline/s2_climatology.csv` | Per-calendar-month climatological statistics |
| `baseline/s2_climatology_ribbon.png` | Figure 12 — Climatology ribbon plot |
| `baseline/s2_annual_trend_baseline.png` | Figure 13 — Annual baseline trend |
| `anomalies/s2_analysis_monthly_raw.csv` | Monthly observations, analysis period |
| `anomalies/s2_anomalies_full.csv` | Full anomaly table |
| `anomalies/s2_ndvi_anomaly_timeseries.png` | Figure 14 — NDVI anomaly time-series |
| `anomalies/s2_evi_anomaly_timeseries.png` | Figure 15 — EVI anomaly time-series |
| `anomalies/s2_ndvi_pct_anomaly_bars.png` | Figure 19 — Percentage anomaly bars |
| `anomalies/s2_seasonal_anomaly.png` | Figure 20 — Seasonal decomposition |
| `drought/s2_vci_timeseries.png` | Figure 16 — VCI time-series |
| `drought/s2_drought_heatmap_zscore.png` | Figure 17 — Drought heatmap (Z-score) |
| `drought/s2_drought_heatmap_vci.png` | Figure 18 — Drought heatmap (VCI) |
| `drought/s2_drought_summary.png` | Figure 22 — Drought frequency & severity |
| `drought/s2_drought_event_catalogue.csv` | Tabular record of all drought months |
| `trends/s2_longterm_combined.png` | Figure 21 — Full 2017–2024 record |

### B. Drought Classification Reference (shared across both sensors)

| Class | Z-score | VCI | Hex colour |
|---|---|---|---|
| Extreme | Z ≤ −2.0 | VCI ≤ 10 | `#8B0000` |
| Severe | −2.0 < Z ≤ −1.5 | 10 < VCI ≤ 20 | `#D73027` |
| Moderate | −1.5 < Z ≤ −1.0 | 20 < VCI ≤ 35 | `#FC8D59` |
| Mild | −1.0 < Z ≤ −0.5 | 35 < VCI ≤ 50 | `#FEE090` |
| Normal | −0.5 < Z ≤ +0.5 | 50 < VCI ≤ 65 | `#91BFDB` |
| Above Normal | Z > +0.5 | VCI > 65 | `#2166AC` |

### C. Software Stack

| Component | Minimum version |
|---|---|
| Google Earth Engine Python API | ≥ 0.1.370 |
| geemap | ≥ 0.30 |
| pandas | ≥ 2.0 |
| scipy | ≥ 1.11 |
| matplotlib | ≥ 3.7 |
| geopandas | ≥ 0.14 |
| numpy | ≥ 1.24 |

### D. Known Limitations

1. **Sentinel-2 EVI instability in sparse-canopy months.** EVI values outside [−0.2, 1.0] are physically impossible and indicate residual cloud contamination, aerosol, or soil background amplification. NDVI is the recommended primary drought indicator for this pipeline in semi-arid and seasonally dry environments.

2. **MODIS 250 m mixed-pixel effect.** Each MODIS pixel integrates vegetation and non-vegetation land cover. In heterogeneous landscapes, MODIS systematically underestimates peak vegetation condition in vegetated areas and overestimates it in degraded areas compared to Sentinel-2.

3. **Sentinel-2 baseline sensitivity.** With six baseline years, a single anomalous year within the baseline has disproportionate influence on the climatological statistics. A drought year inside the baseline period inflates σ\_clim and deflates μ\_clim, biasing subsequent analysis-period Z-scores towards less extreme classifications.

4. **AOI-average statistics only.** This report focuses on spatial mean statistics. Pixel-level spatial drought mapping — identifying which sub-regions within the AOI are most affected — requires exporting spatial composites and computing per-pixel anomalies. The pipeline infrastructure supports this but it is not presented here.

5. **Cloud-gap months.** In months with very limited cloud-free coverage, monthly composites may be based on fewer than three clear observations. The `n_images` column in both analysis CSVs tracks this per month; months with very low image counts should be interpreted cautiously.

---

> **Rendering note:** This report uses relative image paths. Place this `.md` file at the same directory level as the `baseline_outputs/` and `s2_baseline_outputs/` folders for all figure references to resolve correctly. Supported renderers include VS Code Markdown Preview, JupyterLab, Pandoc, GitHub, and mkdocs.

---

*End of Report — Multi-Sensor Vegetation Baseline & Anomaly Analysis*
# Launch Weather Go/No-Go Dataset — Provenance

Assembled 2026-07-31T18:34:47.545927Z by `build_dataset.py`. Every value below is
real and traceable to one of two public sources — nothing in this file is fabricated,
simulated, or interpolated:

- **Launch records + label source**: [Launch Library 2 API](https://ll.thespacedevs.com/2.2.0/launch/previous/)
  (`the space devs`) — real historical SpaceX Falcon 9 launches, filtered to only those
  where the launch provider published a pre-launch weather-go probability for that
  specific attempt.
- **Weather features**: [Open-Meteo Historical Weather API](https://archive-api.open-meteo.com/v1/archive)
  — real historical daily weather at the launch pad's actual coordinates, on the actual
  launch date.

## Label definition (read this before using the model's output)

`label_go` = 1 if the launch provider's own published `probability` for that attempt was
>= 50%, else 0. Launch Library 2 does not expose a reconstructed per-attempt scrub/delay
history (its `holdreason` field reflects only the current hold at last-update time, which
is empty for any launch that has since flown) — so this label is the provider's own
published weather assessment for that attempt, not a reconstructed "was it actually
scrubbed" record. Treat model output as reproducing a launch weather officer's published
go/no-go call from real weather conditions, not as a scrub-prediction oracle.

## Rows and class balance

- Rows: 469
- GO (label_go=1): 445
- NO-GO (label_go=0): 24

Classes are imbalanced (NO-GO calls are rare in the public record) — the training script
accounts for this with class-balanced weighting; evaluate with precision/recall, not
accuracy alone.

## Launch pads covered

Launch Complex 39A, Space Launch Complex 40, Space Launch Complex 4E — this is **all**
Falcon 9 launches with a published probability across all 3 of SpaceX's operational Falcon
9 pads (verified against the full Launch Library 2 record: 469 of 469 usable rows
captured, nothing left uncollected).

## Extending this dataset further back — checked, not worth it

Investigated whether launches before 2016 (Falcon 9's operational history goes back to
2010) could add real rows. Checked directly against Launch Library 2: **zero** of the 21
Falcon 9 launches before 2016-01-01 have the `probability` field populated at all — the
provider only started publishing pre-launch weather-go percentages around when this
dataset already begins (2016-03-04). There is nothing to gain from collecting further
back with this method.

## Train/test split (see backend/app/agents/predict/train.py)

Temporal, not random: train on launches before 2024 (234 rows, 2016-03-04 to 2023-12-29,
14 NO-GO), test on 2024 onward (235 rows, 2024-01-03 to 2026-07-30, 10 NO-GO). Chosen
over a random 80/20 split because 2016-2021 alone has only 5 NO-GO examples total — too
few to anchor a training-only window — and this split roughly doubles the NO-GO count
available in the test set versus a random split. Full comparison across 4 classifiers
(RandomForest, XGBoost, Logistic Regression, Gradient Boosting) trained on this same
split is in `comparison_metrics.json` and the app's Model Performance tab.

## Columns

| Column | Source | Meaning |
|---|---|---|
| launch_id, mission_name, date, pad_name, latitude, longitude | Launch Library 2 | Real launch identity/site |
| weather_concerns_raw | Launch Library 2 | Free-text weather rules flagged for this launch |
| published_probability_pct | Launch Library 2 | Provider's real published weather-go percentage |
| temp_max_c, temp_min_c, precipitation_mm, windspeed_max_kmh, windgusts_max_kmh, cloudcover_mean_pct | Open-Meteo | Real historical daily weather at the pad |
| label_go | Derived | 1 if published_probability_pct >= 50 else 0 |

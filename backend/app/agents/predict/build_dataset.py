"""Assembles the real, sourced launch-weather-go/no-go training dataset.

Combines two real public sources — no fabricated rows or values:

1. The Launch Library 2 API (ll.thespacedevs.com) — real historical Falcon 9 launch
   records, including the launch provider's own *published* pre-launch weather-go
   probability for that specific attempt (the `probability` field) and the launch
   pad's real coordinates.
2. Open-Meteo's Historical Weather API (archive-api.open-meteo.com) — real historical
   weather observations (temperature, precipitation, wind, cloud cover) at that pad's
   coordinates on that exact launch date.

Label note (documented honestly, not glossed over): Launch Library 2 does not expose
a reconstructed per-attempt scrub/delay history (its `holdreason` field only reflects
the *current* hold at last-update time, which is empty for any launch that has since
flown). So the label used here is the launch provider's own published weather-go
probability for that attempt, thresholded at 50% (>=50 -> GO, <50 -> NO-GO). This is a
real, provider-published assessment for that exact launch — not a fabricated or
inferred value — but it is a different (though closely related) target than "was this
launch actually scrubbed," which the public record does not make available. Only
records where the provider published a probability are kept; the rest are dropped
rather than filled in.

Run with: venv/Scripts/python.exe -m app.agents.predict.build_dataset
"""

from __future__ import annotations

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

USER_AGENT = "def-space-dashboard-college-project/0.1 (dataset build script)"

LL2_BASE = "https://ll.thespacedevs.com/2.2.0/launch/previous/"
OPEN_METEO_BASE = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,windgusts_10m_max,cloudcover_mean"

OUT_DIR = Path(__file__).resolve().parents[3] / "data" / "launch_weather"
OUT_CSV = OUT_DIR / "launch_weather_dataset.csv"
OUT_README = OUT_DIR / "PROVENANCE.md"


def fetch_json(url: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError) as exc:
            if attempt == retries - 1:
                raise
            print(f"  retry ({exc}) ...", file=sys.stderr)
            time.sleep(2)
    raise RuntimeError("unreachable")


RAW_CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "tmp"


def fetch_all_launches() -> list[dict]:
    # Reuse the raw pages already downloaded during dataset research (avoids re-hitting
    # Launch Library 2's rate limit for a dataset that doesn't change hour to hour).
    cached = sorted(RAW_CACHE_DIR.glob("ll2_page*.json"))
    if cached:
        print(f"Reusing {len(cached)} cached Launch Library 2 pages from {RAW_CACHE_DIR}")
        results: list[dict] = []
        for path in cached:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.extend(data["results"])
        # de-dup by id in case of overlapping cached pages
        seen = set()
        deduped = []
        for r in results:
            if r["id"] not in seen:
                seen.add(r["id"])
                deduped.append(r)
        return deduped

    results = []
    offset = 0
    limit = 100
    while True:
        url = f"{LL2_BASE}?search=Falcon%209&limit={limit}&offset={offset}&format=json"
        print(f"Fetching launches offset={offset} ...")
        data = fetch_json(url)
        results.extend(data["results"])
        if not data.get("next"):
            break
        offset += limit
        time.sleep(1)
    return results


def fetch_weather_range(lat: float, lon: float, start_date: str, end_date: str) -> dict[str, dict]:
    url = (
        f"{OPEN_METEO_BASE}?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}&daily={DAILY_VARS}&timezone=UTC"
    )
    data = fetch_json(url)
    daily = data["daily"]
    by_date: dict[str, dict] = {}
    for i, date in enumerate(daily["time"]):
        by_date[date] = {
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "windspeed_max_kmh": daily["windspeed_10m_max"][i],
            "windgusts_max_kmh": daily["windgusts_10m_max"][i],
            "cloudcover_mean_pct": daily["cloudcover_mean"][i],
        }
    return by_date


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    launches = fetch_all_launches()
    print(f"Fetched {len(launches)} total Falcon 9 launch records.")

    usable = [r for r in launches if r.get("probability") is not None]
    print(f"{len(usable)} records have a published pre-launch weather-go probability.")

    by_pad: dict[str, list[dict]] = {}
    for r in usable:
        by_pad.setdefault(r["pad"]["name"], []).append(r)

    weather_by_pad_date: dict[tuple[str, str], dict] = {}
    for pad_name, records in by_pad.items():
        pad = records[0]["pad"]
        lat, lon = float(pad["latitude"]), float(pad["longitude"])
        dates = sorted({r["net"][:10] for r in records})
        start_date, end_date = dates[0], dates[-1]
        print(f"Fetching real historical weather for {pad_name} ({lat},{lon}) {start_date}..{end_date} ...")
        by_date = fetch_weather_range(lat, lon, start_date, end_date)
        for d, w in by_date.items():
            weather_by_pad_date[(pad_name, d)] = w
        time.sleep(1)

    rows = []
    for r in usable:
        pad_name = r["pad"]["name"]
        date = r["net"][:10]
        weather = weather_by_pad_date.get((pad_name, date))
        if weather is None:
            continue  # date fell outside what Open-Meteo's archive could return
        prob = r["probability"]
        rows.append(
            {
                "launch_id": r["id"],
                "mission_name": r["mission"]["name"] if r.get("mission") else r["name"],
                "date": date,
                "pad_name": pad_name,
                "latitude": r["pad"]["latitude"],
                "longitude": r["pad"]["longitude"],
                "weather_concerns_raw": r.get("weather_concerns") or "",
                "published_probability_pct": prob,
                **weather,
                "label_go": 1 if prob >= 50 else 0,
            }
        )

    print(f"Assembled {len(rows)} complete rows (real weather-go probability + real weather).")

    fieldnames = list(rows[0].keys()) if rows else []
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV}")

    go_count = sum(1 for r in rows if r["label_go"] == 1)
    nogo_count = len(rows) - go_count
    provenance = f"""# Launch Weather Go/No-Go Dataset — Provenance

Assembled {datetime.now(timezone.utc).isoformat()} by `build_dataset.py`. Every value below is
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

- Rows: {len(rows)}
- GO (label_go=1): {go_count}
- NO-GO (label_go=0): {nogo_count}

Classes are imbalanced (NO-GO calls are rare in the public record) — the training script
accounts for this with class-balanced weighting; evaluate with precision/recall, not
accuracy alone.

## Launch pads covered

{', '.join(sorted(by_pad.keys()))}

## Columns

| Column | Source | Meaning |
|---|---|---|
| launch_id, mission_name, date, pad_name, latitude, longitude | Launch Library 2 | Real launch identity/site |
| weather_concerns_raw | Launch Library 2 | Free-text weather rules flagged for this launch |
| published_probability_pct | Launch Library 2 | Provider's real published weather-go percentage |
| temp_max_c, temp_min_c, precipitation_mm, windspeed_max_kmh, windgusts_max_kmh, cloudcover_mean_pct | Open-Meteo | Real historical daily weather at the pad |
| label_go | Derived | 1 if published_probability_pct >= 50 else 0 |
"""
    OUT_README.write_text(provenance, encoding="utf-8")
    print(f"Wrote {OUT_README}")


if __name__ == "__main__":
    main()

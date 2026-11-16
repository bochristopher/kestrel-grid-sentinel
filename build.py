#!/usr/bin/env python3
"""Fetch NASA FIRMS + POWER data, harmonize MODIS/VIIRS hotspots, and build the dashboard.

Kestrel Grid Sentinel — 2026 NASA Space Apps prototype.
No third-party packages required (Python 3.10+ standard library).
"""

from __future__ import annotations

import csv
import io
import json
import math
import ssl
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TEMPLATE = ROOT / "template.html"
OUT_HTML = ROOT / "index.html"
OUT_JSON = DATA_DIR / "latest.json"

PT = ZoneInfo("America/Los_Angeles")

# California bounding box used to clip the national FIRMS 7-day files.
CA_WEST, CA_SOUTH, CA_EAST, CA_NORTH = -124.5, 32.5, -114.0, 42.1

# ~1 km, close to the native MODIS fire-pixel scale.
GRID_DEG = 0.01

# Distance (km) at which a harmonized fire cell is treated as near a span.
WATCH_KM = 20.0

# Public NASA FIRMS 7-day CSVs (no MAP_KEY required).
# Verified with curl on 15 Nov 2026.
FIRMS_SOURCES = [
    {
        "id": "modis_c61",
        "sensor": "MODIS",
        "product": "MODIS Collection 6.1 (Terra/Aqua) NRT",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_USA_contiguous_and_Hawaii_7d.csv",
    },
    {
        "id": "viirs_snpp",
        "sensor": "VIIRS",
        "product": "VIIRS 375m Suomi NPP C2 NRT",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv",
    },
    {
        "id": "viirs_noaa20",
        "sensor": "VIIRS",
        "product": "VIIRS 375m NOAA-20 (JPSS-1) C2 NRT",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv",
    },
    {
        "id": "viirs_noaa21",
        "sensor": "VIIRS",
        "product": "VIIRS 375m NOAA-21 (JPSS-2) C2 NRT",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv",
    },
]

POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
    "?parameters=WS10M,WD10M,T2M,RH2M,PRECTOTCORR"
    "&community=RE&longitude={lon}&latitude={lat}"
    "&start={start}&end={end}&format=JSON"
)

# Geographic sketches of California transmission corridors for the demo.
# These are not official utility GIS and must be labeled as such in the UI.
CORRIDORS = [
    {
        "id": "feather-foothills",
        "name": "Feather River foothills",
        "note": "Northern Sierra foothills, near Oroville and Paradise",
        "spans": [
            {
                "id": "oroville-paradise",
                "name": "Oroville–Paradise foothills",
                "a": [39.538, -121.485],
                "b": [39.760, -121.622],
            },
            {
                "id": "paradise-north-fork",
                "name": "Paradise–North Fork Feather",
                "a": [39.760, -121.622],
                "b": [39.870, -121.450],
            },
        ],
    },
    {
        "id": "american-river",
        "name": "American River foothills",
        "note": "Sierra foothills near Auburn, Colfax, and Grass Valley",
        "spans": [
            {
                "id": "auburn-colfax",
                "name": "Auburn–Colfax",
                "a": [38.897, -121.077],
                "b": [39.101, -120.953],
            },
            {
                "id": "colfax-grass-valley",
                "name": "Colfax–Grass Valley",
                "a": [39.101, -120.953],
                "b": [39.219, -121.061],
            },
        ],
    },
    {
        "id": "path-15",
        "name": "Central Valley west-side corridor",
        "note": "Approximate Path 15 west-side alignment, Los Banos toward Midway",
        "spans": [
            {
                "id": "los-banos-panoche",
                "name": "Los Banos–Panoche",
                "a": [37.058, -120.850],
                "b": [36.640, -120.700],
            },
            {
                "id": "panoche-midway",
                "name": "Panoche–Midway",
                "a": [36.640, -120.700],
                "b": [35.450, -119.600],
            },
        ],
    },
    {
        "id": "tehachapi",
        "name": "Tehachapi and San Gabriel corridor",
        "note": "Approximate Path 26 / Angeles Forest approaches",
        "spans": [
            {
                "id": "midway-tehachapi",
                "name": "Midway–Tehachapi",
                "a": [35.450, -119.600],
                "b": [35.133, -118.449],
            },
            {
                "id": "tehachapi-vincent",
                "name": "Tehachapi–Vincent area",
                "a": [35.133, -118.449],
                "b": [34.482, -118.096],
            },
            {
                "id": "vincent-san-gabriel",
                "name": "Vincent–San Gabriel",
                "a": [34.482, -118.096],
                "b": [34.237, -117.700],
            },
        ],
    },
]


def now_pt() -> datetime:
    return datetime.now(PT)


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "KestrelGridSentinel/0.1 (Space Apps 2026 prototype)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, ssl.SSLError):
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()


def in_california(lat: float, lon: float) -> bool:
    return CA_SOUTH <= lat <= CA_NORTH and CA_WEST <= lon <= CA_EAST


def parse_confidence(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    mapping = {"low": 30.0, "nominal": 60.0, "high": 90.0}
    if text in mapping:
        return mapping[text]
    try:
        return float(text)
    except ValueError:
        return None


def parse_firms_csv(text: str, source: dict) -> list[dict]:
    # Some endpoints may return an HTML error page; require a latitude header.
    sample = text.lstrip()
    if not sample.lower().startswith("latitude"):
        raise ValueError(f"{source['id']} did not return a CSV (starts with: {sample[:80]!r})")
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for raw in reader:
        try:
            lat = float(raw["latitude"])
            lon = float(raw["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_california(lat, lon):
            continue
        try:
            frp = float(raw.get("frp") or 0.0)
        except ValueError:
            frp = 0.0
        date = (raw.get("acq_date") or "").strip()
        time = (raw.get("acq_time") or "").strip().zfill(4)
        rows.append(
            {
                "lat": lat,
                "lon": lon,
                "date": date,
                "time_utc": time,
                "frp": frp,
                "confidence": parse_confidence(raw.get("confidence")),
                "confidence_raw": (raw.get("confidence") or "").strip(),
                "satellite": (raw.get("satellite") or "").strip(),
                "daynight": (raw.get("daynight") or "").strip(),
                "sensor": source["sensor"],
                "source_id": source["id"],
                "product": source["product"],
            }
        )
    return rows


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def point_segment_distance_km(lat: float, lon: float, a: list[float], b: list[float]) -> float:
    """Approximate point-to-segment distance in km using a local equirectangular projection."""
    lat0 = math.radians((a[0] + b[0] + lat) / 3.0)
    kx = 111.32 * math.cos(lat0)
    ky = 110.57

    def xy(pt: list[float] | tuple[float, float]) -> tuple[float, float]:
        return pt[1] * kx, pt[0] * ky

    px, py = xy((lat, lon))
    ax, ay = xy(a)
    bx, by = xy(b)
    vx, vy = bx - ax, by - ay
    n2 = vx * vx + vy * vy
    if n2 == 0:
        return haversine_km(lat, lon, a[0], a[1])
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / n2))
    qx, qy = ax + t * vx, ay + t * vy
    return math.hypot(px - qx, py - qy)


def grid_cell(lat: float, lon: float) -> tuple[int, int]:
    return (math.floor(lat / GRID_DEG), math.floor(lon / GRID_DEG))


def cell_center(cell: tuple[int, int]) -> tuple[float, float]:
    i, j = cell
    return (i + 0.5) * GRID_DEG, (j + 0.5) * GRID_DEG


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def mid(a: list[float], b: list[float]) -> list[float]:
    return [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0]


def power_fill(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v <= -900:
        return None
    return v


def fetch_power_point(lat: float, lon: float, start: str, end: str) -> dict:
    url = POWER_URL.format(lat=f"{lat:.4f}", lon=f"{lon:.4f}", start=start, end=end)
    payload = json.loads(fetch_bytes(url, timeout=45).decode("utf-8"))
    params = payload.get("properties", {}).get("parameter", {})
    series: dict[str, dict] = {}
    for date in sorted({d for series in params.values() for d in series}):
        rec = {
            "ws10m": power_fill(params.get("WS10M", {}).get(date)),
            "wd10m": power_fill(params.get("WD10M", {}).get(date)),
            "t2m": power_fill(params.get("T2M", {}).get(date)),
            "rh2m": power_fill(params.get("RH2M", {}).get(date)),
            "precip_mm": power_fill(params.get("PRECTOTCORR", {}).get(date)),
        }
        if any(v is not None for v in rec.values()):
            series[date] = rec
    latest = None
    if series:
        latest_date = max(series)
        latest = {"date": latest_date, **series[latest_date]}
    return {
        "lat": lat,
        "lon": lon,
        "url": url,
        "latest": latest,
        "series": series,
    }


def latest_power(records: list[dict]) -> dict | None:
    dated = [r["latest"] for r in records if r.get("latest")]
    if not dated:
        return None
    # Prefer the most common latest date, then average numeric fields.
    dates = [r["date"] for r in dated]
    best = max(set(dates), key=dates.count)
    subset = [r for r in dated if r["date"] == best]
    out = {"date": best}
    for key in ("ws10m", "wd10m", "t2m", "rh2m", "precip_mm"):
        vals = [r[key] for r in subset if r.get(key) is not None]
        out[key] = round(sum(vals) / len(vals), 2) if vals else None
    return out


def fetch_all_firms() -> tuple[list[dict], list[dict]]:
    detections = []
    source_stats = []
    for source in FIRMS_SOURCES:
        log(f"Fetching {source['product']}...")
        try:
            raw = fetch_bytes(source["url"])
            text = raw.decode("utf-8", errors="replace")
            rows = parse_firms_csv(text, source)
            source_stats.append(
                {
                    "id": source["id"],
                    "sensor": source["sensor"],
                    "product": source["product"],
                    "url": source["url"],
                    "bytes": len(raw),
                    "california_detections": len(rows),
                    "ok": True,
                    "note": "CSV contained a header only (no detection rows)." if len(rows) == 0 and "latitude" in text.lower() else None,
                }
            )
            detections.extend(rows)
            log(f"  {len(rows)} California detections")
        except Exception as exc:  # noqa: BLE001 — keep the build going if one sensor file fails
            source_stats.append(
                {
                    "id": source["id"],
                    "sensor": source["sensor"],
                    "product": source["product"],
                    "url": source["url"],
                    "bytes": 0,
                    "california_detections": 0,
                    "ok": False,
                    "note": str(exc),
                }
            )
            log(f"  FAILED: {exc}")
    return detections, source_stats


def harmonize(detections: list[dict]) -> tuple[list[dict], list[dict]]:
    """Bin detections to a 0.01° daily grid so MODIS and VIIRS can be compared."""
    buckets: dict[tuple[str, tuple[int, int]], list[dict]] = defaultdict(list)
    for det in detections:
        if not det["date"]:
            continue
        buckets[(det["date"], grid_cell(det["lat"], det["lon"]))].append(det)

    cells = []
    for (date, cell), items in buckets.items():
        lat, lon = cell_center(cell)
        modis = [d for d in items if d["sensor"] == "MODIS"]
        viirs = [d for d in items if d["sensor"] == "VIIRS"]
        frps = [d["frp"] for d in items]
        confs = [d["confidence"] for d in items if d["confidence"] is not None]
        cells.append(
            {
                "date": date,
                "cell": [cell[0], cell[1]],
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "n_raw": len(items),
                "n_modis": len(modis),
                "n_viirs": len(viirs),
                "has_modis": bool(modis),
                "has_viirs": bool(viirs),
                "both_sensors": bool(modis and viirs),
                "max_frp": round(max(frps), 2) if frps else 0.0,
                "sum_frp": round(sum(frps), 2) if frps else 0.0,
                "mean_confidence": round(sum(confs) / len(confs), 1) if confs else None,
                "satellites": sorted({d["satellite"] for d in items if d["satellite"]}),
                "sources": sorted({d["source_id"] for d in items}),
            }
        )
    cells.sort(key=lambda c: (c["date"], -c["max_frp"]))
    calendar = build_calendar(cells, detections)
    return cells, calendar


def build_calendar(cells: list[dict], detections: list[dict]) -> list[dict]:
    dates = sorted({c["date"] for c in cells} | {d["date"] for d in detections})
    rows = []
    for date in dates:
        day_cells = [c for c in cells if c["date"] == date]
        raw_modis = sum(1 for d in detections if d["date"] == date and d["sensor"] == "MODIS")
        raw_viirs = sum(1 for d in detections if d["date"] == date and d["sensor"] == "VIIRS")
        rows.append(
            {
                "date": date,
                "harmonized_cells": len(day_cells),
                "cells_modis": sum(1 for c in day_cells if c["has_modis"]),
                "cells_viirs": sum(1 for c in day_cells if c["has_viirs"]),
                "cells_both": sum(1 for c in day_cells if c["both_sensors"]),
                "raw_modis": raw_modis,
                "raw_viirs": raw_viirs,
                "sum_frp": round(sum(c["sum_frp"] for c in day_cells), 2),
                "max_frp": round(max((c["max_frp"] for c in day_cells), default=0.0), 2),
            }
        )
    return rows


def flatten_spans() -> list[dict]:
    out = []
    for corridor in CORRIDORS:
        for span in corridor["spans"]:
            item = dict(span)
            item["corridor_id"] = corridor["id"]
            item["corridor"] = corridor["name"]
            item["corridor_note"] = corridor["note"]
            item["mid"] = mid(span["a"], span["b"])
            out.append(item)
    return out


def score_spans(spans: list[dict], cells: list[dict], power_points: list[dict]) -> list[dict]:
    dates = sorted({c["date"] for c in cells})
    latest_date = dates[-1] if dates else None
    scored = []
    for span in spans:
        nearby = []
        for cell in cells:
            dist = point_segment_distance_km(cell["lat"], cell["lon"], span["a"], span["b"])
            if dist <= WATCH_KM:
                nearby.append({**cell, "distance_km": round(dist, 2)})
        last24 = [c for c in nearby if c["date"] == latest_date] if latest_date else []
        power = nearest_power(span["mid"], power_points)
        wind = power.get("latest") if power else None
        wind_bonus = 0.0
        wind_note = "No recent POWER wind value for this span."
        if wind and wind.get("ws10m") is not None:
            ws = wind["ws10m"]
            wind_note = f"Latest NASA POWER 10 m wind is {ws:.1f} m/s"
            if wind.get("date"):
                wind_note += f" on {format_power_date(wind['date'])}"
            wind_note += "."
            # Meteorological wind direction is the direction the wind comes FROM.
            if wind.get("wd10m") is not None and last24:
                alignments = []
                for cell in last24:
                    fire_to_span = bearing_deg(cell["lat"], cell["lon"], span["mid"][0], span["mid"][1])
                    wind_toward = (wind["wd10m"] + 180.0) % 360.0
                    alignments.append(angle_diff(wind_toward, fire_to_span))
                if alignments and min(alignments) <= 45:
                    wind_bonus = min(2.0, ws / 4.0)
                    wind_note += " Wind is aligned toward the span from at least one nearby hotspot."
            elif ws >= 7:
                wind_bonus = 0.5
        score = (
            2.0 * len(nearby)
            + 3.0 * len(last24)
            + 1.2 * math.log1p(sum(c["sum_frp"] for c in nearby))
            + wind_bonus
        )
        if score >= 12 or len(last24) >= 3:
            priority = "Watch"
        elif score >= 4 or nearby:
            priority = "Monitor"
        else:
            priority = "Stand down"
        scored.append(
            {
                "id": span["id"],
                "name": span["name"],
                "corridor": span["corridor"],
                "corridor_note": span["corridor_note"],
                "a": span["a"],
                "b": span["b"],
                "mid": [round(span["mid"][0], 5), round(span["mid"][1], 5)],
                "nearby_cells": len(nearby),
                "nearby_last_day": len(last24),
                "sum_frp": round(sum(c["sum_frp"] for c in nearby), 2),
                "max_frp": round(max((c["max_frp"] for c in nearby), default=0.0), 2),
                "nearest_km": round(min((c["distance_km"] for c in nearby), default=99.0), 2) if nearby else None,
                "score": round(score, 2),
                "priority": priority,
                "wind": wind,
                "wind_note": wind_note,
                "nearby": sorted(nearby, key=lambda c: (c["distance_km"], -c["max_frp"]))[:25],
            }
        )
    scored.sort(key=lambda s: (-s["score"], s["name"]))
    return scored


def nearest_power(midpt: list[float], power_points: list[dict]) -> dict | None:
    if not power_points:
        return None
    return min(power_points, key=lambda p: haversine_km(midpt[0], midpt[1], p["lat"], p["lon"]))


def format_power_date(yyyymmdd: str) -> str:
    try:
        return datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return yyyymmdd


def fetch_power(spans: list[dict]) -> list[dict]:
    # One POWER request per corridor midpoint, not per span.
    seen = []
    points = []
    end = now_pt().strftime("%Y%m%d")
    start_dt = now_pt().replace(day=1)
    start = start_dt.strftime("%Y%m%d")
    for span in spans:
        key = (round(span["mid"][0], 1), round(span["mid"][1], 1))
        if key in seen:
            continue
        seen.append(key)
        lat, lon = span["mid"]
        log(f"Fetching NASA POWER for {lat:.3f}, {lon:.3f}...")
        try:
            points.append(fetch_power_point(lat, lon, start, end))
        except Exception as exc:  # noqa: BLE001
            log(f"  FAILED: {exc}")
            points.append({"lat": lat, "lon": lon, "url": None, "latest": None, "series": {}, "note": str(exc)})
    return points


def summarize(detections: list[dict], cells: list[dict], calendar: list[dict], spans: list[dict], sources: list[dict]) -> dict:
    dates = [c["date"] for c in calendar]
    return {
        "california_bbox": [CA_WEST, CA_SOUTH, CA_EAST, CA_NORTH],
        "grid_deg": GRID_DEG,
        "watch_km": WATCH_KM,
        "raw_detections": len(detections),
        "raw_modis": sum(1 for d in detections if d["sensor"] == "MODIS"),
        "raw_viirs": sum(1 for d in detections if d["sensor"] == "VIIRS"),
        "harmonized_cells": len(cells),
        "cells_both_sensors": sum(1 for c in cells if c["both_sensors"]),
        "date_start": dates[0] if dates else None,
        "date_end": dates[-1] if dates else None,
        "watch_spans": sum(1 for s in spans if s["priority"] == "Watch"),
        "monitor_spans": sum(1 for s in spans if s["priority"] == "Monitor"),
        "sources_ok": sum(1 for s in sources if s["ok"]),
        "sources_attempted": len(sources),
    }


def build_payload() -> dict:
    detections, source_stats = fetch_all_firms()
    cells, calendar = harmonize(detections)
    spans = flatten_spans()
    power_points = fetch_power(spans)
    scored = score_spans(spans, cells, power_points)
    generated = now_pt()
    payload = {
        "project": "Kestrel Grid Sentinel",
        "challenge": {
            "name": "Harmonization of MODIS and VIIRS Hot Spots",
            "url": "https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/",
        },
        "generated_at": generated.isoformat(),
        "generated_at_label": generated.strftime("%B %-d, %Y, %-I:%M %p PT"),
        "timezone": "America/Los_Angeles",
        "disclaimer": (
            "Hackathon prototype only. Corridor waypoints are geographic sketches, not official utility GIS. "
            "Kestrel is at TRL 4 and is not claimed to be deployed for fire response. "
            "A 5 November 2026 attempt to land on a de-energized line struck the line rather than landing."
        ),
        "method": {
            "title": "How the two sensor records are harmonized",
            "text": (
                "MODIS active-fire pixels are nominally 1 km; VIIRS pixels are 375 m, so a single fire often "
                "produces several VIIRS detections and one MODIS detection. Raw counts cannot be compared "
                "directly. This prototype bins every NASA FIRMS detection in California onto a 0.01° "
                "(about 1 km) daily grid, close to the MODIS scale. Each occupied cell is one harmonized "
                "hotspot, tagged with whether MODIS, VIIRS, or both sensors saw it, plus Fire Radiative Power. "
                "The burning-activity calendar counts unique cells, not raw pixels. This is a spatial-temporal "
                "harmonization for comparison, not a full radiometric intercalibration. The public FIRMS files "
                "used here cover about seven days; a FIRMS MAP_KEY would extend the same method over the archive."
            ),
        },
        "datasets": [
            {
                "name": "NASA FIRMS MODIS Collection 6.1 and VIIRS 375 m active fire / hotspots",
                "urls": [
                    "https://www.earthdata.nasa.gov/data/tools/firms",
                    "https://firms.modaps.eosdis.nasa.gov/",
                ],
            },
            {
                "name": "NASA POWER daily meteorology (10 m wind speed and direction, 2 m temperature and humidity, precipitation)",
                "urls": [
                    "https://power.larc.nasa.gov/",
                    "https://power.larc.nasa.gov/docs/services/api/",
                ],
            },
        ],
        "summary": summarize(detections, cells, calendar, scored, source_stats),
        "sources": source_stats,
        "calendar": calendar,
        "cells": cells,
        "spans": scored,
        "corridors": [
            {
                "id": c["id"],
                "name": c["name"],
                "note": c["note"],
                "path": [pt for span in c["spans"] for pt in (span["a"], span["b"])],
            }
            for c in CORRIDORS
        ],
        "power": {
            "fill_value": -999,
            "points": [
                {
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "latest": p.get("latest"),
                    "series": p.get("series", {}),
                    "note": p.get("note"),
                }
                for p in power_points
            ],
            "corridor_average": latest_power(power_points),
        },
        "detections_sample": sorted(detections, key=lambda d: d["frp"], reverse=True)[:400],
        "detection_count_by_source": {
            s["id"]: s["california_detections"] for s in source_stats
        },
    }
    return payload


def render_html(payload: dict) -> str:
    template = TEMPLATE.read_text()
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if "__DATA__" not in template:
        raise RuntimeError("template.html is missing the __DATA__ placeholder")
    return template.replace("__DATA__", blob)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log("Building Kestrel Grid Sentinel dashboard...")
    try:
        payload = build_payload()
    except Exception as exc:  # noqa: BLE001
        if OUT_JSON.exists():
            log(f"Live fetch failed ({exc}); keeping existing {OUT_JSON}")
            payload = json.loads(OUT_JSON.read_text())
        else:
            log(f"Live fetch failed and no cache is available: {exc}")
            return 1
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    OUT_HTML.write_text(render_html(payload))
    s = payload["summary"]
    log(
        f"Wrote {OUT_HTML} and {OUT_JSON}: "
        f"{s['raw_detections']} raw detections, "
        f"{s['harmonized_cells']} harmonized cells, "
        f"{s['watch_spans']} watch spans."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

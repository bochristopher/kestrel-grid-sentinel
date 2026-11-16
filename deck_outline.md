# Kestrel Grid Sentinel — 7-slide outline

For a 7-slide Space Apps demo deck (title slide included). This is an outline only; the slides themselves have not been built or uploaded.

Every factual claim has a source. Prototype counts are from the live NASA pull at **5:15 PM PT on November 15, 2026** and will change if the prototype is rebuilt. Do not present Kestrel as operational for fire response.

Suggested visual style: dark field, amber highlights, a California corridor map, and the burning-activity calendar. Open `index.html` for screenshots of the map and calendar.

---

## Slide 1 — Title

**Title:** Kestrel Grid Sentinel

**Subtitle:** Harmonized NASA fire data, watching the grid from the line

**Bullets:**

- A Space Apps 2026 entry for Harmonization of MODIS and VIIRS Hot Spots
- Chargebotic · product: Kestrel, a line-perching, self-charging drone
- Mountain View local event · projects due November 15, 2026, 11:59 PM PT

**Sources:**

- Challenge name and URL: https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- Product name and role: Chargebotic Kestrel one-pager for NEETRAC, October 2026
- Deadline: official Space Apps 2026 Mountain View / event materials (projects due 15 Nov 2026, 11:59 PM PT)

---

## Slide 2 — The records do not compare

**Title:** Two fire satellites, two disagreeing counts

**Bullets:**

- MODIS (Terra/Aqua) has a long hotspot record at a nominal 1 km fire-pixel scale; VIIRS (NOAA-20 and NOAA-21) continues it at 375 m
- A single fire often yields several VIIRS pixels and one MODIS pixel, so raw counts mislead a fire manager
- In California, 8–15 November 2026, FIRMS reported 175 MODIS detections and 2,546 VIIRS detections — more than a 14-to-1 raw gap
- The challenge: turn those records into one burning-activity calendar

**Sources:**

- Sensor roles, archive length, and the need for harmonization: official challenge text, Harmonization of MODIS and VIIRS Hot Spots, https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- Nominal resolutions (MODIS ~1 km, VIIRS 375 m): same challenge text; FIRMS product descriptions at https://www.earthdata.nasa.gov/data/tools/firms and https://firms.modaps.eosdis.nasa.gov/
- California counts, 8–15 Nov 2026: live FIRMS 7-day CSVs ingested by `build.py` at 5:15 PM PT, 15 Nov 2026 (see `data/latest.json`)

---

## Slide 3 — The idea

**Title:** A calendar for fire managers, a watch list for the line

**Bullets:**

- Harmonize MODIS and VIIRS hotspots, then show a daily burning-activity calendar for California
- Overlay those cells on sketch corridors and rank spans as Watch, Monitor, or Stand down
- Add NASA POWER 10 m wind, temperature, humidity, and precipitation for spread and flight context
- Use the ranking to task Kestrel, a drone that perches on a line and charges from it, to the spans that most need persistent eyes

**Sources:**

- Calendar and target audiences (emergency responders, scientists, land managers): official challenge text, link above
- NASA POWER variables (WS10M, WD10M, T2M, RH2M, PRECTOTCORR): https://power.larc.nasa.gov/docs/services/api/
- Kestrel function (perch, clamp a split-core CT, harvest by induction, no galvanic connection): Chargebotic Kestrel one-pager, October 2026

---

## Slide 4 — How we harmonize NASA data

**Title:** One grid, so the sensor of origin no longer drives the count

**Bullets:**

- Clip public FIRMS 7-day CSVs to California and bin every detection to a 0.01° (about 1 km) daily cell
- Count unique cells, not raw pixels; tag each cell as MODIS, VIIRS, or both, and keep Fire Radiative Power
- This is a spatial-temporal harmonization for comparison, not a full radiometric intercalibration of the two sensors
- The same method extends to the 20-year archive once a FIRMS MAP_KEY is added

**Sources:**

- Method: `build.py` in this folder; also summarized on the prototype dashboard
- FIRMS public 7-day CSVs (verified HTTP 200 on 15 Nov 2026):
  - https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_USA_contiguous_and_Hawaii_7d.csv
  - https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv
  - https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv
- Challenge request to harmonize so that “the sensor of origin no longer matters”: official challenge text
- Archive length and MAP_KEY access: https://firms.modaps.eosdis.nasa.gov/download/ and https://firms.modaps.eosdis.nasa.gov/api/

---

## Slide 5 — What the prototype shows tonight

**Title:** California, 8–15 November 2026

**Bullets:**

- 2,721 raw FIRMS detections became 1,285 harmonized daily cells; only 78 cells were seen by both sensors
- Burning activity peaked on 10–12 November; 10 November had the window’s highest FRP (maximum 639 MW)
- Six of nine demo spans ranked Watch; the Oroville–Paradise foothills span scored highest
- Latest NASA POWER corridor average, 12 November (daily fields lag): 2.7 m/s wind, 16 °C, 48% RH, 0.7 mm precipitation

**Sources:**

- All figures: `data/latest.json` and `index.html`, built 5:15 PM PT, 15 Nov 2026, from the verified FIRMS and POWER URLs above
- POWER fill value and lag: NASA POWER API returned -999 for 13–15 November at these points; those values were treated as missing, https://power.larc.nasa.gov/docs/services/api/
- Demo spans are geographic sketches, not official utility GIS: stated in the dashboard disclaimer and `build.py`

**Visual:** Screenshot the calendar table and the Leaflet map from `index.html`. Caption: prototype only; corridors are sketches.

---

## Slide 6 — Why a line-perching drone

**Title:** Kestrel is the persistent watcher — at TRL 4, not a deployed asset

**Bullets:**

- Kestrel lands on a power line and harvests energy by induction so it can stay on station instead of flying home to swap batteries
- Verified so far: bench harvest of 13.7–187 W (10 Oct 2026, 64–832 A-turns, 77–92% efficiency); about 17–18 W on a ~100 A line at JIFX, August 2026
- A 5 November 2026 attempt to land on a de-energized line struck the line rather than landing; flights today are piloted; the system is at TRL 4
- Chargebotic has an $80,000 paid pilot with Chariot, of which $40,000 has been received — not a claim of field fire-response use

**Sources:**

- Function, bench table, efficiency, JIFX result, piloted status: Chargebotic Kestrel one-pager for NEETRAC, October 2026, and *Kestrel Energized-Line Test Specs*, October 2026
- TRL 4 and 5 November landing attempt: Bo Redfearn, 6 November 2026
- Chariot pilot amount and $40,000 received: Chargebotic confirmed figures (shared team memory; $40,000 received is the only revenue that should be claimed)

---

## Slide 7 — Impact, limits, and next steps

**Title:** A consistent fire calendar, with a path to a longer watch

**Bullets:**

- Immediate use: responders and land managers get one comparable hotspot calendar, plus a short list of line spans worth watching
- Limits: seven days of public FIRMS data, not the full archive; sketch corridors, not official GIS; simple wind rules, not a fire-spread model
- Next: extend the same grid over the FIRMS archive with a MAP_KEY, and replace sketch corridors with a utility-provided line layer
- Kestrel remains TRL 4 until landing and energized-line perching are actually demonstrated — this entry does not claim those results

**Sources:**

- Intended audiences: official challenge text
- Data-window and corridor limits: prototype README and dashboard disclaimer
- Archive next step: https://firms.modaps.eosdis.nasa.gov/api/ and https://firms.modaps.eosdis.nasa.gov/download/
- TRL and undemonstrated landing: Bo Redfearn, 6 November 2026, and the 5 November 2026 de-energized-line attempt

**Closing line:** NASA data tells us where the fire is. A perched Kestrel would be how we keep watching the line. Not yet.

---

## Notes for whoever builds the slides

- Use the product name **Kestrel** only. Do not use Magline.
- Keep the 7-slide cap and stay in English.
- If a demo video is chosen instead of a deck, it must be 30 seconds or less; this outline is for the 7-slide option.
- Screenshot `index.html` after a fresh `python3 build.py` if time allows, and update Slide 5 numbers to match.

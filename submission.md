# Space Apps 2026 submission draft — Kestrel Grid Sentinel

Local draft only. Nothing in this file has been posted or submitted.

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots
**Challenge URL:** https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/

Copy the fields below into the official project form after review. Prototype numbers are from a live NASA data pull at 5:15 PM PT on November 15, 2026, and will change if `build.py` is run again.

---

## Project Name

Kestrel Grid Sentinel

---

## High-Level Summary

(99 words)

Kestrel Grid Sentinel is a web prototype that turns NASA FIRMS MODIS and VIIRS active-fire records into one daily burning-activity calendar for California, then ranks transmission-corridor spans for watch. VIIRS pixels are 375 m and MODIS pixels are about 1 km, so raw counts cannot be compared; the tool bins both sensors to a 0.01° daily grid. NASA POWER wind and weather supply spread and flight context. The ranking is meant to task Chargebotic's line-perching drone, Kestrel, to the spans that most need persistent eyes. Kestrel is at TRL 4 and is not claimed to be in fire-response service.

---

## Detailed Description

### What it does

Satellites have tracked active-fire hotspots for more than two decades, but the record is split across sensors that cannot be compared directly. MODIS, on Terra and Aqua, provides a long archive at a nominal 1 km fire-pixel scale. VIIRS, now flying on NOAA-20 and NOAA-21, continues that record at 375 m, so a single fire often produces several VIIRS detections and one MODIS detection. The 2026 Space Apps challenge asks for a web application that harmonizes those records into a burning-activity calendar.

Kestrel Grid Sentinel does that for California and then takes one further step that matters to grid operators. It:

1. Downloads the public NASA FIRMS 7-day active-fire CSVs for MODIS Collection 6.1 and for VIIRS on Suomi NPP, NOAA-20, and NOAA-21.
2. Clips detections to California and bins every pixel to a 0.01° (about 1 km) daily grid, close to the MODIS scale.
3. Treats each occupied grid cell as one harmonized hotspot, tagged with whether MODIS, VIIRS, or both sensors saw it, plus Fire Radiative Power (FRP).
4. Builds a burning-activity calendar that counts unique cells, not raw pixels, and still shows the raw MODIS and VIIRS counts so the bias is visible.
5. Pulls NASA POWER daily 10 m wind, 2 m temperature and humidity, and precipitation at sample points along a set of California transmission corridors.
6. Ranks each demo corridor span by nearby harmonized cells, FRP, and wind, and labels it Watch, Monitor, or Stand down.

In the 5:15 PM PT build on November 15, 2026, the tool ingested 2,721 California FIRMS detections from 8–15 November (175 MODIS and 2,546 VIIRS) and collapsed them to 1,285 harmonized daily cells, including 78 cells seen by both sensors. Raw VIIRS counts were much higher than raw MODIS counts on every day, which is exactly why a pixel-for-pixel comparison would mislead a fire manager. Activity peaked on 10–12 November; 10 November had the highest daily FRP in the window (maximum 639 MW). The Suomi NPP VIIRS 7-day file returned a header and no detection rows, so VIIRS continuity in this run comes from NOAA-20 (1,262 California detections) and NOAA-21 (1,284). NASA POWER daily fields lagged a few days; the latest non-fill corridor average was for 12 November, with a 10 m wind of 2.7 m/s, 16.1 °C, 48% relative humidity, and 0.7 mm of precipitation. Six of nine demo spans were ranked Watch, with the Oroville–Paradise foothills span highest. No demo span had a new nearby cell on 15 November itself; the Watch labels reflect the seven-day window, not an active fire on the line that day.

The map and calendar are a decision-support sketch, not an operational dispatch system. Corridor waypoints are geographic sketches for the demo, not official utility GIS.

### Benefits

Early-warning and emergency responders, land managers, and utility operators get a consistent calendar of burning activity instead of two disagreeing satellite counts. They can see which days were unusual, compare MODIS-only, VIIRS-only, and combined cells, and scan a short list of line spans that warrant persistent eyes. Pairing the calendar with NASA POWER wind adds simple spread and weather context without claiming a full fire-behavior model.

### Tools used

- Python 3 standard library (`build.py`) to fetch, harmonize, and score the data
- HTML, CSS, and JavaScript, with Leaflet and OpenStreetMap tiles, for the dashboard (`index.html`)
- NASA FIRMS public 7-day CSVs (no MAP_KEY required for this prototype)
- NASA POWER Web Services daily point API
- A 0.01° daily-grid harmonization, documented in the dashboard, not a full radiometric intercalibration of MODIS and VIIRS

### Intended impact, and honest limits

The intended users are the audiences named in the challenge — early-warning and emergency responders, scientists, land managers, and firefighters — plus transmission operators who have to decide where to watch a corridor when fire weather is elevated. The longer-term idea is that a drone that can perch on a line and charge from it, Chargebotic's Kestrel, could be tasked to the highest-ranked spans and stay there, instead of flying out and back on a battery.

That idea is a concept of operations, not a field result. Kestrel is a drone that lands on a power line, clamps a split-core current transformer around the conductor, and harvests energy by induction, with no galvanic connection to the line. Intended uses are defense and utility inspection and persistent surveillance. It is at technology readiness level 4. Flights today are piloted. A bench loop test on 10 October 2026 measured harvested power from 13.7 W at 64 A-turns up to a peak of 187 W at 832 A-turns, with efficiency of 77–92% across that range. A JIFX field test in August 2026 measured about 17–18 W on a line carrying about 100 A. A 5 November 2026 attempt to land on a de-energized line struck the line rather than landing. Chargebotic has an $80,000 paid pilot with Chariot, of which $40,000 has been received. This project does not claim that Kestrel has perched on an energized line in the field, that it is deployed for wildfire response, or that the span ranking should be used for operational dispatch.

The public FIRMS files used here cover about seven days, not the full MODIS and VIIRS archive. The same grid method would extend over the historical record with a FIRMS MAP_KEY, which is the natural next step toward the multi-year calendar the challenge describes.

---

## NASA Data and Resources

1. **NASA FIRMS (Fire Information for Resource Management System) — MODIS Collection 6.1 and VIIRS 375 m active fire / hotspots**
   - Earthdata FIRMS: https://www.earthdata.nasa.gov/data/tools/firms
   - FIRMS home: https://firms.modaps.eosdis.nasa.gov/
   - FIRMS API documentation: https://firms.modaps.eosdis.nasa.gov/api/
   - MODIS C6.1 USA 7-day CSV (verified HTTP 200 on 15 Nov 2026): https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_USA_contiguous_and_Hawaii_7d.csv
   - VIIRS NOAA-20 C2 USA 7-day CSV (verified HTTP 200): https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv
   - VIIRS NOAA-21 C2 USA 7-day CSV (verified HTTP 200): https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv
   - VIIRS Suomi NPP C2 USA 7-day CSV (verified HTTP 200; header only, no detection rows in this run): https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_USA_contiguous_and_Hawaii_7d.csv

2. **NASA POWER (Prediction Of Worldwide Energy Resources) — daily meteorology**
   - POWER home: https://power.larc.nasa.gov/
   - POWER API documentation (verified HTTP 200): https://power.larc.nasa.gov/docs/services/api/
   - Daily point API, parameters WS10M, WD10M, T2M, RH2M, PRECTOTCORR, community RE (verified HTTP 200 and valid JSON on 15 Nov 2026)

These are the datasets used in the prototype. FIRMS is also the NASA data resource named on the official challenge page.

---

## Space Agency Partner Data

None used.

The challenge page credits the National Commission on Space Activities of Argentina (CONAE) for a photograph. That image was not used in this project, and no CONAE or other space-agency-partner dataset was ingested.

---

## References

- NASA Space Apps Challenge 2026, Harmonization of MODIS and VIIRS Hot Spots: https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- NASA Earthdata, Fire Information for Resource Management System (FIRMS): https://www.earthdata.nasa.gov/data/tools/firms
- NASA LANCE FIRMS: https://firms.modaps.eosdis.nasa.gov/
- NASA Langley Research Center, POWER Project and API: https://power.larc.nasa.gov/ and https://power.larc.nasa.gov/docs/services/api/
- Challenge text on sensor differences: MODIS on Terra and Aqua provides more than two decades of observations and is being replaced by VIIRS; the records cannot be compared directly without harmonization because of different spatial resolutions, sensitivities, and observation schedules.
- Chargebotic, *Kestrel* one-pager prepared for NEETRAC, October 2026: product description; bench loop test of 10 October 2026 (13.7 W at 64 A-turns to 187 W peak at 832 A-turns, 77–92% efficiency); JIFX field test, August 2026 (about 17–18 W on a line carrying about 100 A); 7 kV hipot held for 1 minute; piloted flight status.
- Bo Redfearn, 6 November 2026: Kestrel is at TRL 4; a 5 November 2026 de-energized-line landing attempt struck the line rather than landing successfully.
- Chargebotic paid pilot with Chariot: $80,000 total, $40,000 received.

---

## AI-use disclosure

AI tools helped write the submission text, the prototype code, and the slide outline. A person on the team chose the challenge, set the product facts that could be claimed, and must review every field before any official submission. Live hotspot counts and weather values in the dashboard come from NASA FIRMS and NASA POWER, not from a model. The 0.01° daily-grid method and the span-ranking rules are simple, documented heuristics, not a trained fire-spread or landing model. No generated imagery is presented as a photograph of a test or a NASA scene.

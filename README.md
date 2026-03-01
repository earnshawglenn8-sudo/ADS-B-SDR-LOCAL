# ADS-B SDR Local

Local ADS‑B integration for Home Assistant using **readsb** / **dump1090** (aircraft.json).

## What you get
- Sensors:
  - Aircraft count (filtered)
  - Nearest aircraft distance (km)
  - Nearest callsign/hex
  - Lowest altitude (ft)
- **Map support** via Home Assistant **geo_location** entities (each aircraft appears on the HA Map)
- **Military filter (heuristic)**:
  - Toggle “Military only”
  - Optional callsign prefixes / regex / hex prefixes

> Note: “military” identification is best‑effort only. ADS‑B data doesn’t reliably label “military”, so this uses callsign/prefix/hex heuristics.

## Default endpoint
`http://<receiver_ip>:8080/data/aircraft.json`

## Install via HACS
Add this repository as a Custom Repository (Integration):
`https://github.com/earnshawglenn8-sudo/ADS-B-SDR-LOCAL`

## Setup
Settings → Devices & Services → Add Integration → **ADS-B SDR Local**

After adding, open the integration **Options** to set:
- Home lat/lon (for distance filtering and “nearest”)
- Max range (km)
- Minimum altitude (ft)
- Military only toggle + filters

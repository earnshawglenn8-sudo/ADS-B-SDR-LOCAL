# ADS-B SDR Local

Local ADS-B integration for Home Assistant that reads `aircraft.json` from **tar1090/readsb/dump1090**.

## Features
- Sensors:
  - **ADS-B Aircraft Count** (all aircraft in feed)
  - **ADS-B Aircraft Count (Filtered)** (filtered when Military Only is ON)
- Toggle:
  - **ADS-B Military Only** switch (filters by callsign prefixes)
- Map:
  - Aircraft with `lat`/`lon` are exposed as **geo_location** entities and show on the HA Map.

## Endpoint (your setup)
For tar1090 on `http://192.168.1.188/tar1090/` the JSON endpoint is:
`http://192.168.1.188/tar1090/data/aircraft.json`

## Setup
Settings → Devices & Services → Add Integration → **ADS-B SDR Local**

Default is **ALL aircraft**. Turn **ADS-B Military Only** ON to filter.

> Military detection is best-effort (ADS-B Exchange does not reliably flag military).

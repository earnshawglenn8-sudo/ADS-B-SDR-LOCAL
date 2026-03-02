# ADS-B SDR Local

tar1090/readsb `aircraft.json` integration for Home Assistant.

## Features
- Sensors:
  - ADS-B Aircraft Count
  - ADS-B Aircraft Count (Filtered)
- Switch:
  - ADS-B Military Only (filters by callsign prefix)
- Map:
  - Aircraft as **device_tracker** entities (airplane icon on the HA map)

## tar1090 endpoint example
`http://192.168.1.188/tar1090/data/aircraft.json`

Default behavior:
- **All aircraft** shown.
- Turn **Military Only** ON to show only military callsigns (best-effort).

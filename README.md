# ADS-B SDR Local (Local + OpenSky)

Home Assistant integration for ADS-B aircraft tracking.

## Sources
- **Local (tar1090/readsb/dump1090)**: `aircraft.json` on your LAN
- **Worldwide (OpenSky Network)**: `states/all` (rate-limited; can optionally use a bounding box)

## Entities
- Sensors:
  - ADS-B Aircraft Count
  - ADS-B Aircraft Count (Filtered)
- Switches:
  - ADS-B Military Only
  - ADS-B Use Worldwide (OpenSky)

## Notes
OpenSky is rate-limited. To avoid pulling huge datasets, set **Home lat/lon** and a **Max range (km)** in the integration config.
If range is 0, it will request global data (not recommended).

Local endpoint example (your setup):
`http://192.168.1.188/tar1090/data/aircraft.json`

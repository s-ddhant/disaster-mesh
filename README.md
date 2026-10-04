# Disaster Mesh

AI-assisted disaster-resilient mesh network: victim phone -> 16-byte frame -> gateway (rescue center).

- `protocol/` frame encoder/decoder, codebooks, CRC-16, triage rule, reconstruction template
- `gateway/` laptop rescue center (FastAPI): receives frames, drops duplicates, RED-first dashboard, GeoJSON
- `phone/` victim app (web page served by the gateway), packs the frame in JavaScript
- `tests/` round-trip, bit-flip, triage, dedup/ordering, and JS == Python byte-for-byte

Wire spec: `E:\AgentContext\disaster-mesh-wire-spec.md`

## Setup (once)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python gateway\make_cert.py      # HTTPS certificate, needed for phone GPS
```

## Run the tests

```powershell
python -m pytest -q
```

## Demo

1. Laptop: Settings -> Network & internet -> Mobile hotspot -> On. Note the network name and password.
2. Double-click `run-gateway.cmd` (allow Python through the Windows firewall on **private** networks when asked).
3. Laptop browser: `https://localhost:8443/dashboard` -> Advanced -> Proceed.
4. Each phone: join the hotspot, open Chrome at `https://192.168.137.1:8443` -> Advanced -> Proceed -> allow location.
5. Pick the options, press SEND SOS. The report appears on the dashboard, RED first.

If GPS is refused, the page falls back to an editable demo location.

## Endpoints

| Path | What |
|---|---|
| `POST /frame` | 16 raw bytes in; 400 if damaged |
| `GET /messages` | decoded queue, RED first then oldest |
| `GET /victims.geojson` | map points for God's Eye View |
| `GET /codebook` | dropdown lists for the phone |
| `GET /dashboard` | rescue-center screen |
| `GET /` | phone app |

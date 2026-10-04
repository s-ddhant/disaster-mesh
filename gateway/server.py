"""FastAPI server: receives frames from the phones, decodes them, serves the dashboard and victims.geojson.

Run from the project folder (see README):
    uvicorn gateway.server:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from gateway.store import Store
from protocol import codebook as cb
from protocol.codebook import INJURY, PRIORITY
from protocol.describe import describe
from protocol.frame import FrameError, decode

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="Disaster Mesh Gateway")
store = Store()

# Lets God's Eye View (another port) read victims.geojson from the browser.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


@app.post("/frame")
async def receive_frame(request: Request):
    """A phone sends exactly 16 raw bytes. Nothing else crosses the 'radio'."""
    frame = await request.body()
    try:
        fields = decode(frame)
    except FrameError as e:
        raise HTTPException(status_code=400, detail=str(e))
    accepted = store.add(fields, frame)
    return {"accepted": accepted, "duplicate": not accepted, "bytes": len(frame)}


@app.get("/codebook")
def codebook():
    """The phone builds its dropdowns from this, so the lists live only in protocol/codebook.py."""
    return {
        "injury": [label for label, _ in cb.INJURY],
        "injury_priority": [priority for _, priority in cb.INJURY],
        "priority": cb.PRIORITY,
        "mobility": cb.MOBILITY,
        "people": cb.PEOPLE,
        "hazard": cb.HAZARD,
        "needs": cb.NEEDS,
    }


@app.get("/messages")
def messages():
    return [{**m, "priority_label": PRIORITY[m["priority"]], "brief": describe(m)}
            for m in store.queue()]


@app.get("/victims.geojson")
def victims_geojson():
    """One map point per message, for God's Eye View or any map tool."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [m["lon"], m["lat"]]},
                "properties": {
                    "priority": PRIORITY[m["priority"]],
                    "injury": INJURY[m["injury"]][0],
                    "brief": describe(m),
                    "device": m["device"],
                },
            }
            for m in store.queue()
        ],
    }


@app.get("/dashboard")
def dashboard():
    return FileResponse(ROOT / "gateway" / "dashboard.html")


# The phone app is served last so the routes above take precedence.
app.mount("/", StaticFiles(directory=ROOT / "phone", html=True), name="phone")

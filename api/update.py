"""Downloads the FlixBus GTFS feed, turns it into the map's data.json and stores it in Vercel Blob.

Runs as a script during the Vercel build, and as POST /api/update behind the page's Update button.
Without BLOB_READ_WRITE_TOKEN (local development) it writes public/data.json instead.
"""
import csv
import io
import json
import os
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

FEED = "https://gtfs.gis.flix.tech/gtfs_generic_eu.zip"
BLOB_API = "https://vercel.com/api/blob/?pathname=data.json"


def rows(zf, name):
    return csv.DictReader(io.TextIOWrapper(zf.open(name), encoding="utf-8-sig"))


def build():
    with urllib.request.urlopen(FEED) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))
    stops = {r["stop_id"]: r for r in rows(zf, "stops.txt")}
    route_of = {r["trip_id"]: r["route_id"] for r in rows(zf, "trips.txt")}
    trips = defaultdict(list)
    for r in rows(zf, "stop_times.txt"):
        trips[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"]))
    routes = defaultdict(set)  # route_id -> set of (stop_a, stop_b) segments
    for trip_id, seq in trips.items():
        ids = [stop_id for _, stop_id in sorted(seq)]
        for a, b in zip(ids, ids[1:]):
            if a != b:
                routes[route_of[trip_id]].add((min(a, b), max(a, b)))
    used = sorted({s for edges in routes.values() for edge in edges for s in edge})
    index = {s: i for i, s in enumerate(used)}
    return {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stops": [[round(float(stops[s]["stop_lon"]), 4), round(float(stops[s]["stop_lat"]), 4), stops[s]["stop_code"]] for s in used],
        "routes": [sorted([index[a], index[b]] for a, b in edges) for _, edges in sorted(routes.items())],
    }


def store(data):
    body = json.dumps(data, separators=(",", ":")).encode()
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        open("public/data.json", "wb").write(body)
        return body
    headers = {
        "authorization": f"Bearer {token}",
        "x-api-version": "12",
        "x-content-type": "application/json",
        "x-add-random-suffix": "0",
        "x-allow-overwrite": "1",
        "x-cache-control-max-age": "60",  # the minimum
    }
    urllib.request.urlopen(urllib.request.Request(BLOB_API, data=body, method="PUT", headers=headers)).close()
    return body


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = store(build())
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    store(build())

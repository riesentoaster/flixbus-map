"""Download the FlixBus GTFS feed and write public/data.json for the map."""
import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

URL = "https://gtfs.gis.flix.tech/gtfs_generic_eu.zip"


def rows(zf, name):
    return csv.DictReader(io.TextIOWrapper(zf.open(name), encoding="utf-8-sig"))


with urllib.request.urlopen(URL) as resp:
    zf = zipfile.ZipFile(io.BytesIO(resp.read()))

stops = {r["stop_id"]: (float(r["stop_lon"]), float(r["stop_lat"])) for r in rows(zf, "stops.txt")}
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
data = {
    "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "stops": [[round(stops[s][0], 4), round(stops[s][1], 4)] for s in used],
    "routes": [sorted([index[a], index[b]] for a, b in edges) for _, edges in sorted(routes.items())],
}
with open("public/data.json", "w") as f:
    json.dump(data, f, separators=(",", ":"))
print(f"{len(used)} stops, {len(routes)} routes")

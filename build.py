"""Download the FlixBus GTFS feed and write public/data.json for the map."""
import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict

URL = "https://gtfs.gis.flix.tech/gtfs_generic_eu.zip"


def rows(zf, name):
    return csv.DictReader(io.TextIOWrapper(zf.open(name), encoding="utf-8-sig"))


with urllib.request.urlopen(URL) as resp:
    zf = zipfile.ZipFile(io.BytesIO(resp.read()))

stops = {r["stop_id"]: (float(r["stop_lon"]), float(r["stop_lat"])) for r in rows(zf, "stops.txt")}

trips = defaultdict(list)
for r in rows(zf, "stop_times.txt"):
    trips[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"]))

edges = set()
for seq in trips.values():
    ids = [stop_id for _, stop_id in sorted(seq)]
    for a, b in zip(ids, ids[1:]):
        if a != b:
            edges.add((min(a, b), max(a, b)))

used = sorted({s for edge in edges for s in edge})
index = {s: i for i, s in enumerate(used)}
data = {
    "stops": [[round(stops[s][0], 4), round(stops[s][1], 4)] for s in used],
    "edges": sorted([index[a], index[b]] for a, b in edges),
}
with open("public/data.json", "w") as f:
    json.dump(data, f, separators=(",", ":"))
print(f"{len(used)} stops, {len(edges)} edges")

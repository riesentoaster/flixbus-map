# FlixBus Route Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A single static web page that draws every FlixBus stop and every stop-to-stop segment from the European GTFS feed on a Leaflet map, rebuilt on each Vercel deploy and once a day.

**Architecture:** A standard-library Python script downloads the GTFS zip at build time and emits one small JSON file. A single HTML file loads Leaflet from a CDN and draws that JSON. A Vercel cron job calls a tiny serverless function that POSTs to a deploy hook, which triggers a rebuild.

**Tech Stack:** Python 3 (stdlib only), Leaflet 1.9.4, OpenStreetMap tiles, Vercel (Hobby tier) static hosting + Python serverless function + cron.

**Spec:** `docs/superpowers/specs/2026-09-07-flixbus-map-design.md`

## Global Constraints

- No dependencies beyond the Python standard library and Leaflet from cdnjs. No npm, no bundler, no test framework.
- Feed URL: `https://gtfs.gis.flix.tech/gtfs_generic_eu.zip`
- Output data format: `{"stops": [[lon, lat], ...], "edges": [[i, j], ...]}`, coordinates rounded to 4 decimals, `i < j` never required but `a < b` on stop ids before dedup.
- Generated `public/data.json` is gitignored.
- Fewest possible lines: do not add features not in the spec.

---

### Task 1: Data pipeline (`build.py`)

**Files:**
- Create: `build.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `public/data.json` with shape `{"stops": [[lon, lat], ...], "edges": [[i, j], ...]}` where `i`, `j` are indices into `stops`. Task 2 reads this file.

- [ ] **Step 1: Write `.gitignore`**

```
public/data.json
```

- [ ] **Step 2: Write `build.py`**

```python
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
```

- [ ] **Step 3: Run it and check the output**

Run: `mkdir -p public && python3 build.py`
Expected: prints roughly `2276 stops, 4673 edges` (numbers drift with the feed), and `public/data.json` is about 90 KB.

Run: `python3 -c "import json; d=json.load(open('public/data.json')); assert set(d)=={'stops','edges'}; assert all(0<=i<len(d['stops']) and 0<=j<len(d['stops']) for i,j in d['edges']); print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add build.py .gitignore
git commit -m "Add GTFS to JSON build script"
```

---

### Task 2: The page (`public/index.html`)

**Files:**
- Create: `public/index.html`

**Interfaces:**
- Consumes: `data.json` from Task 1, fetched relative to the page.

- [ ] **Step 1: Write `public/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FlixBus route map</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>html, body, #map { height: 100%; margin: 0; }</style>
</head>
<body>
<div id="map"></div>
<script>
const map = L.map("map", { preferCanvas: true }).setView([50, 10], 5);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

fetch("data.json").then(r => r.json()).then(({ stops, edges }) => {
  const latlngs = stops.map(([lon, lat]) => [lat, lon]);
  L.polyline(edges.map(([a, b]) => [latlngs[a], latlngs[b]]), { color: "#73d700", weight: 1.5 }).addTo(map);
  for (const p of latlngs) L.circleMarker(p, { radius: 2, color: "#333", weight: 1, fillOpacity: 1 }).addTo(map);
});
</script>
</body>
</html>
```

Notes for the implementer: `L.polyline` accepts an array of lines (a multi-polyline), so all edges are one layer. `preferCanvas` makes Leaflet draw vectors on a canvas instead of thousands of SVG nodes.

- [ ] **Step 2: Serve locally and check**

Run: `python3 -m http.server -d public 8000` and open `http://localhost:8000`.
Expected: a map of Europe with green lines between stops and small dark dots at stops. No console errors.

If no browser is available, at least run:
`python3 -c "import html.parser,sys; html.parser.HTMLParser().feed(open('public/index.html').read()); print('parsed')"`
Expected: `parsed`

- [ ] **Step 3: Commit**

```bash
git add public/index.html
git commit -m "Add Leaflet map page"
```

---

### Task 3: Vercel config and daily rebuild (`vercel.json`, `api/cron.py`)

**Files:**
- Create: `vercel.json`
- Create: `api/cron.py`

**Interfaces:**
- Consumes: environment variables `DEPLOY_HOOK_URL` (Vercel deploy hook, set in the Vercel dashboard) and `CRON_SECRET` (Vercel sends it as `Authorization: Bearer <secret>` on cron invocations).

- [ ] **Step 1: Write `vercel.json`**

```json
{
  "buildCommand": "python3 build.py",
  "outputDirectory": "public",
  "crons": [{ "path": "/api/cron", "schedule": "0 4 * * *" }]
}
```

- [ ] **Step 2: Write `api/cron.py`**

```python
"""Called daily by Vercel cron; triggers a redeploy via a deploy hook."""
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Authorization") != f"Bearer {os.environ['CRON_SECRET']}":
            self.send_response(401)
        else:
            with urllib.request.urlopen(os.environ["DEPLOY_HOOK_URL"], data=b"") as resp:
                self.send_response(resp.status)
        self.end_headers()
```

Note: `data=b""` turns the request into a POST, which is what deploy hooks expect.

- [ ] **Step 3: Check the function locally**

Run:
```bash
python3 - <<'EOF'
import os, threading, urllib.request, urllib.error
from http.server import HTTPServer
os.environ["CRON_SECRET"] = "s"
os.environ["DEPLOY_HOOK_URL"] = "http://127.0.0.1:8765/"   # a fake hook: see below
import importlib.util
spec = importlib.util.spec_from_file_location("cron", "api/cron.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from http.server import BaseHTTPRequestHandler
class Hook(BaseHTTPRequestHandler):
    def do_POST(self): self.send_response(201); self.end_headers()
hook = HTTPServer(("127.0.0.1", 8765), Hook); threading.Thread(target=hook.serve_forever, daemon=True).start()
srv = HTTPServer(("127.0.0.1", 8766), m.handler); threading.Thread(target=srv.serve_forever, daemon=True).start()
try: urllib.request.urlopen("http://127.0.0.1:8766/")
except urllib.error.HTTPError as e: print("no auth ->", e.code)
print("auth ->", urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8766/", headers={"Authorization": "Bearer s"})).status)
EOF
```
Expected: `no auth -> 401` then `auth -> 201`.

- [ ] **Step 4: Validate `vercel.json` is JSON**

Run: `python3 -c "import json; json.load(open('vercel.json')); print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add vercel.json api/cron.py
git commit -m "Add Vercel build config and daily rebuild cron"
```

---

## Hosting (done together later, not part of this plan)

1. Push the repo to GitHub and import it in Vercel with the "Other" framework preset.
2. Create a deploy hook (Project Settings → Git → Deploy Hooks) and set it as `DEPLOY_HOOK_URL`.
3. Set `CRON_SECRET` to a random string (Vercel then sends it with cron requests).
4. Deploy. The build runs `build.py`; the cron fires at 04:00 UTC daily.

# FlixBus route map — design

## Goal

A single web page showing every FlixBus/FlixTrain route in the European GTFS feed
(https://gtfs.gis.flix.tech/gtfs_generic_eu.zip) on a map. Optimise for the least
code and the fewest moving parts. Hosted on Vercel's free (Hobby) tier.

## What the map shows

- Every stop as a small dot.
- Every pair of consecutive stops on any trip as a straight line (schematic, not
  road geometry). Duplicate segments are merged, direction is ignored.
- Clicking a stop highlights the routes (GTFS `route_id`) that serve it and
  greys out all others. Clicking another stop moves the focus; clicking
  anywhere else resets it.
- Nothing else: no names, popups, or search.

## Data pipeline

`build.py` (Python 3, standard library only):

1. Download the zip into memory.
2. Read `stops.txt` → id → (lon, lat).
3. Read `trips.txt` → trip id → route id.
4. Read `stop_times.txt`, group by `trip_id`, sort by `stop_sequence`.
5. For each trip, add each consecutive `(stop_a, stop_b)` pair (ordered so a < b)
   to that route's set of segments.
6. Write `public/data.json`:
   `{"stops": [[lon, lat], ...], "routes": [[[i, j], ...], ...]}` where `i`, `j`
   index into `stops` and each inner list is one route's segments. Coordinates
   rounded to 4 decimals. Only stops that appear in a segment are included.

Measured on the 2026-09-06 feed: 2,276 stops, 1,176 routes, 10,914 segments,
163 KB, < 1 s of processing.

## Frontend

`public/index.html`, one file:

- Leaflet from cdnjs, OpenStreetMap raster tiles.
- `L.map(..., {preferCanvas: true})` so thousands of shapes render on canvas.
- Fetch `data.json`, add one multi-segment `L.polyline` per route and one
  `L.circleMarker` per stop, centred on Europe.
- A `focus(stop)` function recolours every route layer green or grey depending
  on whether it touches `stop` (`null` = all green). Stop markers call it on
  click with `bubblingMouseEvents: false` so the map's own click handler, which
  calls `focus(null)`, does not also fire.

No framework, no bundler, no npm.

## Refresh

- Every Vercel deploy runs `python3 build.py` (build command in `vercel.json`),
  so each deploy has fresh data. `public/data.json` is gitignored.
- Daily: a Vercel cron job (`vercel.json` `crons`, once per day, allowed on
  Hobby) calls `api/cron.py`, which POSTs to a Vercel deploy hook URL read from
  the `DEPLOY_HOOK_URL` environment variable. That triggers a rebuild.
- If the download fails, the build fails and Vercel keeps serving the previous
  deployment. No extra handling needed.

## Files

```
build.py            data pipeline
public/index.html   the page
api/cron.py         daily rebuild trigger
vercel.json         build command, output dir, cron schedule
.gitignore          public/data.json
```

## Testing

Run `python3 build.py` locally, serve `public/` with any static server, open in
a browser. No test framework.

## Deliberately excluded

Route names, stop names/tooltips, per-route colours, FlixBus vs FlixTrain
distinction, real road geometry (`shapes.txt`, 146 MB), search, filtering.

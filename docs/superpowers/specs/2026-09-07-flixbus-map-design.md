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
  anywhere else resets it. The selection is mirrored into the URL as
  `?stop=<stop_code>` (short, unique codes like `WOL`) so links survive reloads.
- A small box in the corner shows when the data was last updated, in the
  viewer's local time zone, and has an Update button (see Refresh).
- Nothing else: no names, popups, or search.

## Data pipeline

`api/update.py` (Python 3, standard library only) is both the build script and
the serverless function:

1. Download the zip into memory.
2. Read `stops.txt` → id → (lon, lat, stop_code).
3. Read `trips.txt` → trip id → route id.
4. Read `stop_times.txt`, group by `trip_id`, sort by `stop_sequence`.
5. For each trip, add each consecutive `(stop_a, stop_b)` pair (ordered so a < b)
   to that route's set of segments.
6. Produce
   `{"updated": "<ISO 8601 UTC>", "stops": [[lon, lat, code], ...], "routes": [[[i, j], ...], ...]}`
   where `i`, `j` index into `stops` and each inner list is one route's
   segments. Coordinates rounded to 4 decimals. Only stops that appear in a
   segment are included.
7. Upload it to Vercel Blob as `data.json` (PUT to the Blob API with the
   `BLOB_READ_WRITE_TOKEN`, overwrite allowed, no random suffix, 60 s cache).
   Without a token it writes `public/data.json` instead, for local development.

Measured on the 2026-09-06 feed: 2,276 stops, 1,176 routes, 10,914 segments,
180 KB, < 1 s of processing plus the 30 MB download.

## Frontend

`public/index.html`, one file:

- Leaflet from cdnjs, OpenStreetMap raster tiles. Routes are drawn in deep
  purple, a colour OSM's default style never uses, so they stand out.
- `L.map(..., {preferCanvas: true})` so thousands of shapes render on canvas.
- Fetch `data.json` (rewritten by Vercel to the blob's public URL), add one
  multi-segment `L.polyline` per route and one `L.circleMarker` per stop,
  centred on Europe.
- A `focus(stop)` function recolours every route layer purple or faint grey
  depending on whether it touches `stop` (`null` = all purple) and brings the
  purple ones to the front. Stop markers call it on click with
  `bubblingMouseEvents: false` so the map's own click handler, which calls
  `focus(null)`, does not also fire.
- Stops are drawn on a separate canvas in their own pane above the routes
  (Leaflet's canvas hit-test picks the topmost shape, so routes must never sit
  above stops), with a 6 px click tolerance so the small dots are easy to hit.

No framework, no bundler, no npm.

## Refresh

- Every Vercel deploy runs `python3 api/update.py` as the build command, which
  uploads fresh data to Blob. So there is always data, from the first deploy on.
- The Update button POSTs to `/api/update`. The function rebuilds and uploads
  the data, then returns the new `updated` timestamp. The page reloads with
  `?v=<timestamp>` appended, which bypasses the CDN's cached copy of
  `data.json` (Blob's minimum cache time is 60 s); the page drops `v` from the
  URL again once loaded. Other visitors see the new data within a minute.
- If the download fails during the build, the build fails and Vercel keeps the
  previous deployment and the previous blob. If it fails during a button press,
  the function returns 500 and the button shows "Update failed".
- The button is public by design.

## Files

```
api/update.py       data pipeline: build script + Update function
public/index.html   the page
vercel.json         build command, function timeout, /data.json -> Blob rewrite
.gitignore          public/data.json
```

## Testing

Run `python3 api/update.py` locally (writes `public/data.json` when no Blob
token is set), serve `public/` with any static server, open in a browser. No
test framework.

## Deliberately excluded

Route names, stop names/tooltips, per-route colours, FlixBus vs FlixTrain
distinction, real road geometry (`shapes.txt`, 146 MB), search, filtering.

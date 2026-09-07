# FlixBus route map

A single-page map of every FlixBus and FlixTrain stop in Europe, with straight
lines between consecutive stops. Click a stop to highlight the routes that serve
it; click anywhere else to reset. The corner box shows when the data was last
built; its **Update** button triggers a fresh build.

Data: the public GTFS feed at https://gtfs.gis.flix.tech/gtfs_generic_eu.zip.

## Run locally

Requires Python 3. No other dependencies.

```bash
python3 build.py                       # downloads the feed, writes public/data.json
python3 -m http.server -d public 8000  # then open http://localhost:8000
```

## Files

| File                | Purpose                                                                   |
|---------------------|---------------------------------------------------------------------------|
| `build.py`          | Turns the GTFS feed into `public/data.json` (stops + per-route segments). |
| `public/index.html` | The whole frontend: Leaflet, OpenStreetMap tiles, click handling.         |
| `api/cron.py`       | Serverless function that triggers a redeploy via a Vercel deploy hook.    |
| `vercel.json`       | Build command, output directory, daily cron schedule.                     |

`public/data.json` is generated and not committed.

## Deploy on Vercel

1. Import the repo in Vercel with the **Other** framework preset. The build
   command and output directory come from `vercel.json`.
2. In the project settings, create a **Deploy Hook** and store its URL in the
   environment variable `DEPLOY_HOOK_URL`.
3. Deploy. Every deploy downloads a fresh feed. The Update button on the page
   POSTs to `/api/update`, which calls the deploy hook; the new data appears
   about a minute later. Anyone can press it, and each press costs one build.

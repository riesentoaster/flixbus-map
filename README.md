# FlixBus route map

A single-page map of every FlixBus and FlixTrain stop in Europe, with straight
lines between consecutive stops. Click a stop to highlight the routes that serve
it; click anywhere else to reset. The selected stop is kept in the URL
(`?stop=WOL`), so links can be shared. The corner box shows when the data was
last updated; its **Update** button fetches a fresh feed and reloads.

Data: the public GTFS feed at https://gtfs.gis.flix.tech/gtfs_generic_eu.zip.

## Run locally

Requires Python 3. No other dependencies.

```bash
python3 api/update.py                  # downloads the feed, writes public/data.json
python3 -m http.server -d public 8000  # then open http://localhost:8000
```

Without a Blob token the script writes a local file, so the map works offline
from Vercel. The Update button does nothing locally (there is no backend).

## Files

| File                | Purpose                                                                   |
|---------------------|---------------------------------------------------------------------------|
| `public/index.html` | The whole frontend: Leaflet, OpenStreetMap tiles, click handling.         |
| `api/update.py` | Downloads the feed and turns it into `data.json`. Run by the build (so every deploy has data) and by the Update button (`POST /api/update`). Stores the result in Vercel Blob. |
| `vercel.json` | Build command, function timeout, and the rewrite from `/data.json` to the Blob store. |

`public/data.json` is generated and not committed.

## Deploy on Vercel

1. Import the repo in Vercel with the **Other** framework preset. The build
   command and output directory come from `vercel.json`.
2. In the project's **Storage** tab, create a **Blob** store and connect it to
   the project. This sets the `BLOB_READ_WRITE_TOKEN` environment variable.
3. Replace `STORE_ID` in the `vercel.json` rewrite with your store's id (the
   hostname of any blob URL in the store, `<id>.public.blob.vercel-storage.com`).
4. Deploy. The build downloads the feed and uploads `data.json` to Blob, so
   there is data from the first deploy on. The Update button does the same on
   demand and reloads the page. Anyone can press it.

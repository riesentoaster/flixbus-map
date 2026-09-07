# FlixBus route map

A single-page map of every FlixBus and FlixTrain stop in Europe, with straight
lines between consecutive stops. Click a stop to highlight the routes that serve
it; click anywhere else to reset. The selected stop is kept in the URL
(`?stop=WOL`), so links can be shared. The corner box shows when the data was
last updated; its **Update** button fetches a fresh feed and redraws the map.

Data: the public GTFS feed at https://gtfs.gis.flix.tech/gtfs_generic_eu.zip.

## Run locally

Requires Python 3. No other dependencies.

```bash
python3 dev.py   # then open http://localhost:8000 and press Update
```

`dev.py` serves `public/` and runs the update function behind `POST /api/update`,
like Vercel does. Without a Blob token the update writes `public/data.json`
instead of uploading, so everything works without a Vercel account.

## Files

| File                | Purpose                                                                   |
|---------------------|---------------------------------------------------------------------------|
| `public/index.html` | The whole frontend: Leaflet, OpenStreetMap tiles, click handling.         |
| `dev.py` | Local stand-in for Vercel: static files plus the update function. |
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
   demand and redraws the map with the result. Anyone can press it.

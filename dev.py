"""Local dev server: serves public/ and runs api/update.py behind POST /api/update, like Vercel does.

Run `python3 dev.py`, then open http://localhost:8000. Without BLOB_READ_WRITE_TOKEN the update
writes public/data.json, which this server then serves.
"""
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

sys.path.insert(0, "api")
import update  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    do_POST = update.handler.do_POST


HTTPServer(("", 8000), partial(Handler, directory="public")).serve_forever()

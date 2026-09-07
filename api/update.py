"""Called by the page's Update button; triggers a rebuild via a Vercel deploy hook."""
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        with urllib.request.urlopen(os.environ["DEPLOY_HOOK_URL"], data=b"") as resp:
            self.send_response(resp.status)
        self.end_headers()

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

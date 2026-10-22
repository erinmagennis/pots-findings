#!/usr/bin/env python3
"""serve_local.py — preview the static site with Vercel-style clean URLs (/about -> about.html). Usage: python site_tools/serve_local.py [port]"""
import http.server, os, sys, functools
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?", 1)[0].split("#", 1)[0]
        full = super().translate_path(p)
        if not os.path.exists(full) and not os.path.splitext(p)[1] and os.path.exists(full + ".html"): return full + ".html"
        return full
    def log_message(self, *a): pass
if __name__ == "__main__":
    os.chdir(ROOT); print(f"serving {os.path.abspath(ROOT)} at http://localhost:{PORT}/ (clean URLs)", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

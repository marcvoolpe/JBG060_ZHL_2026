"""
Labelling server: opens the labelling tool and saves every label to disk the
moment you press Save.

    python cropland/label_server.py

then open http://localhost:8765 in any browser. Each labeller's work goes to
cropland/labels/<set>_labels_<name>.csv (one file per person, so commits from
different people never clash). The file is rewritten after every saved point,
and the tool reloads it when you come back, so clearing the browser loses
nothing. Stop the server with Ctrl+C.

Only the Python standard library is used. The server listens on this computer
only (127.0.0.1), not on the network.
"""

import csv
import json
import os
import re
import tempfile
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
TOOL = HERE / "label_tool"
LABELS = HERE / "labels"
PORT = 8765
COLUMNS = ["id", "lat", "lon", "area", "labeller", "label", "reason", "confidence", "cover",
           "cue_a_bare", "cue_b_greenup", "cue_c_harvest", "cue_d_shape", "cue_e_crop2024",
           "key_suggestion", "overridden", "minutes", "notes", "saved_at"]
SAFE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def path_for(which: str, who: str) -> Path:
    if not (SAFE.match(which) and SAFE.match(who)):
        raise ValueError("bad set or labeller name")
    return LABELS / f"{which}_labels_{who}.csv"


def read(which, who) -> dict:
    p = path_for(which, who)
    if not p.exists():
        return {}
    with p.open(newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f) if r.get("label")}


def write(which, who, rows: list[dict]):
    """Write atomically: a crash halfway never leaves a broken file."""
    LABELS.mkdir(exist_ok=True)
    p = path_for(which, who)
    fd, tmp = tempfile.mkstemp(dir=LABELS, suffix=".tmp")
    with os.fdopen(fd, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    # On Windows, OneDrive or an open Excel window can lock the CSV for a moment: retry, then write directly.
    for _ in range(10):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.2)
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.remove(tmp)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(TOOL), **kw)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/labels":
            q = parse_qs(u.query)
            try:
                self._json(200, read(q["set"][0], q["who"][0]))
            except (KeyError, ValueError) as e:
                self._json(400, {"error": str(e)})
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/labels":
            self._json(404, {"error": "not found"})
            return
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            write(data["set"], data["who"], data["rows"])
            self._json(200, {"saved": len(data["rows"])})
        except (KeyError, ValueError, TypeError) as e:
            self._json(400, {"error": str(e)})
        except OSError as e:
            print(f"could not write the label file: {e}")
            self._json(500, {"error": f"could not write the label file: {e}"})

    def log_message(self, fmt, *args):
        if "/api/labels" in (args[0] if args else "") and "POST" in (args[0] if args else ""):
            print(f"saved  {self.address_string()}  {args[0]}")


def main() -> None:
    LABELS.mkdir(exist_ok=True)
    n_img = len(list((TOOL / "img").glob("*.webp"))) if (TOOL / "img").exists() else 0
    if n_img < 1900:
        print(f"WARNING: only {n_img} images in cropland/label_tool/img/ (expected 1,920).\n"
              "  Unzip cropland_images.zip inside cropland/label_tool/ so that the folder\n"
              "  cropland/label_tool/img/ holds the .webp files. The images are not in git.")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Labelling tool: http://localhost:{PORT}   (labels saved in {LABELS})   Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()

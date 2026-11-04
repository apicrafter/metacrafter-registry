"""Local static server that mimics GitHub Pages URL resolution.

GitHub Pages serves ``/datatype/email`` from ``datatype/email.html``,
redirects ``/tool`` to ``/tool/`` when ``tool/`` is a directory, and serves
``404.html`` with status 404. Python's ``http.server`` does none of that, so
this handler adds it. It lets CI check the public URL contract before deploy.
"""

from __future__ import annotations

import functools
import http.server
import mimetypes
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote, urlsplit

mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("text/turtle", ".ttl")
mimetypes.add_type("application/x-ndjson", ".jsonl")


class PagesLikeHandler(http.server.SimpleHTTPRequestHandler):
    def _resolve(self) -> tuple[str, Path | None]:
        """Return ('file', path) | ('redirect', None) | ('missing', None)."""
        root = Path(self.directory).resolve()
        url_path = unquote(urlsplit(self.path).path)
        target = (root / url_path.lstrip("/")).resolve()
        if root not in (target, *target.parents):
            return "missing", None
        if target.is_dir():
            if not url_path.endswith("/"):
                return "redirect", None
            index = target / "index.html"
            return ("file", index) if index.is_file() else ("missing", None)
        if target.is_file():
            return "file", target
        html = target.with_name(target.name + ".html")
        if html.is_file():
            return "file", html
        return "missing", None

    def send_head(self):  # noqa: D401 - stdlib override
        kind, path = self._resolve()
        if kind == "redirect":
            parts = urlsplit(self.path)
            location = parts.path + "/" + (f"?{parts.query}" if parts.query else "")
            self.send_response(301)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        status = 200
        if kind == "missing":
            status = 404
            path = Path(self.directory) / "404.html"
            if not path.is_file():
                self.send_error(404)
                return None
        ctype = self.guess_type(str(path))
        if ctype.startswith("text/") or ctype == "application/json":
            ctype += "; charset=utf-8"
        handle = open(path, "rb")
        size = path.stat().st_size
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        return handle

    def log_message(self, format: str, *args) -> None:  # quieter default
        if getattr(self.server, "verbose", False):
            super().log_message(format, *args)


def make_server(directory: Path, host: str = "127.0.0.1", port: int = 8089, verbose=True):
    handler = functools.partial(PagesLikeHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer((host, port), handler)
    server.verbose = verbose
    return server


def serve(directory: Path, host: str = "127.0.0.1", port: int = 8089) -> None:
    server = make_server(directory, host, port)
    print(f"Serving {directory} at http://{host}:{server.server_address[1]}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


@contextmanager
def running_server(directory: Path) -> Iterator[str]:
    """Serve ``directory`` on a free port in a background thread; yield its base URL."""
    server = make_server(directory, port=0, verbose=False)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()

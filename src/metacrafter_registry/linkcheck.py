"""Check that every internal link in a built site resolves.

Links are resolved with the same rules GitHub Pages applies (see ``serve.py``):
an exact file, ``<path>.html`` for extensionless URLs, or ``index.html`` for
directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value and name in ("href", "src", "action"):
                self.links.append(value)


@dataclass(frozen=True)
class BrokenLink:
    page: str
    link: str

    def __str__(self) -> str:
        return f"{self.page}: {self.link}"


def _resolves(root: Path, url_path: str) -> bool:
    target = root / url_path.lstrip("/")
    if url_path.endswith("/"):
        return (target / "index.html").is_file()
    return (
        target.is_file()
        or target.with_name(target.name + ".html").is_file()
        or (target / "index.html").is_file()
    )


def check_links(root: Path, base_path: str = "") -> tuple[int, list[BrokenLink]]:
    """Return (number of internal links checked, broken links)."""
    root = Path(root)
    base_path = base_path.rstrip("/")
    checked = 0
    broken: list[BrokenLink] = []
    for page in sorted(root.rglob("*.html")):
        parser = _LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith(("#", "mailto:")):
                continue
            path = unquote(parts.path)
            if not path.startswith("/"):
                path = "/" + (page.parent.relative_to(root) / path).as_posix().lstrip("./")
            if base_path:
                if not path.startswith(base_path + "/") and path != base_path:
                    broken.append(BrokenLink(page.relative_to(root).as_posix(), link))
                    continue
                path = path[len(base_path) :] or "/"
            checked += 1
            if not _resolves(root, path):
                broken.append(BrokenLink(page.relative_to(root).as_posix(), link))
    return checked, broken

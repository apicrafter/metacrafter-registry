"""Runtime access to registry data: lookup, search, value identification.

    from metacrafter_registry import Registry

    reg = Registry.load()     # bundled snapshot, or the YAML sources of a checkout
    reg = Registry.fetch()    # published data from the site, cached locally
    reg.get("ssn")            # aliases resolve to the canonical record
    reg.identify(["7707083893"], field_name="inn")

Records are the normalized ``/api/v1/`` records (see ``/api/v1/openapi.json``).
Nothing here sends sample values anywhere: matching runs locally.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.request
from collections.abc import Iterable, Iterator
from functools import cached_property
from pathlib import Path
from typing import Any

from . import DEFAULT_BASE_URL
from .checksums import ALGORITHMS
from .fibo import normalize as fibo_normalize

SNAPSHOT_FILES = (
    "index.json",
    "datatypes.jsonl",
    "tools.json",
    "aliases.json",
    "categories.json",
    "countries.json",
    "languages.json",
)
SNAPSHOT_DIR = Path(__file__).with_name("snapshot")

_TOKEN = re.compile(r"[a-z0-9]+")
_SEPARATORS = re.compile(r"[\s-]")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

# How a regexp matches one value (see _match_kind).
_NO_MATCH, _RAW, _COMPACT = 0, 1, 2
# A value that a regexp matches only without its spaces and hyphens is weaker
# evidence than a match as written: in the score it counts this much of a hit,
# unless the record's check digit passes on it. identify-core.js uses the same
# weight.
_COMPACT_WEIGHT = 0.5


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(_CAMEL.sub(" ", str(text)).lower()))


def _match_kind(pattern: re.Pattern[str], value: str) -> int:
    """_RAW if ``pattern`` matches ``value`` as written, _COMPACT if it matches
    only once spaces and hyphens are removed, _NO_MATCH otherwise."""
    # A column value is the whole value: unanchored registry regexps must not
    # match a substring of a longer value. Values printed with spaces or
    # hyphens ("4111 1111 1111 1111") are also tried in compact form.
    if pattern.fullmatch(value) is not None:
        return _RAW
    compact = _SEPARATORS.sub("", value)
    if compact != value and pattern.fullmatch(compact) is not None:
        return _COMPACT
    return _NO_MATCH


def _sherlock_key(label: str) -> str:
    """A Sherlock type label without case and whitespace: "birth Date" -> "birthdate"."""
    return re.sub(r"\s+", "", str(label)).lower()


def _purview_key(name: str) -> str:
    """Compare Purview type names without case, periods and apostrophes."""
    return " ".join(re.sub(r"[.'’]", "", name).casefold().split())


def _orgid_code(value: str) -> str:
    """The ORG-ID.guide list code of a code, its URL or a full identifier.

    ``https://org-id.guide/list/GB-COH``, ``gb-coh`` and ``GB-COH-09506232`` all
    give ``GB-COH``: a list code has exactly one hyphen, and an ORG-ID.guide
    organization identifier is the list code, a hyphen and the identifier.
    """
    value = str(value).strip()
    if "org-id.guide/list/" in value:
        value = value.split("org-id.guide/list/", 1)[1].strip("/")
    return "-".join(value.split("-")[:2]).upper()


# qddate generates variants of each date pattern: with a time after the date
# (:time_1 ... :time_4), before it (:time_left), and with text after it (:t_right).
_QDDATE_VARIANT = re.compile(r"(?::time_(?:\d+|left))?(?::t_right)?$")


def _qddate_key(value: str) -> str:
    """The base qddate pattern key of a key, a generated variant or a bare name.

    ``dt:date:date_2:time_1``, ``dt:date:date_2:t_right`` and ``date_2`` all give
    ``dt:date:date_2``, the key that ``mappings.qddate`` holds.
    """
    key = _QDDATE_VARIANT.sub("", str(value).strip(), count=1)
    return key if key.startswith("dt:") else "dt:date:" + key


def _bioregistry_prefix(value: str) -> str:
    """The normalized Bioregistry prefix of a prefix, its URL or a CURIE.

    ``CHEBI``, ``https://bioregistry.io/chebi``, ``https://bioregistry.io/registry/chebi``
    and ``CHEBI:15377`` all give ``chebi``, the form ``mappings.bioregistry`` holds.
    """
    value = str(value).strip().rstrip("/")
    if "bioregistry.io/" in value:
        value = value.split("bioregistry.io/", 1)[1].removeprefix("registry/")
    return value.split(":", 1)[0].casefold()


def _stdnum_module(value: str) -> str:
    """The python-stdnum module path of a module name, its file path or its documentation URL.

    ``stdnum.br.cpf``, ``br/cpf``, ``br.cpf`` and
    ``https://arthurdejong.org/python-stdnum/doc/2.2/stdnum.br.cpf.html`` all give
    ``br.cpf``, the form ``mappings.stdnum`` holds.
    """
    value = str(value).strip().rstrip("/")
    if "://" in value:
        value = value.rsplit("/", 1)[-1].removesuffix(".html")
    value = value.removesuffix(".py").replace("/", ".")
    return value.removeprefix("stdnum.").casefold()


def _cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "metacrafter-registry"


def _get(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "metacrafter-registry-client"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


class Registry:
    """Normalized registry records with lookup, search and identification."""

    def __init__(
        self,
        datatypes: Iterable[dict[str, Any]],
        tools: Iterable[dict[str, Any]] = (),
        aliases: dict[str, str] | None = None,
        manifest: dict[str, Any] | None = None,
        categories: Iterable[dict[str, Any]] = (),
        countries: Iterable[dict[str, Any]] = (),
        languages: Iterable[dict[str, Any]] = (),
        source: str = "",
    ) -> None:
        self.datatypes = {r["id"]: r for r in datatypes}
        self.tools = {t["id"]: t for t in tools}
        self.aliases = dict(aliases or {})
        self.manifest = dict(manifest or {})
        self.categories = {c["id"]: c for c in categories}
        self.countries = {c["id"]: c for c in countries}
        self.languages = {c["id"]: c for c in languages}
        self.source = source

    # --- constructors ------------------------------------------------------

    @classmethod
    def from_directory(cls, directory: Path | str, source: str = "") -> Registry:
        """Load snapshot files (as published under /api/v1/)."""
        directory = Path(directory)

        def read_json(name: str, default: Any) -> Any:
            path = directory / name
            return json.loads(path.read_text("utf-8")) if path.exists() else default

        lines = (directory / "datatypes.jsonl").read_text("utf-8").splitlines()
        return cls(
            datatypes=[json.loads(line) for line in lines if line.strip()],
            tools=read_json("tools.json", []),
            aliases=read_json("aliases.json", {}),
            manifest=read_json("index.json", {}),
            categories=read_json("categories.json", []),
            countries=read_json("countries.json", []),
            languages=read_json("languages.json", []),
            source=source or str(directory),
        )

    @classmethod
    def from_sources(cls, data_dir: Path | str, base_url: str = DEFAULT_BASE_URL) -> Registry:
        """Build from the YAML sources of a registry checkout (no validation)."""
        from .loader import load_sources
        from .model import build_registry

        model = build_registry(load_sources(Path(data_dir)), base_url)
        return cls(
            datatypes=model.datatypes.values(),
            tools=model.tools.values(),
            aliases=model.aliases,
            manifest={"base_url": base_url.rstrip("/"), "version": "source"},
            categories=model.categories.values(),
            countries=model.countries.values(),
            languages=model.langs.values(),
            source=f"sources:{data_dir}",
        )

    @classmethod
    def load(cls, path: Path | str | None = None) -> Registry:
        """Load local data, in this order: ``path`` (a snapshot or a ``data/``
        directory), the sources of the checkout this package runs from, the
        snapshot bundled in the wheel, a ``data/`` directory above the current
        directory."""
        if path is not None:
            path = Path(path)
            if (path / "datatypes.jsonl").exists():
                return cls.from_directory(path)
            if (path / "datatypes").is_dir():
                return cls.from_sources(path)
            raise FileNotFoundError(f"{path} is neither a snapshot nor a registry data directory")
        # In a source checkout the live YAML wins over any stale bundled snapshot.
        source_checkout = Path(__file__).resolve().parents[2] / "data"
        if (source_checkout / "datatypes").is_dir():
            return cls.from_sources(source_checkout)
        if (SNAPSHOT_DIR / "datatypes.jsonl").exists():
            return cls.from_directory(SNAPSHOT_DIR, source="bundled snapshot")
        from .loader import find_data_dir

        try:
            return cls.from_sources(find_data_dir())
        except FileNotFoundError:
            pass
        raise FileNotFoundError(
            "No bundled snapshot and no registry checkout found; use Registry.fetch()"
        )

    @classmethod
    def fetch(
        cls,
        base_url: str = DEFAULT_BASE_URL,
        *,
        cache_dir: Path | str | None = None,
        timeout: float = 30.0,
    ) -> Registry:
        """Load the published data, downloading only when the manifest changed.

        Downloaded files are verified against the SHA-256 in the manifest.
        """
        base = base_url.rstrip("/")
        cache = (
            Path(cache_dir)
            if cache_dir
            else _cache_dir() / hashlib.sha1(base.encode()).hexdigest()[:12]
        )
        manifest = json.loads(_get(f"{base}/api/v1/index.json", timeout))
        cached_manifest = cache / "index.json"
        if cached_manifest.exists() and json.loads(cached_manifest.read_text("utf-8")) == manifest:
            return cls.from_directory(cache, source=f"{base} (cached)")
        cache.mkdir(parents=True, exist_ok=True)
        hashes = {
            Path(info["path"]).name: info["sha256"]
            for name, info in manifest.get("files", {}).items()
            if name.startswith("api/v1/")
        }
        for name in SNAPSHOT_FILES[1:]:
            body = _get(f"{base}/api/v1/{name}", timeout)
            expected = hashes.get(name)
            if expected and hashlib.sha256(body).hexdigest() != expected:
                raise ValueError(f"{name}: SHA-256 does not match the manifest")
            (cache / name).write_bytes(body)
        cached_manifest.write_text(json.dumps(manifest), "utf-8")
        return cls.from_directory(cache, source=base)

    # --- lookup ------------------------------------------------------------

    @property
    def version(self) -> str:
        return str(self.manifest.get("version", "unknown"))

    @property
    def base_url(self) -> str:
        return str(self.manifest.get("base_url", DEFAULT_BASE_URL)).rstrip("/")

    def __len__(self) -> int:
        return len(self.datatypes)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.datatypes.values())

    def __contains__(self, rid: object) -> bool:
        return self.resolve(str(rid)) is not None

    def resolve(self, rid: str) -> str | None:
        """Canonical id for an id or a former id (alias)."""
        rid = str(rid).strip()
        if rid in self.datatypes:
            return rid
        return self.aliases.get(rid)

    def get(self, rid: str) -> dict[str, Any] | None:
        canonical = self.resolve(rid)
        return self.datatypes.get(canonical) if canonical else None

    def url_for(self, rid: str) -> str:
        canonical = self.resolve(rid) or rid
        template = self.manifest.get("datatype_url_template") or self.base_url + "/datatype/{id}"
        return template.replace("{id}", canonical)

    # --- search ------------------------------------------------------------

    def search(
        self,
        query: str = "",
        *,
        category: str | None = None,
        country: str | None = None,
        is_pii: bool | None = None,
        status: str | None = None,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Rank records by query tokens (id, aliases, names, translations, doc)."""
        tokens = [t for t in _TOKEN.findall(query.lower())] if query else []
        country = country.upper() if country else None
        hits = []
        for record in self.datatypes.values():
            if category and category not in record.get("categories", []):
                continue
            if country and country not in record.get("country", []):
                continue
            if is_pii is not None and record["is_pii"] != is_pii:
                continue
            if status and record["status"] != status:
                continue
            if kind and record["kind"] != kind:
                continue
            score = self._text_score(record, tokens) if tokens else 1
            if score:
                hits.append((score, record))
        hits.sort(key=lambda hit: (-hit[0], hit[1]["id"]))
        return [record for _, record in hits[:limit]]

    @staticmethod
    def _text_score(record: dict[str, Any], tokens: list[str]) -> int:
        rid = record["id"]
        aliases = " ".join(record.get("aliases", []))
        name = record["name"].lower()
        names = " ".join(t.get("name", "") for t in record.get("translations", {}).values()).lower()
        cats = " ".join(record.get("categories", []) + record.get("country", [])).lower()
        doc = record["doc"].lower()
        total = 0
        for t in tokens:
            if rid == t or t in record.get("aliases", []):
                s = 100
            elif rid.startswith(t):
                s = 60
            elif t in rid or t in aliases:
                s = 40
            elif t in name:
                s = 35
            elif t in names:
                s = 25
            elif t in cats:
                s = 10
            elif t in doc:
                s = 8
            else:
                return 0
            total += s
        return total

    # --- identification ----------------------------------------------------

    @cached_property
    def _compiled(self) -> dict[str, re.Pattern[str]]:
        compiled = {}
        for rid, record in self.datatypes.items():
            if record.get("regexp"):
                try:
                    compiled[rid] = re.compile(record["regexp"])
                except re.error:
                    continue
        return compiled

    @cached_property
    def _broadness(self) -> dict[str, float]:
        """Share of other records' example values that each regexp also matches.

        A regexp like ``[A-Za-z0-9_]+`` matches most identifiers, so a hit is weak
        evidence; a regexp that matches no other record's examples is strong.
        Rounded to 3 decimals, as in the site's identify index, so that the
        Python and JavaScript scorers compute the same scores.
        """
        corpus = [
            (record["id"], example["value"])
            for record in self.datatypes.values()
            for example in record.get("examples", [])
            if example.get("valid", True)
        ]
        broadness = {}
        for rid, pattern in self._compiled.items():
            others = [value for owner, value in corpus if owner != rid]
            matched = sum(1 for value in others if pattern.fullmatch(value))
            broadness[rid] = round(matched / len(others), 3) if others else 0.0
        return broadness

    def _regexp_matches(self, rid: str, value: str) -> bool:
        pattern = self._compiled.get(rid)
        return pattern is not None and _match_kind(pattern, value) != _NO_MATCH

    def match(self, value: str) -> list[dict[str, Any]]:
        """Records whose regexp matches ``value`` and whose check digit (if any) passes."""
        value = str(value).strip()
        out = []
        for rid in sorted(self._compiled):
            if not self._regexp_matches(rid, value):
                continue
            record = self.datatypes[rid]
            algorithm = record.get("checksum")
            if algorithm in ALGORITHMS and not ALGORITHMS[algorithm](value):
                continue
            out.append(record)
        return out

    def _name_similarity(self, record: dict[str, Any], field_name: str) -> float:
        field = field_name.strip().lower()
        if not field:
            return 0.0
        if field == record["id"] or field in record.get("aliases", []):
            return 1.0
        field_tokens = _tokens(field_name)
        if not field_tokens:
            return 0.0
        best = 0.0
        # "card" in "bankcard", "phone" in "phonenumber": ids are often run together
        for candidate_id in (record["id"], *record.get("aliases", [])):
            compact = candidate_id.replace("_", "")
            if any(len(tok) >= 4 and tok in compact for tok in field_tokens):
                best = 0.6
        candidates = [record["id"], *record.get("aliases", []), record["name"]]
        candidates += [t.get("name", "") for t in record.get("translations", {}).values()]
        for candidate in candidates:
            tokens = _tokens(candidate)
            if not tokens:
                continue
            overlap = len(field_tokens & tokens) / len(field_tokens | tokens)
            best = max(best, overlap)
        return best

    def identify(
        self,
        values: Iterable[Any],
        *,
        field_name: str | None = None,
        country: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Rank candidate datatypes for sample values of one column.

        Score (0-100): 60 x weighted regexp hit rate x regexp specificity
        + 25 x check-digit pass rate + 25 x field-name similarity, +5 for a
        matching country, -10 for a different country, -5 for drafts; capped at
        100. Specificity is 1 minus the share of other records' examples that the
        regexp also matches, so catch-all patterns rank low.

        A value printed with spaces or hyphens ("4111 1111 1111 1111") is also a
        regexp hit when it matches without them, unless the regexp of another
        record that is at least as specific matches the value as written. So
        "2025-05-15" is not a hit for an eight-digit number such as ``okpo``
        when a date regexp matches it. That check uses every record with a
        regexp, whatever ``status`` filters.

        In the weighted hit rate a value matched as written counts 1 and a value
        matched only without its spaces and hyphens counts 0.5, so a regexp that
        fits the notation of the values outranks one that fits only their
        digits. A value matched without separators whose check digit passes
        counts 1: its spaces are presentation, as in grouped card numbers.
        ``regexp_hit_rate`` in the result is the unweighted share of values that
        are hits in either form.
        """
        samples = [str(v).strip() for v in values if v is not None and str(v).strip()]
        country = country.upper() if country else None
        kinds = (
            {rid: [_match_kind(p, v) for v in samples] for rid, p in self._compiled.items()}
            if samples
            else {}
        )
        # Per sample, the broadness of the most specific regexp that matches it
        # as written: a compact-form hit counts only for a more specific regexp.
        claimed = [math.inf] * len(samples)
        for rid, record_kinds in kinds.items():
            for i, kind in enumerate(record_kinds):
                if kind == _RAW:
                    claimed[i] = min(claimed[i], self._broadness[rid])
        results = []
        for rid, record in self.datatypes.items():
            if status and record["status"] != status:
                continue
            hit_rate = None
            weighted_rate = 0.0
            algorithm = record.get("checksum")
            checks = (
                [ALGORITHMS[algorithm](v) for v in samples]
                if samples and algorithm in ALGORITHMS
                else None
            )
            if rid in kinds:
                own = self._broadness[rid]
                hits, weight = 0, 0.0
                for i, kind in enumerate(kinds[rid]):
                    if kind == _RAW:
                        hits += 1
                        weight += 1.0
                    elif kind == _COMPACT and claimed[i] > own:
                        hits += 1
                        weight += 1.0 if checks and checks[i] else _COMPACT_WEIGHT
                hit_rate = hits / len(samples)
                weighted_rate = weight / len(samples)
            checksum = None
            if checks is not None:
                checksum = {"algorithm": algorithm, "pass_rate": sum(checks) / len(samples)}
            similarity = self._name_similarity(record, field_name) if field_name else 0.0
            if not (hit_rate or (checksum and checksum["pass_rate"]) or similarity >= 0.5):
                continue
            specificity = 1.0 - self._broadness.get(rid, 0.0)
            score = 60 * weighted_rate * specificity + 25 * similarity
            if checksum:
                score += 25 * checksum["pass_rate"]
            if country and record.get("country"):
                score += 5 if country in record["country"] else -10
            if record["status"] == "draft":
                score -= 5
            results.append(
                {
                    "id": rid,
                    "name": record["name"],
                    "kind": record["kind"],
                    "status": record["status"],
                    "is_pii": record["is_pii"],
                    "score": max(0, min(100, round(score))),
                    "regexp_hit_rate": None if hit_rate is None else round(hit_rate, 3),
                    "regexp_specificity": None if hit_rate is None else round(specificity, 3),
                    "checksum": None
                    if checksum is None
                    else {**checksum, "pass_rate": round(checksum["pass_rate"], 3)},
                    "field_name_similarity": round(similarity, 3),
                    "url": self.url_for(rid),
                }
            )
        results.sort(key=lambda r: (-r["score"], r["status"] != "stable", r["id"]))
        return results[:limit]

    # --- crosswalk ---------------------------------------------------------

    def crosswalk(self, system: str, external_id: str) -> list[dict[str, Any]]:
        """Records mapped to ``external_id`` in another vocabulary (wikidata, fibo, presidio, ...).

        For wikidata, a property id or its URL; for fibo, a class path or its full IRI;
        for fta, a semantic type as FTA reports it, including locale-bound names such
        as MONTH.FULL_fr-FR or GENDER.TEXT_DE; for sherlock, a type label, compared
        without case and spaces; for sato, a Sato type label (Sato predicts the
        Sherlock types, written birthDate); for autotype, a benchmark test case name,
        its file name or its data_release path;
        for gs1_ai, an Application Identifier as written in a barcode's
        human-readable text ((414) or 414) or its https://ref.gs1.org/ai/ IRI;
        for orgid, an ORG-ID.guide list code (GB-COH), its org-id.guide URL or a
        whole organization identifier (GB-COH-09506232);
        for qddate, a date pattern key as qddate and metacrafter report it
        (dt:date:date_2), a generated variant of it (dt:date:date_2:time_1,
        dt:date:date_2:t_right), which resolves to the notation of its date part,
        or the key without dt:date: (date_2);
        for bioregistry, a Bioregistry prefix (chebi, CHEBI), its bioregistry.io URL or a
        CURIE (CHEBI:15377);
        for stdnum, a python-stdnum module (br.cpf, stdnum.br.cpf, br/cpf) or its
        documentation URL;
        for fhir, an HL7 FHIR identifier system URI (http://hl7.org/fhir/sid/us-ssn).
        """
        if system == "fta":
            return self._crosswalk_fta(str(external_id).strip())
        # Sato predicts the 78 Sherlock types, in camelCase (birthDate), so its
        # labels resolve through mappings.sherlock.
        if system == "sato":
            system = "sherlock"
        wanted = str(external_id).strip()
        if system == "wikidata":
            wanted = wanted.rstrip("/").rsplit("/", 1)[-1].removeprefix("Property:").upper()
        elif system == "fibo":
            wanted = fibo_normalize(wanted)
        elif system == "autotype":
            # Test cases are data_release/<name>.txt files; accept the bare name too.
            wanted = wanted.rsplit("/", 1)[-1].removesuffix(".txt")
        elif system == "gs1_ai":
            wanted = wanted.rstrip("/").rsplit("/", 1)[-1].strip("()")
        # D3M writes semantic types as URIs (http://schema.org/email). Also
        # accept https://schema.org/... and a bare type name (FileName, email).
        d3m_bare = system == "d3m" and "://" not in wanted
        if system == "d3m" and wanted.startswith("https://schema.org/"):
            wanted = "http://" + wanted.removeprefix("https://")
        # Sherlock returns labels such as "birth Date"; the paper writes "Birth
        # date". Compare without case and spaces, so "birthDate" matches too.
        if system == "sherlock":
            wanted = _sherlock_key(wanted)
        # Microsoft writes the same Purview type name with varying case and
        # punctuation ("U.S. driver's license number", "U.S. Drivers License Number").
        if system == "purview":
            wanted = _purview_key(wanted)
        if system == "orgid":
            wanted = _orgid_code(wanted)
        if system == "qddate":
            wanted = _qddate_key(wanted)
        if system == "bioregistry":
            wanted = _bioregistry_prefix(wanted)
        if system == "stdnum":
            wanted = _stdnum_module(wanted)
        out = []
        for record in self.datatypes.values():
            value = record.get("mappings", {}).get(system)
            values = value if isinstance(value, list) else [value] if value else []
            if system == "wikidata":
                normalized = [v.upper() for v in values]
            elif system == "sherlock":
                normalized = [_sherlock_key(v) for v in values]
            elif system == "purview":
                normalized = [_purview_key(v) for v in values]
            elif d3m_bare:
                normalized = [v.rsplit("/", 1)[-1] for v in values]
            else:
                normalized = values
            if wanted in normalized:
                out.append(record)
        return out

    def _crosswalk_fta(self, name: str) -> list[dict[str, Any]]:
        # FTA binds <LANGUAGE>, <COUNTRY> and <LOCALE> to the locale of the
        # analysis, so it reports GENDER.TEXT_DE for GENDER.TEXT_<LANGUAGE>.
        # An exact name wins: GENDER.TEXT_JA has its own FTA plugin.
        candidates = [[name]]
        if "_" in name:
            head = name.rsplit("_", 1)[0]
            candidates.append([f"{head}_<{p}>" for p in ("LANGUAGE", "COUNTRY", "LOCALE")])
        for names in candidates:
            out = []
            for record in self.datatypes.values():
                value = record.get("mappings", {}).get("fta")
                values = value if isinstance(value, list) else [value] if value else []
                if any(n in values for n in names):
                    out.append(record)
            if out:
                return out
        return []

"""OpenAPI 3.1 description of the static JSON endpoints."""

from __future__ import annotations

from typing import Any


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def _json_response(description: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "200": {
            "description": description,
            "content": {"application/json": {"schema": schema}},
        },
        "404": {"description": "No such record"},
    }


def _id_param(description: str) -> dict[str, Any]:
    return {
        "name": "id",
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": "string", "pattern": "^[a-z0-9_]+$"},
    }


ID_LIST = {"type": "array", "items": {"type": "string"}}

SCHEMAS: dict[str, Any] = {
    "Example": {
        "type": "object",
        "required": ["value", "valid"],
        "properties": {
            "value": {"type": "string"},
            "description": {"type": "string"},
            "valid": {
                "type": "boolean",
                "description": "false marks a negative example that must not match",
            },
        },
    },
    "Link": {
        "type": "object",
        "required": ["type", "url"],
        "properties": {
            "type": {
                "type": "string",
                "description": "wikipedia, wikidata, schema.org, doc, dublincore, "
                "bioschemas, datadrivendiscovery or other",
            },
            "url": {"type": "string", "format": "uri"},
        },
    },
    "Translation": {
        "type": "object",
        "properties": {"name": {"type": "string"}, "doc": {"type": "string"}},
    },
    "Source": {
        "type": "object",
        "required": ["path", "url", "edit_url"],
        "properties": {
            "path": {"type": "string", "description": "YAML source file in the repository"},
            "url": {"type": "string", "format": "uri"},
            "edit_url": {"type": "string", "format": "uri"},
        },
    },
    "Urls": {
        "type": "object",
        "required": ["html", "json"],
        "properties": {
            "html": {"type": "string", "format": "uri"},
            "json": {"type": "string", "format": "uri"},
        },
    },
    "Datatype": {
        "type": "object",
        "description": "A semantic datatype, or a pattern (one representation of a datatype). "
        "Optional fields are omitted when empty.",
        "required": ["id", "kind", "status", "name", "doc", "is_pii", "quality", "source", "urls"],
        "properties": {
            "id": {"type": "string"},
            "kind": {"type": "string", "enum": ["datatype", "pattern"]},
            "status": {
                "type": "string",
                "enum": ["draft", "stable", "deprecated"],
                "description": "draft: not reviewed yet, do not treat as authoritative",
            },
            "aliases": {**ID_LIST, "description": "Former ids that resolve to this record"},
            "replaced_by": {"type": "string"},
            "checksum": {"type": "string", "description": "Check-digit algorithm name"},
            "quality": {
                "type": "object",
                "required": ["score", "missing"],
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "missing": ID_LIST,
                },
            },
            "name": {"type": "string"},
            "doc": {"type": "string"},
            "semantic_type": {
                "type": "string",
                "description": "For patterns: id of the datatype it represents",
            },
            "parent": {"type": "string", "description": "id of the parent datatype"},
            "children": ID_LIST,
            "patterns": ID_LIST,
            "is_pii": {"type": "boolean"},
            "categories": ID_LIST,
            "country": {**ID_LIST, "description": "ISO 3166-1 alpha-2 codes (EU = region)"},
            "langs": {**ID_LIST, "description": "ISO 639-1 codes; 'common' = any language"},
            "classification": {"type": "string"},
            "regexp": {"type": "string", "description": "Python re syntax"},
            "examples": {"type": "array", "items": _ref("Example")},
            "mappings": {
                "type": "object",
                "description": "Identifiers of the same concept in other vocabularies",
                "properties": {"wikidata": {"type": "string", "pattern": "^[PQ][0-9]+$"}},
                "additionalProperties": {
                    "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
                },
            },
            "links": {"type": "array", "items": _ref("Link")},
            "translations": {
                "type": "object",
                "additionalProperties": _ref("Translation"),
                "description": "Keyed by language code",
            },
            "detected_by": {
                "type": "object",
                "properties": {
                    "tools": ID_LIST,
                    "metacrafter_rules": {
                        "type": "array",
                        "description": "Rules of the pinned metacrafter-rules release",
                        "items": {
                            "type": "object",
                            "required": ["rule", "type", "match", "file"],
                            "properties": {
                                "rule": {"type": "string"},
                                "type": {"type": "string", "description": "field or data"},
                                "match": {"type": "string"},
                                "file": {"type": "string"},
                                "key": {
                                    "type": "string",
                                    "description": "when the rule uses an alias",
                                },
                            },
                        },
                    },
                },
            },
            "source": _ref("Source"),
            "urls": _ref("Urls"),
        },
    },
    "Tool": {
        "type": "object",
        "required": ["id", "name", "category", "doc", "supported_types", "source", "urls"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "category": {"type": "string"},
            "doc": {"type": "string"},
            "website": {"type": "string", "format": "uri"},
            "supported_types": ID_LIST,
            "source": _ref("Source"),
            "urls": _ref("Urls"),
        },
    },
    "Reference": {
        "type": "object",
        "required": ["id", "name", "count"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "count": {"type": "integer", "description": "Datatypes and patterns that use it"},
            "kind": {
                "type": "string",
                "description": "country or region; language or special ('common' = any language)",
            },
            "url": {"type": "string", "format": "uri"},
        },
    },
    "FileInfo": {
        "type": "object",
        "required": ["path", "bytes", "sha256"],
        "properties": {
            "path": {"type": "string"},
            "bytes": {"type": "integer"},
            "sha256": {"type": "string"},
        },
    },
    "Manifest": {
        "type": "object",
        "required": ["name", "version", "datatype_url_template", "counts", "files"],
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"},
            "git_sha": {"type": ["string", "null"]},
            "generated_at": {"type": ["string", "null"], "format": "date-time"},
            "license": {"type": "string"},
            "base_url": {"type": "string", "format": "uri"},
            "datatype_url_template": {"type": "string"},
            "counts": {"type": "object", "additionalProperties": {"type": "integer"}},
            "files": {"type": "object", "additionalProperties": _ref("FileInfo")},
        },
    },
    "LegacyRecord": {
        "type": "object",
        "description": "Release 1.02 shape: categories, country and langs are {id, name} "
        "objects; patterns are embedded objects.",
        "required": ["id", "name", "doc", "type", "is_pii"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "doc": {"type": "string"},
            "type": {"type": "string", "enum": ["datatype", "pattern"]},
            "is_pii": {"type": "boolean"},
        },
        "additionalProperties": True,
    },
}


def build_openapi(site_url: str, version: str) -> dict[str, Any]:
    paths: dict[str, Any] = {
        "/api/v1/index.json": {
            "get": {
                "operationId": "getManifest",
                "summary": "Registry manifest: version, counts, file hashes, URL template",
                "responses": _json_response("Manifest", _ref("Manifest")),
            }
        },
        "/api/v1/datatypes.json": {
            "get": {
                "operationId": "listDatatypes",
                "summary": "All datatypes and patterns",
                "responses": _json_response(
                    "Array of records", {"type": "array", "items": _ref("Datatype")}
                ),
            }
        },
        "/api/v1/datatypes/{id}.json": {
            "get": {
                "operationId": "getDatatype",
                "summary": "One datatype or pattern by id",
                "parameters": [_id_param("Datatype or pattern id, e.g. email")],
                "responses": _json_response("Record", _ref("Datatype")),
            }
        },
        "/api/v1/tools.json": {
            "get": {
                "operationId": "listTools",
                "summary": "All tools",
                "responses": _json_response(
                    "Array of tools", {"type": "array", "items": _ref("Tool")}
                ),
            }
        },
        "/api/v1/tools/{id}.json": {
            "get": {
                "operationId": "getTool",
                "summary": "One tool by id",
                "parameters": [_id_param("Tool id, e.g. presidio")],
                "responses": _json_response("Tool", _ref("Tool")),
            }
        },
    }
    for name, summary in (
        ("categories", "Categories (contexts of use) with record counts"),
        ("countries", "Countries and regions with record counts"),
        ("languages", "Languages with record counts"),
    ):
        paths[f"/api/v1/{name}.json"] = {
            "get": {
                "operationId": "list" + name.capitalize(),
                "summary": summary,
                "responses": _json_response(
                    "Array of references", {"type": "array", "items": _ref("Reference")}
                ),
            }
        }
    paths["/api/v1/aliases.json"] = {
        "get": {
            "operationId": "listAliases",
            "summary": "Retired ids and the canonical id each one resolves to",
            "responses": _json_response(
                "Object: alias -> canonical id",
                {"type": "object", "additionalProperties": {"type": "string"}},
            ),
        }
    }
    paths["/api/v1/coverage.json"] = {
        "get": {
            "operationId": "getCoverage",
            "summary": "metacrafter-rules coverage: datatypes without rules, orphan rule keys",
            "responses": _json_response("Coverage report", {"type": "object"}),
        }
    }
    paths["/registry.json"] = {
        "get": {
            "operationId": "getLegacyRegistry",
            "summary": "Legacy: all records keyed by id (used by metacrafter RegistryClient)",
            "responses": _json_response(
                "Object keyed by id",
                {"type": "object", "additionalProperties": _ref("LegacyRecord")},
            ),
        }
    }
    paths["/datatype/{id}.json"] = {
        "get": {
            "operationId": "getLegacyDatatype",
            "summary": "Legacy: one record in the release 1.02 shape",
            "parameters": [_id_param("Datatype or pattern id")],
            "responses": _json_response("Legacy record", _ref("LegacyRecord")),
        }
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Metacrafter Registry API",
            "version": version,
            "description": "Static, read-only JSON files describing semantic data types. "
            "No authentication, no query parameters.",
            "license": {"name": "Apache-2.0", "identifier": "Apache-2.0"},
        },
        "servers": [{"url": site_url.rstrip("/")}],
        "paths": paths,
        "components": {"schemas": SCHEMAS},
    }

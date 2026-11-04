"""Metacrafter Registry: semantic data types catalog tooling."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("metacrafter-registry")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.0.0+unknown"

DEFAULT_BASE_URL = "https://registry.apicrafter.io"
DATATYPE_URL_TEMPLATE = "{base}/datatype/{id}"

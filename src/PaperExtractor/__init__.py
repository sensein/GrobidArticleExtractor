""".. include:: ../../README.md"""  # noqa: D415

from .app import PaperExtractor

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("PaperExtractor")
except PackageNotFoundError:
    # Package not installed, use fallback version
    __version__ = "0.7.0"

__all__ = ['PaperExtractor', '__version__']

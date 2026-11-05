"""Registry of the ?p=<endpoint> API.

Handler modules in api/ register themselves with @endpoint and load_handlers() imports
every module in the package.
"""
import importlib
import logging
import pkgutil
from collections.abc import Callable, Iterable
from typing import Any

logger = logging.getLogger(__name__)

Query = dict[str, str]
Handler = Callable[[Query], Any]

HANDLERS: dict[str, dict[str, Handler]] = {"GET": {}, "POST": {}}

GET_AND_POST = ("GET", "POST")


def endpoint(name: str, *, methods: Iterable[str] = ("GET",)) -> Callable[[Handler], Handler]:
    """Register the decorated function as the handler for `?p=<name>`."""
    def register(handler: Handler) -> Handler:
        for method in methods:
            if name in HANDLERS[method]:
                raise ValueError(f"{method} {name} is registered twice")
            HANDLERS[method][name] = handler
        return handler

    return register


def query_int(query: Query, name: str, default: int) -> int:
    """Return an integer request parameter, or `default` if it wasn't sent."""
    return int(query.get(name, default))


def load_handlers() -> None:
    """Import every module in api/, which registers the endpoints of the handler modules."""
    import api

    for module in pkgutil.iter_modules(api.__path__):
        importlib.import_module(f"api.{module.name}")

    logger.info("%d GET and %d POST endpoints", len(HANDLERS["GET"]), len(HANDLERS["POST"]))

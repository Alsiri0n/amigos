import logging
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_logging(_: "Application"):
    logging.basicConfig(level=logging.INFO)

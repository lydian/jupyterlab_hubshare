from .handlers import setup_handlers
import json
from pathlib import Path

from ._version import __version__  # noqa

HERE = Path(__file__).parent.resolve()

with (HERE / "labextension" / "package.json").open() as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]


def _jupyter_server_extension_points():
    return [{"module": "jupyterlab_hubshare"}]


def _load_jupyter_server_extension(server_app):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    setup_handlers(server_app.web_app)
    server_app.log.info(
        "Registered Jupytelab_hubshare extension at URL path /jupyterlab_hubshare"
    )


# For backward compatibility
load_jupyter_server_extension = _load_jupyter_server_extension

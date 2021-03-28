import os
import sys

from simplespawner import SimpleLocalProcessSpawner

c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"
c.JupyterHub.bind_url = "http://127.0.0.1:8000"
c.JupyterHub.spawner_class = SimpleLocalProcessSpawner
c.SimpleLocalProcessSpawner.home_path_template = "/tmp/{username}"
c.SimpleLocalProcessSpawner.debug = True
c.SimpleLocalProcessSpawner.default_url = "/lab"

c.SimpleLocalProcessSpawner.cmd = [
    os.path.join(os.path.dirname(sys.executable), "jupyter-labhub")
]
c.SimpleLocalProcessSpawner.args = [
    "--debug",
    f"--config={os.getcwd()}/singleuser_config.py",
]

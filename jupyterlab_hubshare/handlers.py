import datetime
import os
import json
import logging
import urllib.parse
from importlib import import_module

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import nbformat
import tornado
from IPython.html.base.handlers import IPythonHandler
from nbconvert import HTMLExporter


def create_manager(cls_or_path, kwargs):
    if isinstance(cls_or_path, str):
        module_name, cls_name = cls_or_path.rsplit(".", 1)
        module = import_module(module_name)
        cls_ = getattr(module, cls_name)
    else:
        cls_ = cls_or_path
    return cls_(**kwargs)


class BaseMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub_share_config = self.config.get("HubShare", {})
        cm_config = self.hub_share_config.get("contents_manager")
        self._cm = (
            create_manager(cm_config["manager_cls"], cm_config.get("kwargs", {}))
            if cm_config
            else self.contents_manager
        )
        logging.info(f"Register contents manager: {type(self._cm)}")

    def get_notebook(self, path):
        if not self._cm.file_exists(path):
            raise tornado.web.HTTPError(404, reason="File Not Found")
        if path.rsplit(".", 1)[-1].lower() != "ipynb":
            raise tornado.web.HTTPError(400, reason="Not ipynb File")
        return self._cm.get(path, content=True)

    def to_json(self, content):
        def convert_dt(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()

        return json.dumps(content, default=convert_dt)


def get_share_path(path_template, data):
    def replace_pattern(pattern):
        replace_kwargs = {}
        if "{path}" in pattern:
            replace_kwargs["path"] = data["path"]
        if "{user}" in pattern:
            replace_kwargs["user"] = os.environ["JUPYTERHUB_USER"]
        if replace_kwargs:
            pattern = pattern.format(**replace_kwargs)
        return pattern

    output = {
        key: replace_pattern(path_template.get(key, "")) for key in ["base_url", "path"]
    }
    path = output["base_url"].rstrip("/") + output["path"]
    if "qs" in path_template:
        path += "?" + "&".join(
            "{}={}".format(key, urllib.parse.quote(replace_pattern(value)))
            for key, value in path_template["qs"].items()
        )
    return path


class ShareURLHandler(BaseMixin, APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def put(self):
        path_template = self.hub_share_config.get("share_url_template", {})
        data = json.loads(self.request.body)
        path = get_share_path(path_template, data)
        self.finish(json.dumps({"share_path": path}))


class ContentHandler(BaseMixin, APIHandler):
    @tornado.web.authenticated
    def put(self):
        data = json.loads(self.request.body)
        path = data.get("path", None)
        self.finish(self.to_json(self.get_notebook(path)))


class PreviewHandler(BaseMixin, IPythonHandler):
    @tornado.web.authenticated
    def get(self):
        path = self.get_argument("path")
        html_exporter = HTMLExporter()
        html_exporter.template_name = "classic"
        notebook_node = nbformat.from_dict(self.get_notebook(path).get("content", {}))
        html, _ = html_exporter.from_notebook_node(notebook_node)
        self.finish(html)


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = url_path_join(web_app.settings["base_url"], "jupyterlab_hubshare")
    route_to_handler = {
        "share-url": ShareURLHandler,
        "content": ContentHandler,
        "preview": PreviewHandler,
    }
    handlers = [
        (url_path_join(base_url, route), handler)
        for route, handler in route_to_handler.items()
    ]
    web_app.add_handlers(host_pattern, handlers)

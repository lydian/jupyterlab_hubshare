import datetime
import os
import json
import logging
import base64
import urllib.parse
from importlib import import_module

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import nbformat
import tornado
from notebook.base.handlers import IPythonHandler
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

    def get_info(self, path):
        decoded_path = base64.b64decode(path).decode("utf-8")
        if not self._cm.file_exists(decoded_path) and not self._cm.dir_exists(
            decoded_path
        ):
            raise tornado.web.HTTPError(404, reason=f"Path: {base64.decode} not Found")
        return self._cm.get(decoded_path, content=False)

    def get_notebook(self, path):
        decoded_path = base64.b64decode(path).decode("utf-8")
        if not self._cm.file_exists(decoded_path):
            raise tornado.web.HTTPError(404, reason="File Not Found")
        if decoded_path.rsplit(".", 1)[-1].lower() != "ipynb":
            raise tornado.web.HTTPError(400, reason="Not ipynb File")
        return self._cm.get(decoded_path, content=True)

    def to_json(self, content):
        def convert_dt(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()

        return json.dumps(content, default=convert_dt)


def get_share_path(
    use_jupyterhub_redirect, use_preview, base_url, path_template, path_func, data
):

    if path_func:
        output_path = path_func(data["path"])
    else:
        output_path = path_template.format(
            user=os.environ.get("JUPYTERHUB_USER"), path=data["path"]
        )
    if use_preview:
        output_path = urllib.parse.quote(base64.b64encode(output_path.encode("utf-8")))
    url = "/user-redirect/" if use_jupyterhub_redirect else "/"
    url += (
        f"?hubshare-preview={output_path}" if use_preview else f"lab/tree/{output_path}"
    )
    if base_url:
        url = base_url.rstrip("/") + url
    return url


class ShareURLHandler(BaseMixin, APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def put(self):
        path_template = self.hub_share_config.get("file_path_template", "{path}")
        path_func = self.hub_share_config.get("file_path_func", None)
        use_jupyterhub_redirect = self.hub_share_config.get(
            "use_jupyterhub_redirect", True
        )
        use_preview = self.hub_share_config.get("use_preview", True)
        base_url = self.hub_share_config.get("base_url", None)
        data = json.loads(self.request.body)
        path = get_share_path(
            use_jupyterhub_redirect,
            use_preview,
            base_url,
            path_template,
            path_func,
            data,
        )
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


class ShareInfoHandler(BaseMixin, APIHandler):
    @tornado.web.authenticated
    def put(self):
        path = self.get_argument("path")
        self.finish(self.to_json(self.get_info(path)))


class GetOtherLinksHander(BaseMixin, APIHandler):
    def get(self):
        self.finish(
            self.to_json(
                {
                    "other_links": [
                        {"id": key, "label": value["label"]}
                        for key, value in self.hub_share_config.get(
                            "other_link_functions", {}
                        ).items()
                    ]
                }
            )
        )

    def post(self):
        data = json.loads(self.request.body)
        func = getattr(self.hub_share_config, "other_link_functions", {})[data["id"]][
            "path_func"
        ]
        self.finish(self.to_json({"id": data["id"], "path": func(data["path"])}))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = url_path_join(web_app.settings["base_url"], "jupyterlab_hubshare")
    route_to_handler = {
        "share-url": ShareURLHandler,
        "content": ContentHandler,
        "preview": PreviewHandler,
        "info": ShareInfoHandler,
        "other-link": GetOtherLinksHander,
    }
    handlers = [
        (url_path_join(base_url, route), handler)
        for route, handler in route_to_handler.items()
    ]
    web_app.add_handlers(host_pattern, handlers)

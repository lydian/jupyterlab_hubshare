from IPython.html.services.contents.filemanager import FileContentsManager

c.ServerApp.jpserver_extensions = {"jupyterlab_hubshare": True}
c.HubShare.share_url_template = {
    "base_url": "",
    "path": "/user-redirect/",
    "qs": {"from": "share", "path": "{user}/{path}"},
}
c.HubShare.contents_manager = {
    "manager_cls": FileContentsManager,
    "kwargs": {"root_dir": "/tmp/"},
}

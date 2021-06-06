from IPython.html.services.contents.filemanager import FileContentsManager

c.ServerApp.jpserver_extensions = {"jupyterlab_hubshare": True}
c.FileContentsManager.root_dir = "/tmp"
c.HubShare.file_path_template = "{path}"
c.HubShare.use_preview = False
c.HubShare.contents_manager = {
    "manager_cls": FileContentsManager,
    "kwargs": {"root_dir": "/tmp/"},
}

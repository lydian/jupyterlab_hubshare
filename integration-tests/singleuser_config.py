from IPython.html.services.contents.filemanager import FileContentsManager

c.ServerApp.jpserver_extensions = {"jupyterlab_hubshare": True}
c.HubShare.file_path_template = "{user}/{path}"
c.HubShare.contents_manager = {
    "manager_cls": FileContentsManager,
    "kwargs": {"root_dir": "/tmp/"},
}

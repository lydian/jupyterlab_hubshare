from IPython.html.services.contents.filemanager import FileContentsManager

c.ServerApp.jpserver_extensions = {"jupyterlab_hubshare": True}
c.HubShare.file_path_template = "{path}"
# c.HubShare.file_path_func = lambda path: f"my/new/{path}" if path.startswith(
#    "1st template/") else path
c.HubShare.use_jupyterhub_redirect = False
c.HubShare.other_link_functions = {
    "view-only": {
        "label": "View Only URL",
        "path_func": lambda path: f"https://github.com/test/repo/{path}",
    },
    "testing": {
        "label": "Test Run URL",
        "path_func": lambda path: f"http://example.com/testing?path={path}",
    },
}

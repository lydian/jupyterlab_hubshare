import datetime
from unittest import mock

import tornado
import pytest
from jupyter_server.services.contents.filemanager import FileContentsManager

from jupyterlab_hubshare.handlers import create_manager
from jupyterlab_hubshare.handlers import BaseMixin
from jupyterlab_hubshare.handlers import get_share_path


@pytest.mark.parametrize(
    "cls_name",
    [
        "jupyter_server.services.contents.filemanager.FileContentsManager",
        FileContentsManager,
    ],
)
def test_create_manager(cls_name):
    kwargs = {"root_dir": "/tmp"}
    manager = create_manager(cls_name, kwargs)

    assert isinstance(manager, FileContentsManager)
    assert manager.root_dir == "/tmp"


class DummyCls(object):
    def __init__(self, config=None):
        self.config = config or {}
        self.contents_manager = mock.Mock()


class DummyHandler(BaseMixin, DummyCls):
    pass


class TestBaseMixin(object):
    @pytest.fixture
    def mock_create_manager(self):
        with mock.patch("jupyterlab_hubshare.handlers.create_manager") as m:
            yield m

    @pytest.mark.parametrize(
        "config,use_internal_cm",
        [
            # didn't configure manager, use built-in
            ({}, True),
            # self defined contents manager
            ({"contents_manager": {"manager_cls": "test_cls"}}, False),
        ],
    )
    def test_init(self, config, use_internal_cm, mock_create_manager):
        dummy_handler = DummyHandler(config={"HubShare": config})
        assert dummy_handler.hub_share_config == config
        if use_internal_cm:
            assert dummy_handler._cm == dummy_handler.contents_manager
        else:
            assert dummy_handler._cm == mock_create_manager.return_value

    @pytest.fixture
    def dummy_handler(self):
        dummy_handler = DummyHandler()
        dummy_handler._cm = mock.Mock()
        return dummy_handler

    def test_get_notebook_file_not_found(self, dummy_handler):
        dummy_handler._cm.file_exists.return_value = False
        with pytest.raises(tornado.web.HTTPError):
            dummy_handler.get_notebook("/path/to/notebook.ipynb")

    def test_get_notebook_wrong_file_type(self, dummy_handler):
        with pytest.raises(tornado.web.HTTPError):
            dummy_handler.get_notebook("/path/to/some")

    def test_get_notebook_success(self, dummy_handler):
        fake_content = {"name": "notebook.ipynb"}
        dummy_handler._cm.get.return_value = fake_content

        assert dummy_handler.get_notebook("/path/to/notebook.ipynb") == fake_content

    def test_to_json(self, dummy_handler):
        assert (
            dummy_handler.to_json({"dt": datetime.datetime(2021, 2, 3, 4, 5, 6)})
            == '{"dt": "2021-02-03T04:05:06"}'
        )


@pytest.mark.parametrize(
    "template,expected_output",
    [
        # replace in path
        (
            {"path": "/user-redirect/{user}/{path}"},
            "/user-redirect/test_user/path/to/file",
        ),
        ({"path": "/user-redirect/{path}"}, "/user-redirect/path/to/file"),
        # replace in query string
        (
            {"path": "/user-redirect/", "qs": {"share-path": "{user}/{path}"}},
            "/user-redirect/?share-path=test_user/path/to/file",
        ),
    ],
)
def test_get_share_path(template, expected_output, monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_USER", "test_user")
    assert get_share_path(template, {"path": "path/to/file"}) == expected_output

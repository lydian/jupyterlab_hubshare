import base64
import datetime
import urllib.parse
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
        encoded_path = base64.b64encode("/path/to/notebook.ipynb".encode("utf-8"))
        dummy_handler._cm.file_exists.return_value = False
        with pytest.raises(tornado.web.HTTPError):
            dummy_handler.get_notebook(encoded_path)

    def test_get_notebook_wrong_file_type(self, dummy_handler):
        encoded_path = base64.b64encode("/path/to/someformat".encode("utf-8"))
        with pytest.raises(tornado.web.HTTPError):
            dummy_handler.get_notebook(encoded_path)

    def test_get_notebook_success(self, dummy_handler):
        encoded_path = base64.b64encode("/path/to/notebook.ipynb".encode("utf-8"))
        fake_content = {"name": "notebook.ipynb"}
        dummy_handler._cm.get.return_value = fake_content

        assert dummy_handler.get_notebook(encoded_path) == fake_content

    def test_to_json(self, dummy_handler):
        assert (
            dummy_handler.to_json({"dt": datetime.datetime(2021, 2, 3, 4, 5, 6)})
            == '{"dt": "2021-02-03T04:05:06"}'
        )


@pytest.mark.parametrize(
    "use_jupyterhub_redirect,expected_first_url_component",
    [(True, "/user-redirect/"), (False, "/")],
)
@pytest.mark.parametrize(
    "use_preview,expected_second_url_component",
    [(True, "?hubshare-preview={FINAL_PATH}"), (False, "{FINAL_PATH}")],
)
@pytest.mark.parametrize(
    "path_template,input_path,expected_file_path",
    [
        ("{path}", "path/to/file", "path/to/file"),
        ("{user}/{path}", "path/to/file", "test_user/path/to/file"),
    ],
)
@pytest.mark.parametrize(
    "base_url", ["", "https://example.com/", "https://example.com"]
)
def test_get_share_path(
    use_jupyterhub_redirect,
    use_preview,
    base_url,
    path_template,
    input_path,
    expected_first_url_component,
    expected_second_url_component,
    expected_file_path,
    monkeypatch,
):
    monkeypatch.setenv("JUPYTERHUB_USER", "test_user")
    if use_preview:
        expected_file_path = urllib.parse.quote(
            base64.b64encode(expected_file_path.encode("utf-8"))
        )

    expected_final_path = (
        expected_first_url_component
        + expected_second_url_component.format(FINAL_PATH=expected_file_path)
    )
    if base_url:
        expected_final_path = "https://example.com" + expected_final_path
    assert (
        get_share_path(
            use_jupyterhub_redirect,
            use_preview,
            base_url,
            path_template,
            {"path": input_path},
        )
        == expected_final_path
    )

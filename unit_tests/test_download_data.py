"""Unit tests for the download_data module."""

from unittest.mock import Mock

import pytest

from ia700_project import download_data as download_module


def test_download_data_success(monkeypatch, tmp_path):
    """Test successful download and file creation."""
    output_file = tmp_path / "data" / "dataset.csv"
    monkeypatch.setattr(
        download_module,
        "TGV_REGULARITY_PATH",
        str(output_file),
    )

    response = Mock()
    response.content = b"col1;col2\nvalue1;value2"

    get_mock = Mock(return_value=response)
    monkeypatch.setattr(download_module.requests, "get", get_mock)

    download_module.download_data()

    get_mock.assert_called_once_with(
        download_module.TGV_REGULARITY_URL,
        timeout=30,
    )
    response.raise_for_status.assert_called_once()
    assert output_file.exists()
    assert output_file.read_bytes() == response.content


def test_download_data_http_error(monkeypatch, tmp_path):
    """Test that HTTP errors are propagated."""
    output_file = tmp_path / "data" / "dataset.csv"
    monkeypatch.setattr(
        download_module,
        "TGV_REGULARITY_PATH",
        str(output_file),
    )

    response = Mock()
    response.raise_for_status.side_effect = download_module.requests.HTTPError(
        "HTTP error"
    )

    monkeypatch.setattr(
        download_module.requests,
        "get",
        Mock(return_value=response),
    )

    with pytest.raises(download_module.requests.HTTPError):
        download_module.download_data()

    assert not output_file.exists()


def test_download_data_request_error(monkeypatch):
    """Test that request errors are propagated."""
    monkeypatch.setattr(
        download_module.requests,
        "get",
        Mock(
            side_effect=download_module.requests.ConnectionError(
                "Connection error"
            )
        ),
    )

    with pytest.raises(download_module.requests.ConnectionError):
        download_module.download_data()

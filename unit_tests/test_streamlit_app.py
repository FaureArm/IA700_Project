"""Unit tests for the streamlit_app module."""

from unittest.mock import Mock

import pandas as pd
import pytest

from ia700_project import streamlit_app


class StopExecution(Exception):
    """Simulate Streamlit stopping the application."""


def prepare_streamlit_mocks(monkeypatch):
    """Prepare Streamlit mocks for testing."""
    monkeypatch.setattr(streamlit_app.st, "set_page_config", Mock())
    monkeypatch.setattr(streamlit_app.st.sidebar, "title", Mock())
    monkeypatch.setattr(streamlit_app.st, "error", Mock())
    monkeypatch.setattr(streamlit_app.st, "info", Mock())
    monkeypatch.setattr(streamlit_app.st, "warning", Mock())

    def stop():
        raise StopExecution

    monkeypatch.setattr(streamlit_app.st, "stop", stop)


def test_main_success(monkeypatch, tmp_path):
    """Test successful application startup and page navigation."""
    prepare_streamlit_mocks(monkeypatch)

    data_file = tmp_path / "data.csv"
    data_file.write_text("test", encoding="utf-8")
    monkeypatch.setattr(streamlit_app, "DATA_PATH", data_file)

    data = pd.DataFrame({"value": [1, 2]})
    monkeypatch.setattr(
        streamlit_app,
        "load_data",
        Mock(return_value=data),
    )

    # Mock page functions before creating navigation pages.
    main_page_mock = Mock()
    exploration_page_mock = Mock()
    comparison_page_mock = Mock()
    methods_page_mock = Mock()

    monkeypatch.setattr(streamlit_app, "main_page", main_page_mock)
    monkeypatch.setattr(
        streamlit_app, "exploration_page", exploration_page_mock
    )
    monkeypatch.setattr(streamlit_app, "comparison_page", comparison_page_mock)
    monkeypatch.setattr(streamlit_app, "methods_page", methods_page_mock)

    created_pages = []

    def fake_page(function, title, default=False):
        page = Mock()
        page.function = function
        page.title = title
        page.default = default
        created_pages.append(page)
        return page

    navigation = Mock()
    navigation_page = Mock()
    navigation.return_value = navigation_page

    monkeypatch.setattr(streamlit_app.st, "Page", fake_page)
    monkeypatch.setattr(streamlit_app.st, "navigation", navigation)

    streamlit_app.main()

    streamlit_app.st.set_page_config.assert_called_once_with(
        page_title="RailInsight · Régularité TGV",
        page_icon="🚆",
        layout="wide",
    )
    streamlit_app.st.sidebar.title.assert_called_once_with(streamlit_app.TITLE)

    streamlit_app.load_data.assert_called_once_with(
        str(data_file),
        data_file.stat().st_mtime_ns,
    )

    assert len(created_pages) == 4
    assert [page.title for page in created_pages] == [
        "Accueil",
        "Explorer une liaison",
        "Comparer les liaisons",
        "Données et méthodes",
    ]
    assert created_pages[0].default is True

    navigation.assert_called_once_with(
        created_pages,
        position="top",
    )
    navigation_page.run.assert_called_once()

    # Execute each page callback to test the nested functions.
    for page in created_pages:
        page.function()

    main_page_mock.assert_called_once_with(data)
    exploration_page_mock.assert_called_once_with(data)
    comparison_page_mock.assert_called_once_with(data)
    methods_page_mock.assert_called_once_with()


def test_main_file_not_found(monkeypatch, tmp_path):
    """Test handling of a missing dataset."""
    prepare_streamlit_mocks(monkeypatch)

    missing_file = tmp_path / "missing.csv"
    monkeypatch.setattr(streamlit_app, "DATA_PATH", missing_file)

    load_data = Mock(side_effect=FileNotFoundError)
    monkeypatch.setattr(streamlit_app, "load_data", load_data)

    with pytest.raises(StopExecution):
        streamlit_app.main()

    streamlit_app.st.error.assert_called_once_with(
        "Le jeu de données SNCF est absent."
    )
    streamlit_app.st.info.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        OSError("Disk error"),
        ValueError("Invalid data"),
    ],
)
def test_main_data_loading_error(monkeypatch, tmp_path, error):
    """Test handling of data loading errors."""
    prepare_streamlit_mocks(monkeypatch)

    data_file = tmp_path / "data.csv"
    data_file.write_text("test", encoding="utf-8")
    monkeypatch.setattr(streamlit_app, "DATA_PATH", data_file)

    monkeypatch.setattr(
        streamlit_app,
        "load_data",
        Mock(side_effect=error),
    )

    with pytest.raises(StopExecution):
        streamlit_app.main()

    streamlit_app.st.error.assert_called_once_with(
        f"Impossible de préparer les données SNCF : {error}"
    )


def test_main_empty_data(monkeypatch, tmp_path):
    """Test handling of an empty dataset."""
    prepare_streamlit_mocks(monkeypatch)

    data_file = tmp_path / "data.csv"
    data_file.write_text("test", encoding="utf-8")
    monkeypatch.setattr(streamlit_app, "DATA_PATH", data_file)

    monkeypatch.setattr(
        streamlit_app,
        "load_data",
        Mock(return_value=pd.DataFrame()),
    )

    with pytest.raises(StopExecution):
        streamlit_app.main()

    streamlit_app.st.warning.assert_called_once_with(
        "Le fichier ne contient aucune observation exploitable."
    )

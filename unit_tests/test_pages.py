"""Unit tests for the pages module."""

from unittest.mock import Mock

import pandas as pd

from ia700_project import pages


def test_main_page(monkeypatch):
    """Test the home page rendering."""
    data = pd.DataFrame({"value": [1, 2]})
    title = Mock()
    markdown = Mock()
    caption = Mock()
    dashboard = Mock()

    monkeypatch.setattr(pages.st, "title", title)
    monkeypatch.setattr(pages.st, "markdown", markdown)
    monkeypatch.setattr(pages.st, "caption", caption)
    monkeypatch.setattr(pages, "render_overview_dashboard", dashboard)

    pages.main_page(data)

    title.assert_called_once_with("Accueil")
    assert markdown.call_count == 1
    caption.assert_called_once()
    dashboard.assert_called_once_with(data)


def test_exploration_page(monkeypatch):
    """Test the exploration page rendering."""
    data = pd.DataFrame({"value": [1, 2]})
    selection = object()

    title = Mock()
    markdown = Mock()
    caption = Mock()
    sidebar = Mock(return_value=selection)
    dashboard = Mock()

    monkeypatch.setattr(pages.st, "title", title)
    monkeypatch.setattr(pages.st, "markdown", markdown)
    monkeypatch.setattr(pages.st, "caption", caption)
    monkeypatch.setattr(pages, "date_itinerary_sidebar", sidebar)
    monkeypatch.setattr(pages, "render_exploration_dashboard", dashboard)

    pages.exploration_page(data)

    title.assert_called_once_with("Explorer une liaison")
    assert markdown.call_count == 1
    caption.assert_called_once()
    sidebar.assert_called_once_with(data)
    dashboard.assert_called_once_with(data, selection)


def test_comparison_page(monkeypatch):
    """Test the comparison page rendering."""
    data = pd.DataFrame({"value": [1, 2]})
    selection = object()

    title = Mock()
    markdown = Mock()
    sidebar = Mock(return_value=selection)
    dashboard = Mock()

    monkeypatch.setattr(pages.st, "title", title)
    monkeypatch.setattr(pages.st, "markdown", markdown)
    monkeypatch.setattr(pages, "comparison_sidebar", sidebar)
    monkeypatch.setattr(pages, "render_comparison_dashboard", dashboard)

    pages.comparison_page(data)

    title.assert_called_once_with("Comparer les liaisons")
    assert markdown.call_count == 1
    sidebar.assert_called_once_with()
    dashboard.assert_called_once_with(data, selection)


def test_methods_page(monkeypatch):
    """Test the methods page rendering."""
    title = Mock()
    monkeypatch.setattr(pages.st, "title", title)

    result = pages.methods_page()

    title.assert_called_once_with("Données et méthodes")
    assert result is None

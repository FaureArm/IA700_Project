"""Unit tests for the map view module."""

import gzip
import json

from ia700_project import map_view


def test_load_map_data_reads_and_decompresses_geojson(tmp_path) -> None:
    """Check that map routes and coverage are correctly loaded."""
    geojson = {
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "route_id": "route_1",
                    "departure": "Paris",
                    "arrival": "Lyon",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[2.0, 48.0], [4.0, 45.0]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "route_id": "route_2",
                    "departure": "Lille",
                    "arrival": "Nice",
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [[3.0, 50.0], [4.0, 49.0]],
                        [[4.0, 49.0], [7.0, 43.0]],
                    ],
                },
            },
        ]
    }

    report = {"coverage": {"routes": 2}}

    (tmp_path / "report.json").write_text(
        json.dumps(report),
        encoding="utf-8",
    )
    (tmp_path / "liaisons.geojson.gz").write_bytes(
        gzip.compress(json.dumps(geojson).encode("utf-8"))
    )

    routes, coverage = map_view.load_map_data(tmp_path, (1, 2))

    assert len(routes) == 2
    assert coverage == {"routes": 2}

    assert routes[0]["route_id"] == "route_1"
    assert routes[0]["paths"] == [[[2.0, 48.0], [4.0, 45.0]]]

    assert routes[1]["route_id"] == "route_2"
    assert routes[1]["paths"] == [
        [[3.0, 50.0], [4.0, 49.0]],
        [[4.0, 49.0], [7.0, 43.0]],
    ]


def test_percentage_label_formats_percentage() -> None:
    """Check that fractions are converted into percentage labels."""
    assert map_view.percentage_label(0.125) == "12,5 %"
    assert map_view.percentage_label(0) == "0,0 %"
    assert map_view.percentage_label(1) == "100,0 %"


def test_rate_color_returns_black_for_missing_rate() -> None:
    """Check that missing rates are represented in black."""
    result = map_view.rate_color(
        None,
        map_view.RATE_SCALES["delay"],
    )

    assert result == map_view.MISSING_COLOR


def test_rate_color_returns_first_color_for_low_rate() -> None:
    """Check that low rates use the first color."""
    result = map_view.rate_color(
        0.0,
        map_view.RATE_SCALES["delay"],
    )

    assert result == map_view.RATE_COLORS[0]


def test_rate_color_returns_middle_color_at_middle_threshold() -> None:
    """Check that the middle threshold uses the amber color."""
    result = map_view.rate_color(
        0.20,
        map_view.RATE_SCALES["delay"],
    )

    assert result == map_view.RATE_COLORS[1]


def test_rate_color_returns_last_color_for_high_rate() -> None:
    """Check that high rates use the last color."""
    result = map_view.rate_color(
        0.30,
        map_view.RATE_SCALES["delay"],
    )

    assert result == map_view.RATE_COLORS[2]


def test_route_tooltip_includes_both_directions() -> None:
    """Check that the tooltip displays rates in both route directions."""
    route = {
        "departure": "Paris",
        "arrival": "Lyon",
    }
    pairs = {
        ("Paris", "Lyon"),
        ("Lyon", "Paris"),
    }
    rates = {
        ("Paris", "Lyon"): {
            "delay": 0.10,
            "cancellation": 0.05,
        },
        ("Lyon", "Paris"): {
            "delay": 0.20,
            "cancellation": 0.03,
        },
    }

    result = map_view.route_tooltip(route, pairs, rates)

    assert "Paris → Lyon" in result
    assert "Lyon → Paris" in result
    assert "Retards à l’arrivée 10,0 %" in result
    assert "Annulations 5,0 %" in result
    assert "Retards à l’arrivée 20,0 %" in result
    assert "Annulations 3,0 %" in result


def test_route_tooltip_handles_missing_rates() -> None:
    """Check that unavailable rates are displayed correctly."""
    route = {
        "departure": "Paris",
        "arrival": "Lyon",
    }
    pairs = {("Paris", "Lyon")}
    rates = {}

    result = map_view.route_tooltip(route, pairs, rates)

    assert "Paris → Lyon" in result
    assert "Données indisponibles" in result


def test_route_tooltip_handles_missing_metric() -> None:
    """Check that a missing metric is replaced by a dash."""
    route = {
        "departure": "Paris",
        "arrival": "Lyon",
    }
    pairs = {("Paris", "Lyon")}
    rates = {
        ("Paris", "Lyon"): {
            "delay": 0.10,
        }
    }

    result = map_view.route_tooltip(route, pairs, rates)

    assert "Retards à l’arrivée 10,0 %" in result
    assert "Annulations —" in result


def test_route_tooltip_does_not_duplicate_loop_route() -> None:
    """Check that a route returning to the same station appears once."""
    route = {
        "departure": "Paris",
        "arrival": "Paris",
    }
    pairs = {("Paris", "Paris")}
    rates = {}

    result = map_view.route_tooltip(route, pairs, rates)

    assert result.count("Paris → Paris") == 1


def test_render_rate_legend_without_rates(monkeypatch) -> None:
    """Check that the missing-data message is displayed."""
    messages = []

    monkeypatch.setattr(
        map_view.st,
        "caption",
        lambda message: messages.append(message),
    )

    map_view.render_rate_legend(
        map_view.RATE_SCALES["delay"],
        False,
    )

    assert len(messages) == 1
    assert "données indisponibles" in messages[0]


def test_render_rate_legend_with_rates(monkeypatch) -> None:
    """Check that the color legend is rendered when rates exist."""
    html_content = []

    monkeypatch.setattr(
        map_view.st,
        "html",
        lambda content: html_content.append(content),
    )

    map_view.render_rate_legend(
        map_view.RATE_SCALES["delay"],
        True,
    )

    assert len(html_content) == 1
    assert "Retards" not in html_content[0]
    assert "12,0 %" in html_content[0]
    assert "20,0 %" in html_content[0]
    assert "30,0 %" in html_content[0]
    assert "données indisponibles" in html_content[0]

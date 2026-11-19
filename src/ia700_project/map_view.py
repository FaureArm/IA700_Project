"""Render the interactive TGV route map."""

import gzip
import json
from pathlib import Path
from zlib import error as ZlibError

import pydeck as pdk
import streamlit as st

from ia700_project.data import DATA_PATH
from ia700_project.map_rates import load_map_rates
from ia700_project.sidebar import map_metric_sidebar, map_route_sidebar

## CONSANTS ##
MAP_DATA = Path(__file__).resolve().parents[2] / "data" / "map"
MAP_METRICS = {
    "disruption": "Perturbations",
    "delay": "Retards à l’arrivée",
    "cancellation": "Annulations",
}
HOVER_METRICS = ("delay", "cancellation")
# Green, amber and red anchors stay the same when we filter the map
RATE_SCALES = {
    "disruption": (0.15, 0.23, 0.35),
    "delay": (0.12, 0.20, 0.30),
    "cancellation": (0.03, 0.05, 0.08),
}
RATE_COLORS = ((26, 116, 67), (190, 119, 16), (186, 37, 52))
MISSING_COLOR = (0, 0, 0)

##


@st.cache_data(show_spinner=False)
def load_map_data(
    directory: Path, modified_at: tuple[int, int]
) -> tuple[list[dict], dict]:
    """Load the saved routes and coverage from the same preprocessing build.

    Args:
        directory: Folder with the compressed GeoJSON and its report
        modified_at: Both file timestamps, used to refresh the cache on rebuild

    Returns:
        Routes with a list of drawable paths each, and the coverage counts
    """
    # load our map data
    # NB: we only generated this data once, no point in keeping the scrips
    # used to generate or running them again given the nature of our data
    report = json.loads(
        (directory / "report.json").read_text(encoding="utf-8")
    )
    payload = gzip.decompress((directory / "liaisons.geojson.gz").read_bytes())
    routes = []
    for feature in json.loads(payload)["features"]:
        geometry = feature["geometry"]
        coordinates = geometry["coordinates"]
        # give Pydeck a list of separate lines for each liaison
        paths = (
            coordinates
            if geometry["type"] == "MultiLineString"
            else [coordinates]
        )
        routes.append({**feature["properties"], "paths": paths})
    return routes, report["coverage"]


def percentage_label(rate: float) -> str:
    """Format a fraction as a percentage for the UI."""
    return f"{100 * rate:.1f}".replace(".", ",") + " %"


def rate_color(
    rate: float | None, scale: tuple[float, float, float]
) -> tuple[int, ...]:
    """Blend between the 3 base colours, or return black for a missing rate."""
    if rate is None:
        return MISSING_COLOR  # see constants
    step = int(rate >= scale[1])
    low, high = scale[step : step + 2]
    fraction = max(0, min(1, (rate - low) / (high - low)))
    return tuple(
        round(a + fraction * (b - a))
        for a, b in zip(RATE_COLORS[step], RATE_COLORS[step + 1])
    )


def route_tooltip(
    route: dict, pairs: set[tuple[str, str]], rates: dict
) -> str:
    """Show perturbations in both directions when hovering a map route."""
    pair = route["departure"], route["arrival"]
    directions = [pair]
    # check if the reverse direction exists and is not a loop then add it
    if pair[::-1] in pairs and pair[::-1] != pair:
        directions.append(pair[::-1])
    lines = []
    # collect our values for perturbations
    for departure, arrival in directions:
        lines.append(f"{departure} → {arrival}")
        values = rates.get((departure, arrival), {})
        if any(key in values for key in HOVER_METRICS):
            lines.append(
                " · ".join(
                    f"{MAP_METRICS[key]} {
                        percentage_label(values[key]) if key in values else '—'
                    }"
                    for key in HOVER_METRICS
                )
            )
        else:
            lines.append("Données indisponibles")
    return "\n".join(lines)


def render_rate_legend(
    scale: tuple[float, float, float], has_rates: bool
) -> None:
    """Function to colour our routes."""
    if not has_rates:
        st.caption("Noir · données indisponibles pour cet indicateur.")
        return
    marks = "".join(
        '<span style="white-space:nowrap">'
        '<span aria-hidden="true" style="display:inline-block;'
        "width:.65rem;height:.65rem;border-radius:50%;"
        f'background:rgb{color}"></span> '
        f"{prefix}{percentage_label(rate)}</span>"
        for rate, color, prefix in zip(scale, RATE_COLORS, ("≤ ", "", "≥ "))
    )
    st.html(
        '<div style="display:flex;align-items:center;flex-wrap:wrap;'
        'gap:.75rem;font-size:.875rem">'
        f"{marks}<span>· Noir si données indisponibles</span></div>"
    )


def render_tgv_map() -> None:
    """Join the saved paths to their AQST rates and draw the overview map."""
    ## Load the prepared map ##
    # NB: Streamlit reads the map build output here
    try:
        files = (MAP_DATA / "liaisons.geojson.gz", MAP_DATA / "report.json")
        routes, _ = load_map_data(
            MAP_DATA, tuple(path.stat().st_mtime_ns for path in files)
        )
    except FileNotFoundError:
        st.info("Données de la carte absentes.")
        return
    # just in case for any other error, so we dont crash the app
    except (OSError, ValueError, KeyError, EOFError, ZlibError):
        st.warning("Données de la carte illisibles.")
        return
    if not routes:
        return
    st.caption(
        "Tracés reconstitués. "
        "Sources: SNCF, Train Nomade, OpenStreetMap, IGN Espagne et ERA."
    )
    ## Sidebar and rates/values ##
    metric = map_metric_sidebar(MAP_METRICS)
    selected = map_route_sidebar(
        {
            route["route_id"]: f"{route['departure']} → {route['arrival']}"
            for route in routes
        }
    )
    try:
        rates = load_map_rates(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
    except (OSError, ValueError):
        rates = {}
    # we use the same stations label for the map as the CSV
    mapped_rates = [
        rates.get((route["departure"], route["arrival"]), {})
        for route in routes
    ]
    scale = RATE_SCALES[metric]
    pairs = {(route["departure"], route["arrival"]) for route in routes}

    # if paths overlap then draw the higher rate on top
    visible = []
    for route, route_rates in sorted(
        zip(routes, mapped_rates), key=lambda item: item[1].get(metric, -1)
    ):
        if selected and route["route_id"] != selected:
            continue
        color = rate_color(route_rates.get(metric), scale)
        tooltip = route_tooltip(route, pairs, rates)
        visible.extend(
            {"path": path, "color": color, "tooltip": tooltip}
            for path in route["paths"]
        )

    render_rate_legend(
        scale, any(metric in route_rates for route_rates in mapped_rates)
    )
    ## Draw the routes ##
    hit_area = pdk.Layer(
        "PathLayer",
        id="tgv-hit-area",
        data=visible,
        get_path="path",
        get_width=14,
        width_units=pdk.types.String("pixels"),
        opacity=0,
        pickable=True,
    )
    layer = pdk.Layer(
        "PathLayer",
        id="tgv-routes",
        data=visible,
        get_path="path",
        get_color="color",
        get_width=4 if selected else 3,
        width_units=pdk.types.String("pixels"),
        pickable=True,
    )
    deck = pdk.Deck(
        layers=[hit_area, layer],
        initial_view_state=pdk.ViewState(
            latitude=45.5, longitude=2.5, zoom=4.35
        ),
        map_style=pdk.map_styles.LIGHT,
        tooltip={
            "text": "{tooltip}",
            "className": "tgv-route-tooltip",
            "style": {
                "marginLeft": "12px",
                "marginTop": "10px",
                "whiteSpace": "pre-line",
                "maxWidth": "23rem",
                "lineHeight": "1.4",
            },
        },
    )
    # align the tooltip overlay with the chart and
    # show a pointer while a route is picked
    with st.container(key="tgv_map_frame"):
        st.html("""
            <style>
                .st-key-tgv_map_frame .deck-widgets-root {
                    position: absolute;
                    inset: 0;
                    pointer-events: none;
                }
                .st-key-tgv_map_frame .stDeckGlJsonChart:has(
                    .tgv-route-tooltip[style*="display: block"]
                ) .deck-events-root:not(:active),
                .st-key-tgv_map_frame .stDeckGlJsonChart:has(
                    .tgv-route-tooltip[style*="display: block"]
                ) .deck-events-root:not(:active) canvas {
                    cursor: pointer !important;
                }
            </style>
        """)
        st.pydeck_chart(
            deck,
            key="tgv_map",
            alt="Carte interactive des tracés ferroviaires reconstitués",
        )

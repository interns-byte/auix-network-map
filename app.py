from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="AUiX Network Map", layout="wide")

DATA_FILE = Path(__file__).with_name("Streamlit.xlsx")

CATEGORY_STYLE = {
    "Air University": {
        "color": "#e32119",
        "position": (-8.8, 6.2),
        "label": "AIR<br>UNIVERSITY",
    },
    "Academia": {
        "color": "#0a55d5",
        "position": (8.8, 6.2),
        "label": "ACADEMIA",
    },
    "Industry": {
        "color": "#ff9800",
        "position": (-8.8, -6.2),
        "label": "INDUSTRY",
    },
    "MIL & GOV": {
        "color": "#57a52c",
        "position": (8.8, -6.2),
        "label": "MIL &amp;<br>GOV",
    },
}


def normalize_category(value: object) -> str:
    text = str(value).strip()
    aliases = {
        "Air Univerity": "Air University",
        "Air university": "Air University",
        "Mil & Gov": "MIL & GOV",
        "MIL&GOV": "MIL & GOV",
        "MIL & Gov": "MIL & GOV",
    }
    return aliases.get(text, text)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    data = pd.read_excel(DATA_FILE)
    data.columns = [str(column).strip().lower() for column in data.columns]

    if "engagament" in data.columns and "engagement" not in data.columns:
        data = data.rename(columns={"engagament": "engagement"})

    required = {"name", "type", "engagement"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    for optional in ("relationship", "expertise"):
        if optional not in data.columns:
            data[optional] = "Not provided"

    data = data.dropna(subset=["name", "type"]).copy()
    data["name"] = data["name"].astype(str).str.strip()
    data["type"] = data["type"].map(normalize_category)
    data["engagement"] = pd.to_numeric(data["engagement"], errors="coerce").fillna(0)
    data["relationship"] = data["relationship"].fillna("Not provided").astype(str).str.strip()
    data["expertise"] = data["expertise"].fillna("Not provided").astype(str).str.strip()
    return data


def add_edge(
    figure: go.Figure,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    width: float = 2.0,
) -> None:
    figure.add_trace(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line={"color": "rgba(255,255,255,0.72)", "width": width},
            hoverinfo="skip",
            showlegend=False,
        )
    )


def add_node(
    figure: go.Figure,
    *,
    x: float,
    y: float,
    label: str,
    color: str,
    size: float,
    node_type: str,
    category: str,
    name: str,
    hover: str,
    text_position: str = "middle center",
    font_size: int = 17,
) -> None:
    figure.add_trace(
        go.Scatter(
            x=[x],
            y=[y],
            mode="markers+text",
            marker={
                "size": size,
                "color": color,
                "line": {"color": "white", "width": 1.8},
            },
            text=[label],
            textposition=text_position,
            textfont={
                "color": "white",
                "size": font_size,
                "family": "Arial Black",
            },
            customdata=[[node_type, category, name]],
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
            cliponaxis=False,
        )
    )


def ring_positions(category: str, count: int) -> list[tuple[float, float, str]]:
    """Place every organization at equal angular intervals around its category hub."""
    if count <= 0:
        return []

    cx, cy = CATEGORY_STYLE[category]["position"]
    radius = max(4.4, count * 0.36)

    # Start at the top and distribute every node evenly around all 360 degrees.
    start_angle = 90.0
    results: list[tuple[float, float, str]] = []
    for index in range(count):
        angle_deg = start_angle + index * (360.0 / count)
        angle = math.radians(angle_deg)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        cosine = math.cos(angle)
        sine = math.sin(angle)
        if cosine > 0.30:
            text_position = "middle right"
        elif cosine < -0.30:
            text_position = "middle left"
        elif sine > 0:
            text_position = "top center"
        else:
            text_position = "bottom center"

        results.append((x, y, text_position))
    return results


def build_figure(
    data: pd.DataFrame,
    expanded_category: str | None,
    selected_organization: str | None,
) -> go.Figure:
    figure = go.Figure()

    # Draw the permanent AUiX-to-category structure first.
    for category, style in CATEGORY_STYLE.items():
        cx, cy = style["position"]
        add_edge(figure, 0, 0, cx, cy, width=3.2)

    # Draw the expanded organization's spokes behind the nodes.
    subset = pd.DataFrame()
    positions: list[tuple[float, float, str]] = []
    if expanded_category:
        subset = (
            data[data["type"] == expanded_category]
            .sort_values(["engagement", "name"], ascending=[False, True])
            .reset_index(drop=True)
        )
        positions = ring_positions(expanded_category, len(subset))
        cx, cy = CATEGORY_STYLE[expanded_category]["position"]
        for (_, row), (x, y, _) in zip(subset.iterrows(), positions):
            line_width = 1.2 + min(float(row["engagement"]), 60.0) / 35.0
            add_edge(figure, cx, cy, x, y, width=line_width)

    # Center node.
    add_node(
        figure,
        x=0,
        y=0,
        label="AUiX",
        color="#f4c542",
        size=150,
        node_type="center",
        category="AUiX",
        name="AUiX",
        hover="<b>AUiX</b><br>Click to collapse the map",
        font_size=33,
    )

    # Category hubs. These visible markers themselves are the click targets.
    for category, style in CATEGORY_STYLE.items():
        cx, cy = style["position"]
        instruction = (
            "Click to hide organizations"
            if expanded_category == category
            else "Click to show organizations"
        )
        add_node(
            figure,
            x=cx,
            y=cy,
            label=style["label"],
            color=style["color"],
            size=155,
            node_type="category",
            category=category,
            name=category,
            hover=f"<b>{category}</b><br>{instruction}",
            font_size=20 if category != "Academia" else 19,
        )

    # Organization nodes for the one open category.
    if expanded_category and not subset.empty:
        maximum = max(float(subset["engagement"].max()), 1.0)
        for (_, row), (x, y, text_position) in zip(subset.iterrows(), positions):
            engagement = float(row["engagement"])
            node_size = 34 + 28 * math.sqrt(engagement / maximum)
            selected = selected_organization == row["name"]
            line_width = 4.5 if selected else 1.8

            figure.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers+text",
                    marker={
                        "size": node_size,
                        "color": CATEGORY_STYLE[expanded_category]["color"],
                        "line": {
                            "color": "#ffe66d" if selected else "white",
                            "width": line_width,
                        },
                    },
                    text=[row["name"]],
                    textposition=text_position,
                    textfont={"color": "white", "size": 13, "family": "Arial Black"},
                    customdata=[["organization", expanded_category, row["name"]]],
                    hovertemplate=(
                        f"<b>{row['name']}</b><br>"
                        f"Category: {expanded_category}<br>"
                        f"Engagements: {engagement:g}<br>"
                        f"Relationship: {row['relationship']}<br>"
                        f"Expertise: {row['expertise']}<br>"
                        "Click to show or hide details"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                    cliponaxis=False,
                )
            )

    figure.update_layout(
        title={
            "text": "2025–2026 AUiX Network Map",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 38, "color": "white", "family": "Arial Black"},
        },
        paper_bgcolor="#031630",
        plot_bgcolor="#031630",
        margin={"l": 25, "r": 25, "t": 90, "b": 30},
        xaxis={"visible": False, "range": [-15.5, 15.5], "fixedrange": True},
        yaxis={
            "visible": False,
            "range": [-12.5, 12.5],
            "scaleanchor": "x",
            "scaleratio": 1,
            "fixedrange": True,
        },
        hoverlabel={"bgcolor": "#10284b", "font_color": "white", "font_size": 14},
        showlegend=False,
        dragmode=False,
        clickmode="event+select",
    )
    return figure


def resolve_clicked_node(figure: go.Figure, clicked_point: dict) -> tuple[str, str, str] | None:
    curve_number = clicked_point.get("curveNumber")
    if curve_number is None or not (0 <= curve_number < len(figure.data)):
        return None

    trace = figure.data[curve_number]
    customdata = getattr(trace, "customdata", None)
    if customdata is None or len(customdata) == 0:
        return None

    values = list(customdata[0])
    if len(values) < 3:
        return None
    return str(values[0]), str(values[1]), str(values[2])


st.markdown(
    """
<style>
  .stApp {
    background: radial-gradient(circle at center, #0b2a52 0%, #031630 62%, #020d1f 100%);
  }
  header[data-testid="stHeader"] { background: transparent; }
  .block-container { padding-top: 0.25rem; max-width: 2000px; }
  .instruction {
    text-align: center;
    color: #d9e7ff;
    font-size: 1rem;
    margin-bottom: -0.2rem;
  }
  .detail-card {
    background: rgba(10, 36, 72, 0.94);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 18px;
    padding: 1.15rem 1.25rem;
    color: white;
    margin-top: 5rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.30);
  }
  .detail-card h2 { margin: 0 0 1rem 0; font-size: 1.55rem; }
  .detail-label { color: #aac9f5; font-weight: 700; margin-top: 0.8rem; }
  .detail-value { color: white; font-size: 1rem; }
  .empty-card { color: #c8daf4; line-height: 1.5; }
</style>
""",
    unsafe_allow_html=True,
)

try:
    df = load_data()
except Exception as exc:
    st.error(f"The spreadsheet could not be loaded: {exc}")
    st.stop()

if "expanded_category" not in st.session_state:
    st.session_state.expanded_category = None
if "selected_organization" not in st.session_state:
    st.session_state.selected_organization = None

st.markdown(
    '<div class="instruction">Click a category circle to open it. Opening another category closes the first. Click an organization once to pin its details, and click it again to hide them.</div>',
    unsafe_allow_html=True,
)

map_column, detail_column = st.columns([4.6, 1.25], gap="medium")

with map_column:
    figure = build_figure(
        df,
        st.session_state.expanded_category,
        st.session_state.selected_organization,
    )
    component_key = (
        f"network_{st.session_state.expanded_category}_"
        f"{st.session_state.selected_organization}"
    )
    clicked = plotly_events(
        figure,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=990,
        key=component_key,
    )

with detail_column:
    selected_name = st.session_state.selected_organization
    if selected_name:
        matching = df[df["name"] == selected_name]
        if not matching.empty:
            row = matching.iloc[0]
            st.markdown(
                f"""
<div class="detail-card">
  <h2>{row['name']}</h2>
  <div class="detail-label">Category</div>
  <div class="detail-value">{row['type']}</div>
  <div class="detail-label">Engagements</div>
  <div class="detail-value">{float(row['engagement']):g}</div>
  <div class="detail-label">Relationship</div>
  <div class="detail-value">{row['relationship']}</div>
  <div class="detail-label">Expertise</div>
  <div class="detail-value">{row['expertise']}</div>
  <div class="detail-label">Close</div>
  <div class="detail-value">Click the highlighted organization bubble again.</div>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
<div class="detail-card empty-card">
  <h2>Organization details</h2>
  Open a category, then click an organization bubble. Its engagement, relationship, and expertise will remain here until you click that bubble again.
</div>
""",
            unsafe_allow_html=True,
        )

if clicked:
    node = resolve_clicked_node(figure, clicked[0])
    if node:
        node_type, category, name = node

        if node_type == "center":
            st.session_state.expanded_category = None
            st.session_state.selected_organization = None
            st.rerun()

        if node_type == "category":
            if st.session_state.expanded_category == category:
                st.session_state.expanded_category = None
            else:
                st.session_state.expanded_category = category
            st.session_state.selected_organization = None
            st.rerun()

        if node_type == "organization":
            if st.session_state.selected_organization == name:
                st.session_state.selected_organization = None
            else:
                st.session_state.selected_organization = name
            st.rerun()

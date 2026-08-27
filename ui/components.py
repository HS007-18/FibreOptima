# FibreOptima Reusable UI Components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ui.theme import COLORS, RISK_ICONS, RISK_LABELS, get_risk_color


def risk_badge(risk_level: str, size: str = "normal") -> str:
    """Render a styled risk badge using HTML."""
    color = get_risk_color(risk_level)
    icon = RISK_ICONS.get(risk_level, "⚪")
    label = RISK_LABELS.get(risk_level, risk_level)
    
    size_styles = {
        "small": "font-size: 0.75rem; padding: 0.15rem 0.5rem;",
        "normal": "font-size: 0.85rem; padding: 0.25rem 0.75rem;",
        "large": "font-size: 1rem; padding: 0.4rem 1rem;",
    }
    style = size_styles.get(size, size_styles["normal"])
    
    return f'''
    <span style="
        background-color: {color};
        color: white;
        border-radius: 4px;
        {style}
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        white-space: nowrap;
    ">
        {icon} {label}
    </span>
    '''


def kpi_card(label: str, value: str, delta: str = None, delta_color: str = "normal", help_text: str = None):
    """Render a KPI metric card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)


def kpi_row(metrics: dict, cols: int = 4):
    """Render a row of KPI cards."""
    columns = st.columns(cols)
    for i, (label, value) in enumerate(metrics.items()):
        with columns[i % cols]:
            if isinstance(value, tuple):
                kpi_card(label, value[0], delta=value[1] if len(value) > 1 else None)
            else:
                kpi_card(label, value)


def section_header(title: str, subtitle: str = None, divider: bool = True):
    """Render a consistent section header."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
    if divider:
        st.divider()


def metric_grid(metrics: dict, cols: int = 4):
    """Render a grid of metrics with labels and values."""
    columns = st.columns(cols)
    for i, (label, value) in enumerate(metrics.items()):
        with columns[i % cols]:
            st.markdown(f"**{label}**")
            st.markdown(f"<div style='font-size: 1.25rem; font-weight: 600; color: #2c3e50;'>{value}</div>", unsafe_allow_html=True)


def signal_chip(label: str, status: str, details: str = None):
    """Render a signal status chip."""
    status_colors = {
        "ok": ("#27ae60", "✅"),
        "warning": ("#f39c12", "⚠️"),
        "alert": ("#c0392b", "🔴"),
        "info": ("#3498db", "ℹ️"),
    }
    color, icon = status_colors.get(status, ("#7f8c8d", "⚪"))
    
    html = f'''
    <div style="
        background-color: {color}15;
        border-left: 3px solid {color};
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        margin-bottom: 0.35rem;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="color: {color}; font-weight: 600;">{icon} {label}</span>
        </div>
    '''
    if details:
        html += f'<div style="margin-top: 0.25rem; font-size: 0.85rem; color: #5d6d7e;">{details}</div>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)


def callout_box(title: str, items: list, icon: str = "📋", color: str = "#3498db"):
    """Render a structured callout box with title and bullet items."""
    if not items:
        return
    
    items_html = "".join([f"<li style='margin-bottom: 0.35rem;'>{item}</li>" for item in items])
    
    st.markdown(f'''
    <div style="
        background-color: {color}10;
        border-left: 4px solid {color};
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.25rem;">{icon}</span>
            <span style="font-weight: 600; font-size: 1.05rem; color: {color};">{title}</span>
        </div>
        <ul style="margin: 0; padding-left: 1.5rem; color: #2c3e50;">
            {items_html}
        </ul>
    </div>
    ''', unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭", action_label: str = None, action_callback=None):
    """Render a consistent empty state."""
    st.markdown(f'''
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background-color: #f7f9fc;
        border-radius: 8px;
        border: 1px dashed #e1e8ed;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <div style="font-size: 1.1rem; color: #5d6d7e; margin-bottom: 1.5rem;">{message}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    if action_label and action_callback:
        if st.button(action_label, type="primary"):
            action_callback()


def plot_waste_trend(df: pd.DataFrame):
    """Plot waste % trend colored by risk level."""
    if df.empty or "waste_pct" not in df.columns or "risk_level" not in df.columns:
        return None
    
    color_map = {"NORMAL": "#27ae60", "WARNING": "#f39c12", "HIGH RISK": "#c0392b", "DATA ISSUE": "#7f8c8d"}
    
    fig = px.scatter(
        df.reset_index(),
        x="index",
        y="waste_pct",
        color="risk_level",
        color_discrete_map=color_map,
        title="Waste % Trend by Batch",
        labels={"index": "Batch Sequence", "waste_pct": "Waste %"},
        hover_data=["batch_id", "machine_id", "fabric_type", "risk_level"],
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=1, color="white")))
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def plot_risk_distribution(df: pd.DataFrame):
    """Plot risk distribution as donut chart."""
    if df.empty or "risk_level" not in df.columns:
        return None
    
    counts = df["risk_level"].value_counts().reset_index()
    counts.columns = ["risk_level", "count"]
    
    # Sort by risk severity
    risk_order = ["HIGH RISK", "WARNING", "NORMAL", "DATA ISSUE"]
    counts["sort_key"] = counts["risk_level"].map({r: i for i, r in enumerate(risk_order)})
    counts = counts.sort_values("sort_key")
    
    color_map = {"NORMAL": "#27ae60", "WARNING": "#f39c12", "HIGH RISK": "#c0392b", "DATA ISSUE": "#7f8c8d"}
    
    fig = go.Figure(data=[go.Pie(
        labels=[RISK_LABELS.get(r, r) for r in counts["risk_level"]],
        values=counts["count"],
        hole=0.55,
        marker=dict(
            colors=[color_map.get(r, "#7f8c8d") for r in counts["risk_level"]],
            line=dict(color="white", width=2),
        ),
        textinfo="label+value",
        textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
    )])
    
    fig.update_layout(
        title="Risk Distribution",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        annotations=[dict(text="Batches", x=0.5, y=0.5, font_size=14, showarrow=False)],
    )
    return fig


def plot_machine_ranking(df: pd.DataFrame):
    """Plot top risk machines as horizontal bar."""
    if df.empty:
        return None
    
    valid = df[df["risk_level"].isin(["WARNING", "HIGH RISK"])]
    if valid.empty:
        return None
    
    machine_risk = valid.groupby("machine_id").size().reset_index(name="risk_count")
    machine_risk = machine_risk.sort_values("risk_count", ascending=True).tail(10)
    
    fig = px.bar(
        machine_risk,
        x="risk_count",
        y="machine_id",
        orientation="h",
        title="Top Risk Machines",
        labels={"machine_id": "Machine", "risk_count": "Risk Batches"},
        color_discrete_sequence=["#c0392b"],
    )
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def plot_analytics_bar(df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str = None):
    """Generic bar chart for analytics tabs."""
    if df.empty:
        return None
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        color_continuous_scale="RdYlGn_r" if color_col else None,
    )
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig
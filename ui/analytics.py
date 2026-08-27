# FibreOptima Analytics
import pandas as pd
import streamlit as st
from src.analytics.machine import analyze_machine
from src.analytics.fabric import analyze_fabric
from src.analytics.shift import analyze_shift
from src.analytics.operator import analyze_operator
from ui.components import plot_analytics_bar, section_header, empty_state
from ui.theme import COLORS


def render_analytics(records):
    """Render the Analytics page with filterable tabs."""
    section_header(
        "Production Analytics",
        "Machine, Fabric, Shift, and Operator waste analysis"
    )
    
    # Filters
    with st.expander("🔍 Filters", expanded=False):
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            risk_filter = st.multiselect(
                "Risk Level",
                ["NORMAL", "WARNING", "HIGH RISK"],
                default=["NORMAL", "WARNING", "HIGH RISK"],
                key="an_risk_filter",
            )
        with filter_col2:
            show_chart = st.checkbox("Show Charts", value=True, key="an_show_chart")
    
    # Filter records
    filtered_records = [r for r in records if r.risk_level in risk_filter]
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏭 Machine", "🧵 Fabric", "🕐 Shift", "👤 Operator"])
    
    with tab1:
        render_machine_tab(filtered_records, show_chart)
    
    with tab2:
        render_fabric_tab(filtered_records, show_chart)
    
    with tab3:
        render_shift_tab(filtered_records, show_chart)
    
    with tab4:
        render_operator_tab(filtered_records, show_chart)


def render_machine_tab(records, show_chart):
    """Render Machine analytics tab."""
    st.subheader("Machine Analysis")
    
    machine_df = analyze_machine(records)
    
    if machine_df.empty:
        empty_state("No machine data available for selected filters.")
        return
    
    # Format for display
    display_df = machine_df.copy()
    display_df["avg_waste_pct"] = display_df["avg_waste_pct"].apply(lambda x: f"{x:.2f}%")
    display_df["median_waste_pct"] = display_df["median_waste_pct"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    if show_chart:
        fig = plot_analytics_bar(
            machine_df, "machine_id", "avg_waste_pct",
            "Average Waste % by Machine", "high_risk_count"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Export
    if st.button("📥 Export Machine Data", key="exp_machine"):
        csv = machine_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "machine_analytics.csv", "text/csv")


def render_fabric_tab(records, show_chart):
    """Render Fabric analytics tab."""
    st.subheader("Fabric Analysis")
    
    fabric_df = analyze_fabric(records)
    
    if fabric_df.empty:
        empty_state("No fabric data available for selected filters.")
        return
    
    display_df = fabric_df.copy()
    display_df["avg_waste_pct"] = display_df["avg_waste_pct"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    if show_chart:
        fig = plot_analytics_bar(
            fabric_df, "fabric_type", "avg_waste_pct",
            "Average Waste % by Fabric", "high_risk_count"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    if st.button("📥 Export Fabric Data", key="exp_fabric"):
        csv = fabric_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "fabric_analytics.csv", "text/csv")


def render_shift_tab(records, show_chart):
    """Render Shift analytics tab."""
    st.subheader("Shift Analysis")
    
    shift_df = analyze_shift(records)
    
    if shift_df.empty:
        empty_state("No shift data available for selected filters.")
        return
    
    display_df = shift_df.copy()
    display_df["avg_waste_pct"] = display_df["avg_waste_pct"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    if show_chart:
        fig = plot_analytics_bar(
            shift_df, "shift", "avg_waste_pct",
            "Average Waste % by Shift", "high_risk_count"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    if st.button("📥 Export Shift Data", key="exp_shift"):
        csv = shift_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "shift_analytics.csv", "text/csv")


def render_operator_tab(records, show_chart):
    """Render Operator analytics tab."""
    st.subheader("Operator Analysis")
    
    operator_df = analyze_operator(records)
    
    if operator_df.empty:
        empty_state("No operator data available for selected filters.")
        return
    
    display_df = operator_df.copy()
    display_df["avg_waste_pct"] = display_df["avg_waste_pct"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    if show_chart:
        fig = plot_analytics_bar(
            operator_df, "operator", "avg_waste_pct",
            "Average Waste % by Operator", "high_risk_count"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    if st.button("📥 Export Operator Data", key="exp_operator"):
        csv = operator_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "operator_analytics.csv", "text/csv")
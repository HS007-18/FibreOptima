# FibreOptima Command Center
import pandas as pd
import streamlit as st
from ui.components import (
    kpi_card,
    kpi_row,
    plot_waste_trend,
    plot_risk_distribution,
    plot_machine_ranking,
    section_header,
)


def render_command_center(df: pd.DataFrame, report):
    """Render the main Command Center dashboard."""
    valid_df = df[df["is_valid"]]
    risk_counts = valid_df["risk_level"].value_counts()
    
    # KPI Row
    section_header("Production Overview", "Key metrics from the latest analysis")
    
    metrics = {
        "Total Batches": len(df),
        "✅ Normal": int(risk_counts.get("NORMAL", 0)),
        "⚠️ Warning": int(risk_counts.get("WARNING", 0)),
        "🔴 High Risk": int(risk_counts.get("HIGH RISK", 0)),
        "⚫ Data Issues": int(risk_counts.get("DATA ISSUE", 0)),
        "Avg Waste %": f"{valid_df['waste_pct'].mean():.1f}%" if not valid_df.empty else "0.0%",
    }
    kpi_row(metrics, cols=6)
    
    st.divider()
    
    # Charts Row
    col_left, col_mid, col_right = st.columns([2, 1.5, 1.5])
    
    with col_left:
        fig_trend = plot_waste_trend(valid_df.reset_index(drop=True))
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No waste trend data available.")
    
    with col_mid:
        fig_dist = plot_risk_distribution(valid_df)
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No risk distribution data.")
    
    with col_right:
        fig_machines = plot_machine_ranking(valid_df)
        if fig_machines:
            st.plotly_chart(fig_machines, use_container_width=True)
        else:
            st.info("No high-risk machines detected.")
    
    st.divider()
    
    # Quick Actions
    section_header("Quick Actions", "Navigate to detailed analysis")
    
    qa_col1, qa_col2, qa_col3 = st.columns(3)
    
    with qa_col1:
        if st.button("🔍 View Risk Queue", use_container_width=True, type="primary"):
            st.session_state.current_page = "Risk Queue"
            st.rerun()
    
    with qa_col2:
        if st.button("📈 Open Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    
    with qa_col3:
        if st.button("🔍 Data Quality Report", use_container_width=True):
            st.session_state.current_page = "Data Quality"
            st.rerun()
    
    st.divider()
    
    # Data Quality Summary
    section_header("Data Quality Summary", "Validation results from the latest run")
    
    qc_col1, qc_col2, qc_col3, qc_col4 = st.columns(4)
    with qc_col1:
        kpi_card("Total Records", report.total_records)
    with qc_col2:
        kpi_card("Valid Records", report.valid_records)
    with qc_col3:
        kpi_card("Duplicates", report.duplicates)
    with qc_col4:
        kpi_card("Imputed Values", report.imputed_values)
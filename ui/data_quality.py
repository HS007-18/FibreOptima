# FibreOptima Data Quality
import pandas as pd
import streamlit as st
from ui.components import kpi_card, section_header, empty_state, callout_box
from ui.theme import COLORS


def render_data_quality(df: pd.DataFrame, report):
    """Render the Data Quality page with plain-language summaries."""
    section_header(
        "Data Quality Report",
        "Validation results and data integrity summary"
    )
    
    # KPI Row
    metrics = {
        "Total Records": report.total_records,
        "Valid Records": report.valid_records,
        "Data Issues": report.data_issues,
        "Duplicates": report.duplicates,
        "Missing Values": report.missing_values,
        "Zero Production": report.zero_production,
        "Invalid Values": report.invalid_values,
        "Imputed Values": report.imputed_values,
    }
    
    # Display in 2 rows of 4
    cols1 = st.columns(4)
    keys1 = list(metrics.keys())[:4]
    for i, key in enumerate(keys1):
        with cols1[i]:
            kpi_card(key, metrics[key])
    
    cols2 = st.columns(4)
    keys2 = list(metrics.keys())[4:]
    for i, key in enumerate(keys2):
        with cols2[i]:
            kpi_card(key, metrics[key])
    
    st.divider()
    
    # Plain-language Summary
    st.markdown("### 📝 Quality Summary")
    
    summary_items = []
    
    if report.duplicates > 0:
        summary_items.append(f"{report.duplicates} duplicate batch record(s) detected and excluded from analysis.")
    
    if report.zero_production > 0:
        summary_items.append(f"{report.zero_production} record(s) with zero production quantity — waste percentage cannot be calculated and these are marked as DATA ISSUE.")
    
    if report.missing_values > 0:
        summary_items.append(f"{report.missing_values} missing humidity value(s) detected. Historical contextual medians were used for imputation and these records are flagged.")
    
    if report.invalid_values > 0:
        summary_items.append(f"{report.invalid_values} record(s) contain invalid numeric values (negative quantities, humidity out of range, etc.) and are marked as DATA ISSUE.")
    
    if report.imputed_values > 0:
        summary_items.append(f"{report.imputed_values} value(s) were imputed from historical context and flagged for review.")
    
    if not summary_items:
        summary_items.append("No data quality issues detected. All records passed validation.")
    
    for item in summary_items:
        callout_box(
            "Finding",
            [item],
            icon="🔍" if "issue" in item.lower() or "invalid" in item.lower() or "zero" in item.lower() else "✅",
            color="#c0392b" if any(w in item.lower() for w in ["issue", "invalid", "zero", "duplicate"]) else "#f39c12" if "imputed" in item.lower() or "missing" in item.lower() else "#27ae60"
        )
    
    st.divider()
    
    # Detailed Issue Tables
    st.markdown("### 📋 Detailed Records")
    
    # Records with issues
    issue_df = df[~df["is_valid"] | df["humidity_imputed"] | df["is_duplicate"]].copy()
    
    if not issue_df.empty:
        st.markdown("#### Records with Quality Flags")
        
        display_cols = [
            "batch_id", "machine_id", "fabric_type", "production_quantity",
            "waste_quantity", "waste_pct", "risk_level",
            "is_valid", "is_duplicate", "zero_production",
            "humidity_missing", "humidity_imputed", "invalid_value",
            "data_quality_reason"
        ]
        available_cols = [c for c in display_cols if c in issue_df.columns]
        
        # Format
        display_df = issue_df[available_cols].copy()
        if "production_quantity" in display_df.columns:
            display_df["production_quantity"] = display_df["production_quantity"].apply(lambda x: f"{x:,.0f}")
        if "waste_quantity" in display_df.columns:
            display_df["waste_quantity"] = display_df["waste_quantity"].apply(lambda x: f"{x:,.0f}")
        if "waste_pct" in display_df.columns:
            display_df["waste_pct"] = display_df["waste_pct"].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.success("No records with quality issues found.")
    
    st.divider()
    
    # All Records Overview
    st.markdown("#### All Records Overview")
    
    overview_cols = [
        "batch_id", "machine_id", "fabric_type", "production_quantity",
        "waste_quantity", "waste_pct", "risk_level", "baseline_source",
        "history_count", "is_valid", "maintenance_signal", "speed_signal",
        "environment_signal", "limited_history", "humidity_imputed"
    ]
    available_overview = [c for c in overview_cols if c in df.columns]
    
    display_df = df[available_overview].copy()
    if "production_quantity" in display_df.columns:
        display_df["production_quantity"] = display_df["production_quantity"].apply(lambda x: f"{x:,.0f}")
    if "waste_quantity" in display_df.columns:
        display_df["waste_quantity"] = display_df["waste_quantity"].apply(lambda x: f"{x:,.0f}")
    if "waste_pct" in display_df.columns:
        display_df["waste_pct"] = display_df["waste_pct"].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Export
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        if st.button("📥 Export Full Dataset", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "fibreoptima_full_data.csv", "text/csv")
    with col_exp2:
        if st.button("📥 Export Quality Report", use_container_width=True):
            quality_df = issue_df if not issue_df.empty else pd.DataFrame({"note": ["No issues found"]})
            csv = quality_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "fibreoptima_quality_report.csv", "text/csv")
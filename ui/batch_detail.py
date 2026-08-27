# FibreOptima Batch Investigation
import pandas as pd
import streamlit as st
from ui.components import (
    section_header,
    metric_grid,
    signal_chip,
    callout_box,
    risk_badge,
)
from ui.theme import get_risk_color, RISK_ICONS, RISK_LABELS


def render_batch_detail(df: pd.DataFrame):
    """Render the Batch Investigation page."""
    valid_df = df[df["is_valid"]].copy()
    
    if valid_df.empty:
        st.warning("No valid batches to investigate.")
        return
    
    # Determine which batch to show
    selected_batch_id = st.session_state.get("selected_batch")
    
    if not selected_batch_id:
        # Show batch selector
        st.markdown("### 🔍 Select a Batch to Investigate")
        
        batch_options = valid_df["batch_id"].tolist()
        batch_labels = [
            f"{row['batch_id']} | {row['machine_id']} | {row['fabric_type']} | {row['waste_pct']:.1f}% | {row['risk_level']}"
            for _, row in valid_df.iterrows()
        ]
        
        selected_idx = st.selectbox(
            "Batch",
            range(len(batch_options)),
            format_func=lambda i: batch_labels[i],
            key="bd_select_batch",
        )
        
        if st.button("🔍 Investigate", type="primary"):
            st.session_state.selected_batch = batch_options[selected_idx]
            st.rerun()
        return
    
    # Get the selected batch record
    record = valid_df[valid_df["batch_id"] == selected_batch_id]
    if record.empty:
        st.error(f"Batch {selected_batch_id} not found.")
        st.session_state.selected_batch = None
        return
    
    row = record.iloc[0]
    risk_level = row["risk_level"]
    risk_color = get_risk_color(risk_level)
    risk_icon = RISK_ICONS.get(risk_level, "⚪")
    risk_label = RISK_LABELS.get(risk_level, risk_level)
    
    # Header with back button
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("← Back to Queue", key="bd_back"):
            st.session_state.selected_batch = None
            st.session_state.current_page = "Risk Queue"
            st.rerun()
    
    with col_title:
        st.markdown(f"""
        <div style="margin-top: 0.5rem;">
            <h1 style="margin: 0; display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.5rem;">{risk_icon}</span>
                <span style="font-weight: 700; color: #2c3e50;">BATCH {selected_batch_id}</span>
                <span style="
                    background-color: {risk_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    font-size: 0.85rem;
                    font-weight: 600;
                ">{risk_label}</span>
            </h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Metric Grid
    metrics = {
        "Waste %": f"{row['waste_pct']:.1f}%",
        "Baseline": f"{row['baseline_waste_pct']:.1f}%",
        "Deviation": f"{row['waste_deviation']:+.1f}%",
        "Z-Score": f"{row['waste_z_score']:.2f}" if row['waste_z_score'] is not None else "N/A",
    }
    metric_grid(metrics, cols=4)
    
    st.divider()
    
    # Context Grid
    st.markdown("### Production Context")
    
    ctx_col1, ctx_col2, ctx_col3, ctx_col4 = st.columns(4)
    
    with ctx_col1:
        signal_chip("Machine", "info", row['machine_id'])
        signal_chip("Fabric", "info", row['fabric_type'])
        signal_chip("Operator", "info", row['operator'])
        signal_chip("Shift", "info", row['shift'])
    
    with ctx_col2:
        signal_chip("Production", "info", f"{row['production_quantity']:,.0f} kg")
        signal_chip("Waste Qty", "info", f"{row['waste_quantity']:,.0f} kg")
        signal_chip("Speed", "info", f"{row['production_speed']:,.0f}")
        signal_chip("Machine Age", "info", f"{row['machine_age']:.0f} years")
    
    with ctx_col3:
        maint_status = "Overdue" if row['maintenance_signal'] else "OK"
        maint_color = "alert" if row['maintenance_signal'] else "ok"
        signal_chip("Maintenance", maint_color, f"{maint_status} ({int(row['days_since_maintenance'])} days)")
        
        humidity_val = row['humidity']
        hum_status = "Imputed" if row['humidity_imputed'] else "Measured"
        signal_chip("Humidity", "info", f"{humidity_val:.1f}% ({hum_status})")
        
        signal_chip("Temperature", "info", f"{row['temperature']:.1f}°C")
        
        baseline_src = row['baseline_source'].replace('_', ' ').title()
        signal_chip("Baseline Source", "info", baseline_src)
    
    with ctx_col4:
        signal_chip("History Count", "info", f"{row['history_count']} batches")
        
        lh_status = "Yes" if row['limited_history'] else "No"
        lh_color = "warning" if row['limited_history'] else "ok"
        signal_chip("Limited History", lh_color, lh_status)
        
        speed_status = "Anomaly" if row['speed_signal'] else "Normal"
        speed_color = "alert" if row['speed_signal'] else "ok"
        signal_chip("Speed Signal", speed_color, speed_status)
        
        env_status = "Anomaly" if row['environment_signal'] else "Normal"
        env_color = "alert" if row['environment_signal'] else "ok"
        signal_chip("Environment Signal", env_color, env_status)
    
    st.divider()
    
    # WHY Section
    if row["reasons"]:
        reasons = row["reasons"].split("; ")
        callout_box(
            "WHY — Contributing Factors",
            reasons,
            icon="🔍",
            color="#c0392b" if risk_level == "HIGH RISK" else "#f39c12"
        )
    
    # WHAT TO CHECK Section
    if row["recommendations"]:
        recommendations = row["recommendations"].split("; ")
        callout_box(
            "WHAT TO CHECK — Recommended Actions",
            recommendations,
            icon="🛠️",
            color="#3498db"
        )
    
    # Data Quality Notes
    quality_notes = []
    if row['humidity_imputed']:
        quality_notes.append("Humidity value was imputed from historical median (contextual fallback).")
    if row['limited_history']:
        quality_notes.append("Limited historical data for this machine-fabric combination; baseline confidence is reduced.")
    if row['is_duplicate']:
        quality_notes.append("This batch was flagged as a duplicate.")
    
    if quality_notes:
        st.divider()
        callout_box(
            "Data Quality Notes",
            quality_notes,
            icon="📋",
            color="#7f8c8d"
        )
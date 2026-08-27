# FibreOptima Risk Queue
import pandas as pd
import streamlit as st
from ui.components import section_header, risk_badge, empty_state
from ui.theme import RISK_SORT_ORDER


def render_risk_queue(df: pd.DataFrame):
    """Render the Risk Queue page with filterable, sortable table."""
    section_header(
        "Risk Queue",
        "Batches sorted by risk severity. Select a batch to investigate."
    )
    
    valid_df = df[df["is_valid"]].copy()
    
    if valid_df.empty:
        empty_state(
            "No valid batches to display.",
            icon="📭",
        )
        return
    
    # Filters
    with st.expander("🔍 Filters", expanded=True):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            machines = ["All"] + sorted(valid_df["machine_id"].unique().tolist())
            selected_machine = st.selectbox("Machine", machines, key="rq_machine")
        
        with filter_col2:
            fabrics = ["All"] + sorted(valid_df["fabric_type"].unique().tolist())
            selected_fabric = st.selectbox("Fabric", fabrics, key="rq_fabric")
        
        with filter_col3:
            shifts = ["All"] + sorted(valid_df["shift"].unique().tolist())
            selected_shift = st.selectbox("Shift", shifts, key="rq_shift")
        
        with filter_col4:
            risks = ["All"] + ["HIGH RISK", "WARNING", "NORMAL", "DATA ISSUE"]
            selected_risk = st.selectbox("Risk Level", risks, key="rq_risk")
    
    # Apply filters
    filtered = valid_df.copy()
    
    if selected_machine != "All":
        filtered = filtered[filtered["machine_id"] == selected_machine]
    if selected_fabric != "All":
        filtered = filtered[filtered["fabric_type"] == selected_fabric]
    if selected_shift != "All":
        filtered = filtered[filtered["shift"] == selected_shift]
    if selected_risk != "All":
        filtered = filtered[filtered["risk_level"] == selected_risk]
    
    # Sort by risk severity
    filtered["risk_sort"] = filtered["risk_level"].map(RISK_SORT_ORDER).fillna(99)
    filtered = filtered.sort_values(["risk_sort", "waste_pct"], ascending=[True, False])
    
    # Summary
    st.caption(f"Showing {len(filtered)} of {len(valid_df)} valid batches")
    
    if filtered.empty:
        empty_state("No batches match the current filters.", icon="🔍")
        return
    
    # Display table with risk badges
    display_cols = [
        "batch_id", "machine_id", "fabric_type", "shift",
        "production_quantity", "waste_quantity", "waste_pct",
        "baseline_waste_pct", "risk_level", "reasons"
    ]
    available = [c for c in display_cols if c in filtered.columns]
    
    # Prepare display dataframe
    display_df = filtered[available].copy()
    
    # Format columns
    if "production_quantity" in display_df.columns:
        display_df["production_quantity"] = display_df["production_quantity"].apply(lambda x: f"{x:,.0f}")
    if "waste_quantity" in display_df.columns:
        display_df["waste_quantity"] = display_df["waste_quantity"].apply(lambda x: f"{x:,.0f}")
    if "waste_pct" in display_df.columns:
        display_df["waste_pct"] = display_df["waste_pct"].apply(lambda x: f"{x:.1f}%")
    if "baseline_waste_pct" in display_df.columns:
        display_df["baseline_waste_pct"] = display_df["baseline_waste_pct"].apply(lambda x: f"{x:.1f}%")
    
    # Show table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        column_config={
            "risk_level": st.column_config.TextColumn(
                "Risk",
                help="Risk classification",
            ),
            "reasons": st.column_config.TextColumn(
                "Main Reason",
                help="Primary contributing factor",
                width="large",
            ),
        },
        hide_index=True,
    )
    
    st.divider()
    
    # Batch Selection for Investigation
    st.markdown("### 🔍 Investigate a Batch")
    
    # Get high-risk batches for quick selection
    high_risk_batches = filtered[filtered["risk_level"].isin(["HIGH RISK", "WARNING"])]
    
    if not high_risk_batches.empty:
        st.markdown("**High Priority Batches**")
        
        batch_options = high_risk_batches["batch_id"].tolist()
        batch_labels = [
            f"{row['batch_id']} | {row['machine_id']} | {row['fabric_type']} | {row['waste_pct']} | {row['risk_level']}"
            for _, row in high_risk_batches.iterrows()
        ]
        
        selected_idx = st.selectbox(
            "Select a high-risk batch to investigate",
            range(len(batch_options)),
            format_func=lambda i: batch_labels[i],
            key="rq_select_batch",
        )
        
        if st.button("🔍 Investigate Selected Batch", type="primary", use_container_width=True):
            selected_batch = batch_options[selected_idx]
            st.session_state.selected_batch = selected_batch
            st.session_state.current_page = "Batch Investigation"
            st.rerun()
    else:
        # Fallback: show all filtered batches
        batch_options = filtered["batch_id"].tolist()
        batch_labels = [
            f"{row['batch_id']} | {row['machine_id']} | {row['fabric_type']} | {row['waste_pct']} | {row['risk_level']}"
            for _, row in filtered.iterrows()
        ]
        
        selected_idx = st.selectbox(
            "Select a batch to investigate",
            range(len(batch_options)),
            format_func=lambda i: batch_labels[i],
            key="rq_select_batch_all",
        )
        
        if st.button("🔍 Investigate Selected Batch", type="primary", use_container_width=True):
            selected_batch = batch_options[selected_idx]
            st.session_state.selected_batch = selected_batch
            st.session_state.current_page = "Batch Investigation"
            st.rerun()
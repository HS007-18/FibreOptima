# FibreOptima — Textile Production Waste Intelligence
# 5-Layer End-to-End System: Data -> ML -> Business -> RAG -> Agent
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from src.pipeline import FibreOptimaPipeline, process_production_data, records_to_dataframe
from ui.dashboard import render_command_center
from ui.risk_queue import render_risk_queue
from ui.batch_detail import render_batch_detail
from ui.analytics import render_analytics
from ui.data_quality import render_data_quality
from ui.validation_preview import render_validation_preview
from src.legacy_v1.config.settings import SETTINGS


st.set_page_config(
    page_title="FibreOptima — Textile Waste Intelligence",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Running FibreOptima Intelligence Pipeline...")
def run_pipeline(file_path: str, reference_date: str = None, historical_df=None) -> tuple:
    """Run the complete FibreOptima pipeline."""
    ref_date = datetime.fromisoformat(reference_date) if reference_date else SETTINGS.reference_date
    batches, report, df, hist_df, _ = process_production_data(
        file_path, reference_date=ref_date, historical_df=historical_df
    )
    return batches, report, df, hist_df


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "data_loaded": False,
        "records": None,
        "report": None,
        "df": None,
        "hist_df": None,
        "selected_batch": None,
        "current_page": "Command Center",
        "file_path": None,
        "reference_date": "2026-01-01",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def sidebar_config():
    """Render sidebar configuration."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Production CSV",
            type=["csv"],
            help="Upload textile production data CSV",
            key="file_uploader",
        )
        
        use_sample = st.checkbox("Use Historical Proxy Telemetry", value=True, key="use_sample")
        
        ref_date_str = st.text_input(
            "Reference Date (YYYY-MM-DD)",
            value=st.session_state.reference_date,
            help="Date for maintenance age calculation",
            key="ref_date_input",
        )
        st.session_state.reference_date = ref_date_str
        
        st.divider()
        
        # Architecture Badges
        st.caption("🧵 FibreOptima V3 Architecture")
        st.caption("1. Data: UCI AI4I Proxy Telemetry")
        st.caption("2. ML: HistGradientBoosting (waste prediction)")
        st.caption("3. ML: IsolationForest (anomaly, no leakage)")
        st.caption("4. Knowledge: Chroma Vector RAG")
        st.caption("5. Agent: Evidence Investigation")
        
        return uploaded_file, use_sample


def handle_data_loading(uploaded_file, use_sample):
    """Handle data loading and pipeline execution."""
    if uploaded_file:
        file_path = uploaded_file
    elif use_sample:
        file_path = "data/production/historical_production.csv"
        if not os.path.exists(file_path):
            st.error("Historical dataset missing. Please run `python scripts/download_real_data.py` first.")
            return False
    else:
        st.info("Please upload a CSV file or enable historical telemetry.")
        return False
    
    # Store file path
    st.session_state.file_path = file_path
    
    # Run pipeline
    try:
        with st.spinner("Running FibreOptima 5-Layer Pipeline..."):
            records, report, df, hist_df = run_pipeline(file_path, st.session_state.reference_date)
        
        st.session_state.records = records
        st.session_state.report = report
        st.session_state.df = df
        st.session_state.hist_df = hist_df
        st.session_state.data_loaded = True
        
        # Reset selected batch on new data
        st.session_state.selected_batch = None
        
        st.success(f"Processed {len(records)} production batches across 5 layers.")
        return True
        
    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        st.exception(e)
        return False


def sidebar_navigation():
    """Render sidebar navigation."""
    with st.sidebar:
        st.divider()
        st.markdown("## 📍 Navigation")
        
        pages = [
            "Command Center",
            "Risk Queue",
            "Batch Investigation",
            "Analytics",
            "Data Quality",
        ]
        
        current = st.session_state.current_page
        
        if st.session_state.selected_batch and current != "Batch Investigation":
            st.session_state.current_page = "Batch Investigation"
            current = "Batch Investigation"
        
        selected = st.radio(
            "Page",
            pages,
            index=pages.index(current) if current in pages else 0,
            key="nav_radio",
            label_visibility="collapsed",
        )
        
        if selected != current:
            st.session_state.current_page = selected
            st.rerun()
        
        if st.session_state.data_loaded and st.session_state.df is not None:
            st.divider()
            st.markdown("### Quick Stats")
            valid_df = st.session_state.df[st.session_state.df["is_valid"]]
            risk_counts = valid_df["risk_level"].value_counts()
            st.caption(f"🟢 Normal: {int(risk_counts.get('NORMAL', 0))}")
            st.caption(f"🟡 Warning: {int(risk_counts.get('WARNING', 0))}")
            st.caption(f"🔴 High Risk: {int(risk_counts.get('HIGH RISK', 0))}")


def render_header():
    """Render application header with methodology disclosure."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a3c5e 0%, #2c5f8a 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: white;
    ">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2.5rem;">🧵</div>
            <div>
                <h1 style="margin: 0; font-size: 1.75rem; font-weight: 700;">FibreOptima</h1>
                <p style="margin: 0.25rem 0 0 0; font-size: 1rem; opacity: 0.9;">Textile Production Waste Intelligence System</p>
            </div>
        </div>
        <p style="margin: 0.75rem 0 0 0; font-size: 0.85rem; opacity: 0.8;">
            <b>Scientific Provenance Disclosure:</b> Underlying operational telemetry derived from UCI AI4I 2020 dataset, deterministically proxy-transformed into textile domain variables for end-to-end architecture validation.
        </p>
    </div>
    """, unsafe_allow_html=True)


def main():
    init_session_state()
    render_header()
    
    uploaded_file, use_sample = sidebar_config()
    
    if not st.session_state.data_loaded or (uploaded_file and st.session_state.get("last_uploaded") != uploaded_file):
        if handle_data_loading(uploaded_file, use_sample):
            st.session_state.last_uploaded = uploaded_file
    
    sidebar_navigation()
    
    if not st.session_state.data_loaded:
        st.info("Loading production telemetry data...")
        return
    
    page = st.session_state.current_page
    df = st.session_state.df
    records = st.session_state.records
    report = st.session_state.report
    
    if page == "Command Center":
        render_command_center(df, report)
    elif page == "Risk Queue":
        render_risk_queue(df)
    elif page == "Batch Investigation":
        render_batch_detail(df)
    elif page == "Analytics":
        render_analytics(records)
    elif page == "Data Quality":
        render_data_quality(df, report)


if __name__ == "__main__":
    main()
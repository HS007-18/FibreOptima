# FibreOptima Validation Preview
# Pre-analysis data quality scan
import pandas as pd
import streamlit as st
from src.ingestion.loader import load_and_normalize_csv
from src.config.settings import SETTINGS


def scan_csv_quality(file_path: str) -> dict:
    """Quick scan of CSV for data quality issues without full pipeline."""
    try:
        df = load_and_normalize_csv(file_path)
    except Exception as e:
        return {"error": str(e), "valid": False}
    
    issues = []
    warnings = []
    
    # Check required columns
    missing_cols = set(SETTINGS.REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        issues.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Check for duplicates
    if "batch_id" in df.columns:
        dup_count = df["batch_id"].duplicated().sum()
        if dup_count > 0:
            warnings.append(f"{dup_count} duplicate Batch ID(s) detected")
    
    # Check zero production
    if "production_quantity" in df.columns:
        zero_prod = (df["production_quantity"] == 0).sum()
        if zero_prod > 0:
            warnings.append(f"{zero_prod} record(s) with zero production quantity")
    
    # Check missing humidity
    if "humidity" in df.columns:
        missing_hum = df["humidity"].isna().sum()
        if missing_hum > 0:
            warnings.append(f"{missing_hum} missing humidity value(s)")
    
    # Check invalid numeric ranges
    invalid_checks = []
    if "production_quantity" in df.columns:
        invalid_checks.append(("production_quantity < 0", (df["production_quantity"] < 0).sum()))
    if "waste_quantity" in df.columns:
        invalid_checks.append(("waste_quantity < 0", (df["waste_quantity"] < 0).sum()))
    if "machine_age" in df.columns:
        invalid_checks.append(("machine_age < 0", (df["machine_age"] < 0).sum()))
    if "humidity" in df.columns:
        invalid_checks.append(("humidity < 0 or > 100", ((df["humidity"] < 0) | (df["humidity"] > 100)).sum()))
    
    for label, count in invalid_checks:
        if count > 0:
            issues.append(f"{count} record(s) with {label}")
    
    return {
        "valid": len(issues) == 0,
        "total_rows": len(df),
        "columns": list(df.columns),
        "issues": issues,
        "warnings": warnings,
        "preview_df": df.head(10),
    }


def render_validation_preview(file_path: str) -> bool:
    """Render validation preview UI. Returns True if user should proceed."""
    st.markdown("### 📋 Data Validation Preview")
    
    result = scan_csv_quality(file_path)
    
    if not result.get("valid", True) and "error" in result:
        st.error(f"Failed to read CSV: {result['error']}")
        return False
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", result["total_rows"])
    with col2:
        st.metric("Columns", len(result["columns"]))
    with col3:
        status = "✅ Ready" if result["valid"] else "⚠️ Issues Found"
        st.metric("Status", status)
    
    # Issues
    if result["issues"]:
        st.markdown("#### ❌ Blocking Issues")
        for issue in result["issues"]:
            st.error(f"• {issue}")
    
    # Warnings
    if result["warnings"]:
        st.markdown("#### ⚠️ Warnings (will be handled automatically)")
        for warning in result["warnings"]:
            st.warning(f"• {warning}")
    
    if not result["issues"] and not result["warnings"]:
        st.success("No issues detected. Data looks clean.")
    
    # Column mapping
    with st.expander("Column Mapping", expanded=False):
        mapping_df = pd.DataFrame({
            "Source Column": list(SETTINGS.COLUMN_ALIASES.keys()),
            "Internal Name": list(SETTINGS.COLUMN_ALIASES.values()),
        })
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)
    
    # Data preview
    with st.expander("Data Preview (first 10 rows)", expanded=True):
        if "preview_df" in result:
            st.dataframe(result["preview_df"], use_container_width=True, hide_index=True)
    
    # Proceed button
    st.divider()
    if result["valid"]:
        return st.button("▶ Run FibreOptima Analysis", type="primary", use_container_width=True)
    else:
        st.button("▶ Run Anyway (not recommended)", type="secondary", use_container_width=True, disabled=False)
        st.caption("Analysis will run but results may be affected by data issues.")
        return st.button("▶ Run Analysis", type="primary", use_container_width=True)
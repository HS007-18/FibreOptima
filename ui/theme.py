# FibreOptima Design System
# Industrial textile production intelligence theme

# Color Palette
COLORS = {
    # Risk levels
    "normal": "#27ae60",
    "warning": "#f39c12",
    "high_risk": "#c0392b",
    "data_issue": "#7f8c8d",
    
    # Brand
    "primary": "#1a3c5e",        # Industrial navy
    "primary_light": "#2c5f8a",
    "accent": "#3498db",
    "background": "#f7f9fc",
    "card_bg": "#ffffff",
    "border": "#e1e8ed",
    "text_primary": "#2c3e50",
    "text_secondary": "#5d6d7e",
    "text_muted": "#95a5a6",
}

# Risk Icons
RISK_ICONS = {
    "NORMAL": "✅",
    "WARNING": "⚠️",
    "HIGH RISK": "🔴",
    "DATA ISSUE": "⚫",
}

RISK_LABELS = {
    "NORMAL": "Normal",
    "WARNING": "Warning",
    "HIGH RISK": "High Risk",
    "DATA ISSUE": "Data Issue",
}

# Risk Sort Order (for display)
RISK_SORT_ORDER = {
    "HIGH RISK": 0,
    "WARNING": 1,
    "NORMAL": 2,
    "DATA ISSUE": 3,
}

# Spacing
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
}

# Typography
TYPOGRAPHY = {
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "heading_1": "1.75rem",
    "heading_2": "1.35rem",
    "heading_3": "1.1rem",
    "body": "0.95rem",
    "small": "0.85rem",
    "caption": "0.75rem",
}

# Chart Colors (Plotly)
CHART_COLORS = {
    "risk_pie": ["#27ae60", "#f39c12", "#c0392b", "#7f8c8d"],
    "risk_bar": {"NORMAL": "#27ae60", "WARNING": "#f39c12", "HIGH RISK": "#c0392b", "DATA ISSUE": "#7f8c8d"},
    "trend_normal": "#27ae60",
    "trend_warning": "#f39c12",
    "trend_high_risk": "#c0392b",
    "trend_data_issue": "#7f8c8d",
}


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    mapping = {
        "NORMAL": COLORS["normal"],
        "WARNING": COLORS["warning"],
        "HIGH RISK": COLORS["high_risk"],
        "DATA ISSUE": COLORS["data_issue"],
    }
    return mapping.get(risk_level, COLORS["text_muted"])


def get_risk_icon(risk_level: str) -> str:
    """Get icon for risk level."""
    return RISK_ICONS.get(risk_level, "⚪")


def format_risk_label(risk_level: str) -> str:
    """Get formatted label for risk level."""
    return RISK_LABELS.get(risk_level, risk_level)
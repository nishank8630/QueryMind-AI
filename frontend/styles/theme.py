"""Custom CSS stylesheet establishing the premium Blue-Black-White Enterprise Theme."""

CUSTOM_CSS = """
<style>
/* -------------------------------------------------------------
   QUERYMIND AI — PREMIUM BLUE-BLACK-WHITE ENTERPRISE THEME
   Midnight Blue Shell: #081426 | Dark Navy: #0D1B2A | Accent: #2563EB / #3B82F6
   ------------------------------------------------------------- */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #F8FAFC;
}

/* Background canvas */
.stApp {
    background: radial-gradient(circle at 50% 0%, #0d1e38 0%, #081426 65%, #050b14 100%) !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #070F1E !important;
    border-right: 1px solid #1E293B !important;
}

/* Brand Logo Treatment */
.brand-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0 24px 0;
    border-bottom: 1px solid #1E2E4A;
    margin-bottom: 20px;
}
.brand-logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: #FFFFFF;
    font-size: 20px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
}
.brand-title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #FFFFFF;
    margin: 0;
}
.brand-tagline {
    font-size: 11px;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0;
}

/* Metric / KPI Cards */
.kpi-card {
    background: linear-gradient(180deg, #0F223D 0%, #0B192C 100%);
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    border-color: #3B82F6;
    transform: translateY(-2px);
}
.kpi-title {
    font-size: 13px;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.5px;
}
.kpi-subtitle {
    font-size: 12px;
    color: #38BDF8;
    margin-top: 4px;
}

/* Query Pipeline Stages Bar */
.stage-pill-container {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}
.stage-pill {
    padding: 6px 14px;
    background: #0E2442;
    border: 1px solid #1E3E6B;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    color: #93C5FD;
}

/* SQL Code Block */
pre, code {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Result Tables */
[data-testid="stDataFrame"] {
    border: 1px solid #1E293B;
    border-radius: 10px;
    overflow: hidden;
}

/* Custom Alert Badges */
.badge-status {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-success {
    background-color: rgba(34, 197, 94, 0.15);
    color: #4ADE80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.badge-warning {
    background-color: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.badge-danger {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Form inputs & buttons */
.stButton>button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s ease !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
}
</style>
"""

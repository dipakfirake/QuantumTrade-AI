# =============================================================================
# Dashboard Custom CSS — Dark theme, professional styling
# =============================================================================

CUSTOM_CSS = """
<style>
    /* --- Premium Typography --- */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* --- Core Base Styles & Theme Responsiveness --- */
    :root {
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent-glow: rgba(59, 130, 246, 0.5);
        --gradient-text: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        --buy-color: #10b981;
        --sell-color: #ef4444;
        --font-main: 'Outfit', -apple-system, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    [data-theme="light"] {
        --glass-bg: rgba(255, 255, 255, 0.6);
        --glass-border: rgba(0, 0, 0, 0.1);
        --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --accent-glow: rgba(59, 130, 246, 0.3);
        --gradient-text: linear-gradient(135deg, #2563eb, #7c3aed, #db2777);
    }

    /* Target the main app container to enforce fonts and backgrounds */
    .stApp {
        font-family: var(--font-main);
        background-color: transparent !important;
    }
    
    /* Create an animated gradient background */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: linear-gradient(-45deg, #0a0e1a, #111827, #1e1b4b, #0f172a);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        z-index: -1;
    }

    [data-theme="light"] .stApp::before {
        background: linear-gradient(-45deg, #f8fafc, #f1f5f9, #e2e8f0, #e0e7ff);
        background-size: 400% 400%;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* --- Hide Streamlit Clutter --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    /* --- Custom Streamlit Inputs (Sidebar, etc) --- */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        font-family: var(--font-mono) !important;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 15px var(--accent-glow) !important;
    }
    
    /* Customize Sidebar */
    [data-testid="stSidebar"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-right: 1px solid var(--glass-border) !important;
    }

    /* --- Custom Streamlit Buttons --- */
    .stButton>button {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(168, 85, 247, 0.2)) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-main) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(168, 85, 247, 0.4)) !important;
        border-color: rgba(59, 130, 246, 0.6) !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px var(--accent-glow) !important;
    }

    /* --- Main Dashboard Header --- */
    .main-header {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        animation: fadeInDown 0.8s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
        opacity: 0.1;
        pointer-events: none;
        animation: pulseGlow 8s infinite alternate;
    }

    .main-header h1 {
        background: var(--gradient-text);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header .subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        gap: 15px;
        font-weight: 500;
    }

    /* Animated Live Dot */
    .live-dot {
        height: 10px; width: 10px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes pulseGlow {
        0% { transform: scale(1); opacity: 0.1; }
        100% { transform: scale(1.1); opacity: 0.2; }
    }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* --- Metric Cards --- */
    .metric-row {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    .metric-card {
        flex: 1;
        min-width: 180px;
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: var(--glass-shadow);
        animation: fadeInUp 0.8s ease-out backwards;
    }
    
    .metric-card:nth-child(1) { animation-delay: 0.1s; }
    .metric-card:nth-child(2) { animation-delay: 0.2s; }
    .metric-card:nth-child(3) { animation-delay: 0.3s; }
    .metric-card:nth-child(4) { animation-delay: 0.4s; }
    .metric-card:nth-child(5) { animation-delay: 0.5s; }

    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        border-color: rgba(255, 255, 255, 0.3);
    }
    [data-theme="light"] .metric-card:hover {
        box-shadow: 0 15px 35px rgba(31, 38, 135, 0.2);
    }

    .metric-card .label {
        font-size: 0.95rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-card .value {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    }
    .section-header h2 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 0;
    }
    .section-header .badge {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* --- Data tables --- */
    .stock-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.82rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    .stock-table thead th {
        background: rgba(30, 41, 59, 0.9);
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.5px;
        padding: 0.7rem 0.6rem;
        text-align: right;
        border-bottom: 2px solid rgba(59, 130, 246, 0.3);
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .stock-table thead th:first-child {
        text-align: left;
    }
    .stock-table tbody tr {
        transition: background 0.15s ease;
    }
    .stock-table tbody tr:nth-child(even) {
        background: rgba(30, 41, 59, 0.3);
    }
    .stock-table tbody tr:hover {
        background: rgba(59, 130, 246, 0.08);
    }
    .stock-table tbody td {
        padding: 0.55rem 0.6rem;
        text-align: right;
        border-bottom: 1px solid rgba(148, 163, 184, 0.06);
        color: #cbd5e1;
    }
    .stock-table tbody td:first-child {
        text-align: left;
        font-weight: 600;
        color: #f1f5f9;
    }

    /* --- Signal badges --- */
    .signal-buy {
        background: rgba(52, 211, 153, 0.15);
        color: #34d399;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .signal-sell {
        background: rgba(248, 113, 113, 0.15);
        color: #f87171;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .signal-none {
        color: #475569;
        font-size: 0.75rem;
    }

    /* --- ML prediction badges --- */
    .ml-accept {
        background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(16, 185, 129, 0.1));
        color: #34d399;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.78rem;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .ml-avoid {
        background: linear-gradient(135deg, rgba(248, 113, 113, 0.2), rgba(239, 68, 68, 0.1));
        color: #f87171;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.78rem;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }

    /* --- Signal cards --- */
    .signal-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        backdrop-filter: blur(10px);
    }
    .signal-card.buy-card {
        border-left: 4px solid #34d399;
    }
    .signal-card.sell-card {
        border-left: 4px solid #f87171;
    }
    .signal-card .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    .signal-card .card-header .symbol {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .signal-card .reason {
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.5;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
        font-family: 'Inter', monospace;
    }

    /* --- P&L coloring --- */
    .pnl-positive { color: #34d399; font-weight: 600; }
    .pnl-negative { color: #f87171; font-weight: 600; }

    /* --- Confidence bar --- */
    .confidence-bar {
        width: 80px;
        height: 6px;
        background: rgba(148, 163, 184, 0.2);
        border-radius: 3px;
        overflow: hidden;
        display: inline-block;
        vertical-align: middle;
        margin-left: 6px;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    .confidence-fill.high { background: linear-gradient(90deg, #34d399, #10b981); }
    .confidence-fill.medium { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
    .confidence-fill.low { background: linear-gradient(90deg, #f87171, #ef4444); }

    /* --- Pulse animation for live indicator --- */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    .live-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34d399;
        animation: pulse 1.5s infinite;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* --- Streamlit overrides --- */
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    div[data-testid="stMetricValue"] { font-family: 'Inter', sans-serif; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59, 130, 246, 0.2) !important;
        color: #60a5fa !important;
    }

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
    }

    /* --- Scrollbar --- */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.5); }
</style>
"""


def inject_css():
    """Inject custom CSS into Streamlit page."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

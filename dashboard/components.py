# =============================================================================
# Dashboard UI Components — Reusable Streamlit widgets
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional


def render_header(last_updated: str, stocks_scanned: int,
                  qualified: int, active_signals: int):
    """Render the main dashboard header."""
    st.markdown(f"""
    <div class="main-header">
        <h1>🌌 QuantumTrade AI — Institutional Market Screener</h1>
        <div class="subtitle">
            <span class="live-dot"></span>
            Last Updated: {last_updated} &nbsp;|&nbsp;
            Stocks Scanned: {stocks_scanned:,} &nbsp;|&nbsp;
            Qualified: {qualified} &nbsp;|&nbsp;
            Active Signals: {active_signals}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(stats: dict):
    """Render the top-level metric cards."""
    total = stats.get("total_trades", 0)
    wins = stats.get("winning_trades", 0)
    losses = stats.get("losing_trades", 0)
    win_rate = stats.get("win_rate", 0)
    total_pnl = stats.get("total_pnl", 0)
    open_pos = stats.get("open_positions", 0)

    pnl_class = "positive" if total_pnl >= 0 else "negative"
    pnl_symbol = "+" if total_pnl >= 0 else ""

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Total Trades</div>
            <div class="value blue">{total}</div>
        </div>
        <div class="metric-card">
            <div class="label">Win Rate</div>
            <div class="value {'positive' if win_rate > 50 else 'negative'}">{win_rate:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="label">Winning</div>
            <div class="value positive">{wins}</div>
        </div>
        <div class="metric-card">
            <div class="label">Losing</div>
            <div class="value negative">{losses}</div>
        </div>
        <div class="metric-card">
            <div class="label">Total P&L</div>
            <div class="value {pnl_class}">₹{pnl_symbol}{total_pnl:.2f}</div>
        </div>
        <div class="metric-card">
            <div class="label">Open Positions</div>
            <div class="value amber">{open_pos}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_screening_table(df: pd.DataFrame):
    """
    Render the main stock screening table.

    Expected columns: Symbol, LTP, SMMA_20, SMMA_120, Signal,
                      Bid_Price, Bid_Qty, Ask_Price, Ask_Qty,
                      Total_Bid_Qty, Total_Ask_Qty,
                      ETQ_5m, ETQ_20m, ETQ_60m,
                      Avg_LTP_20m, Avg_LTP_60m,
                      ML_Prediction, ML_Confidence, ML_Reason
    """
    if df.empty:
        st.info("🔍 No stocks currently match the screening criteria. "
                "Waiting for market data...")
        return

    # Build HTML table
    rows_html = ""
    for _, row in df.iterrows():
        signal = row.get("Signal", "—")
        if signal == "BUY":
            signal_html = '<span class="signal-buy">▲ BUY</span>'
        elif signal == "SELL":
            signal_html = '<span class="signal-sell">▼ SELL</span>'
        else:
            signal_html = '<span class="signal-none">—</span>'

        ml_pred = row.get("ML_Prediction", "")
        if ml_pred == "ACCEPT":
            ml_html = '<span class="ml-accept">✓ ACCEPT</span>'
        elif ml_pred == "AVOID":
            ml_html = '<span class="ml-avoid">✗ AVOID</span>'
        else:
            ml_html = '<span class="signal-none">—</span>'

        confidence = row.get("ML_Confidence", 0)
        conf_class = "high" if confidence > 0.65 else ("medium" if confidence > 0.5 else "low")
        conf_bar = f"""
            <span style="font-size:0.75rem">{confidence:.0%}</span>
            <div class="confidence-bar">
                <div class="confidence-fill {conf_class}" style="width:{confidence*100:.0f}%"></div>
            </div>
        """

        ltp = row.get("LTP", 0)
        smma20 = row.get("SMMA_20", 0)
        smma120 = row.get("SMMA_120", 0)

        rows_html += f"""<tr>
<td>{row.get('Symbol', '')}</td>
<td>₹{ltp:.2f}</td>
<td>{smma20:.2f}</td>
<td>{smma120:.2f}</td>
<td style="text-align:center">{signal_html}</td>
<td>₹{row.get('Bid_Price', 0):.2f}</td>
<td>{row.get('Bid_Qty', 0):,}</td>
<td>₹{row.get('Ask_Price', 0):.2f}</td>
<td>{row.get('Ask_Qty', 0):,}</td>
<td>{row.get('Total_Bid_Qty', 0):,}</td>
<td>{row.get('Total_Ask_Qty', 0):,}</td>
<td>{row.get('ETQ_5m', 0):,}</td>
<td>{row.get('ETQ_20m', 0):,}</td>
<td>{row.get('ETQ_60m', 0):,}</td>
<td>₹{row.get('Avg_LTP_20m', 0):.2f}</td>
<td>₹{row.get('Avg_LTP_60m', 0):.2f}</td>
<td style="text-align:center">{ml_html}</td>
<td style="text-align:center">{conf_bar}</td>
</tr>"""

    st.markdown(f"""
<div class="table-container">
    <div class="table-wrapper">
        <table class="stock-table">
            <thead>
                <tr>
                    <th style="text-align:left">Symbol</th>
                    <th>LTP</th>
                    <th>SMMA(20)</th>
                    <th>SMMA(120)</th>
                    <th style="text-align:center">Signal</th>
                    <th>Bid ₹</th>
                    <th>Bid Qty</th>
                    <th>Ask ₹</th>
                    <th>Ask Qty</th>
                    <th>Tot Bid Qty</th>
                    <th>Tot Ask Qty</th>
                    <th>ETQ 5m</th>
                    <th>ETQ 20m</th>
                    <th>ETQ 60m</th>
                    <th>Avg LTP 20m</th>
                    <th>Avg LTP 60m</th>
                    <th style="text-align:center">ML Prediction</th>
                    <th style="text-align:center">Confidence</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</div>
    """, unsafe_allow_html=True)


def render_signal_cards(signals: List[dict]):
    """Render AI/ML signal analysis cards."""
    if not signals:
        st.info("No crossover signals detected yet. Monitoring...")
        return

    for sig in signals:
        signal_type = sig.get("signal_type", "")
        card_class = "buy-card" if signal_type == "BUY" else "sell-card"
        signal_badge = "signal-buy" if signal_type == "BUY" else "signal-sell"
        arrow = "▲" if signal_type == "BUY" else "▼"
        ml_pred = sig.get("ml_prediction", "")
        ml_class = "ml-accept" if ml_pred == "ACCEPT" else "ml-avoid"
        ml_icon = "✓" if ml_pred == "ACCEPT" else "✗"

        reason = sig.get("ml_reason", "").replace("\n", "<br>")

        st.markdown(f"""
        <div class="signal-card {card_class}">
            <div class="card-header">
                <div>
                    <span class="symbol">{sig.get('symbol', '')}</span>
                    &nbsp;
                    <span class="{signal_badge}">{arrow} {signal_type}</span>
                </div>
                <div>
                    <span class="{ml_class}">{ml_icon} {ml_pred}</span>
                    &nbsp;
                    <span style="color:#94a3b8;font-size:0.8rem">
                        Confidence: {sig.get('ml_confidence', 0):.0%}
                    </span>
                </div>
            </div>
            <div style="color:#94a3b8;font-size:0.8rem;">
                LTP: ₹{sig.get('ltp', 0):.2f} &nbsp;|&nbsp;
                SMMA(20): {sig.get('smma_short', 0):.2f} &nbsp;|&nbsp;
                SMMA(120): {sig.get('smma_long', 0):.2f}
            </div>
            <div class="reason">{reason}</div>
        </div>
        """, unsafe_allow_html=True)


def render_trade_log(trades: List[dict]):
    """Render trade history table."""
    if not trades:
        st.info("No completed trades yet.")
        return

    rows_html = ""
    for t in trades:
        pnl = t.get("pnl", 0) or 0
        pnl_class = "pnl-positive" if pnl > 0 else "pnl-negative"
        signal_type = t.get("signal_type", "")
        signal_class = "signal-buy" if signal_type == "BUY" else "signal-sell"
        arrow = "▲" if signal_type == "BUY" else "▼"

        ml_pred = t.get("ml_prediction", "")
        ml_class = "ml-accept" if ml_pred == "ACCEPT" else ("ml-avoid" if ml_pred == "AVOID" else "signal-none")
        ml_text = f"✓ {ml_pred}" if ml_pred == "ACCEPT" else (f"✗ {ml_pred}" if ml_pred == "AVOID" else "—")

        rows_html += f"""
        <tr>
            <td>{t.get('symbol', '')}</td>
            <td style="text-align:center"><span class="{signal_class}">{arrow} {signal_type}</span></td>
            <td>₹{t.get('entry_ltp', 0):.2f}</td>
            <td>{t.get('entry_time', '')}</td>
            <td>₹{t.get('exit_ltp', 0):.2f}</td>
            <td>{t.get('exit_time', '')}</td>
            <td class="{pnl_class}">₹{pnl:+.2f}</td>
            <td style="text-align:center"><span class="{ml_class}">{ml_text}</span></td>
            <td>{t.get('ml_confidence', 0):.0%}</td>
        </tr>
        """

    st.markdown(f"""
    <div style="overflow-x:auto; border-radius:12px;">
    <table class="stock-table">
        <thead>
            <tr>
                <th style="text-align:left">Symbol</th>
                <th style="text-align:center">Signal</th>
                <th>Entry ₹</th>
                <th>Entry Time</th>
                <th>Exit ₹</th>
                <th>Exit Time</th>
                <th>P&L</th>
                <th style="text-align:center">ML</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


def render_feature_importance(importance: Dict[str, float]):
    """Render feature importance chart."""
    if not importance:
        st.info("Train the ML model to see feature importance.")
        return

    sorted_imp = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    names = list(sorted_imp.keys())
    values = list(sorted_imp.values())

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation='h',
        marker=dict(
            color=values,
            colorscale=[[0, '#1e3a5f'], [0.5, '#3b82f6'], [1, '#a78bfa']],
            line=dict(width=0),
        ),
    ))
    fig.update_layout(
        title="Feature Importance (XGBoost)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter'),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(title="Importance", gridcolor='rgba(148,163,184,0.1)'),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_market_depth_detail(depth_data: dict):
    """Render 5-level market depth for a specific stock."""
    bids = depth_data.get("bids", [])
    asks = depth_data.get("asks", [])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🟢 Bids (Buy Orders)**")
        if bids:
            bid_df = pd.DataFrame(bids)
            bid_df.columns = ["Price", "Quantity", "Orders"]
            st.dataframe(bid_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**🔴 Asks (Sell Orders)**")
        if asks:
            ask_df = pd.DataFrame(asks)
            ask_df.columns = ["Price", "Quantity", "Orders"]
            st.dataframe(ask_df, use_container_width=True, hide_index=True)


def render_pnl_chart(trades: List[dict]):
    """Render cumulative P&L chart."""
    if not trades:
        return

    pnls = [t.get("pnl", 0) or 0 for t in trades]
    cumulative = []
    total = 0
    for p in pnls:
        total += p
        cumulative.append(total)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=cumulative,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#60a5fa', width=2),
        fillcolor='rgba(96,165,250,0.1)',
        marker=dict(
            size=6,
            color=['#34d399' if p > 0 else '#f87171' for p in pnls],
        ),
    ))
    fig.update_layout(
        title="Cumulative P&L",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter'),
        xaxis=dict(title="Trade #", gridcolor='rgba(148,163,184,0.1)'),
        yaxis=dict(title="P&L (₹)", gridcolor='rgba(148,163,184,0.1)'),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

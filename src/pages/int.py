from __future__ import annotations

from pathlib import Path
from typing import Tuple, Set, Dict
import zlib
import json

import numpy as np
import pandas as pd
from dash import html, dcc, Input, Output, State, dash_table, no_update
from dash import callback_context as _ctx
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------- UI helpers ----------

# ---------- Commodity helpers ----------
COMMODITY_LIST = [
    "WTI Crude Oil",
    "Brent Crude Oil",
    "Palm Oil",
    "Soybean Oil",
    "Sunflower Oil",
]

_COMMODITY_CONFIG = {
    "WTI Crude Oil": {"base_price": 75.50, "volatility": 0.025},
    "Brent Crude Oil": {"base_price": 78.20, "volatility": 0.023},
    "Palm Oil": {"base_price": 850.30, "volatility": 0.035},
    "Soybean Oil": {"base_price": 45.20, "volatility": 0.030},
    "Sunflower Oil": {"base_price": 900.15, "volatility": 0.032},
}

# Fallback color palette for commodities (dash-friendly)
COMMODITY_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"
]

class _CommodityPriceGenerator:
    """Lightweight simulator for commodity OHLCV series."""
    def __init__(self, seed_base: int = 12345):
        self.seed_base = seed_base

    def generate_series(self, name: str, days: int = 30):
        import numpy as _np
        import pandas as _pd
        from datetime import datetime, timedelta

        cfg = _COMMODITY_CONFIG.get(name)
        if not cfg:
            raise ValueError(f"Unknown commodity: {name}")

        base = float(cfg["base_price"])  # starting point
        vol = float(cfg["volatility"])   # daily vol (stdev)

        dates = _pd.date_range(end=_pd.Timestamp.utcnow().normalize(), periods=days, freq="D")

        # Stable seed per commodity for reproducibility within a session
        _np.random.seed((hash(name) ^ self.seed_base) & 0xFFFFFFFF)
        changes = _np.random.normal(0, vol, days)
        trend = _np.linspace(0, 0.02, days)  # mild upward drift over window
        changes = changes + trend

        prices = [base]
        for ch in changes[1:]:
            prices.append(max(prices[-1] * (1 + ch), base * 0.5))

        o = [p * (1 + _np.random.normal(0, 0.005)) for p in prices]
        h = [p * (1 + abs(_np.random.normal(0, 0.01))) for p in prices]
        l = [p * (1 - abs(_np.random.normal(0, 0.01))) for p in prices]
        c = prices
        v = _np.random.randint(10_000, 100_000, days)

        df = _pd.DataFrame({
            "Open": o, "High": h, "Low": l, "Close": c, "Volume": v
        }, index=dates)
        df.index.name = "Date"
        df["High"] = df[["Open", "High", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)
        return df

    def generate_all(self, days: int = 30):
        return {name: self.generate_series(name, days) for name in COMMODITY_LIST}


_COMMOD_GEN = _CommodityPriceGenerator()

# --- Live API fetchers (optional, fallback to simulator) ---
import os, requests

class CommodityDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "demo")
        self.quandl_key = os.getenv("QUANDL_API_KEY", "demo")

    def fetch_alpha_vantage_daily(self, symbol: str):
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "compact",
            }
            r = self.session.get(url, params=params, timeout=20)
            j = r.json()
            key = next((k for k in j.keys() if "Time Series" in k), None)
            if not key:
                return None
            df = pd.DataFrame(j[key]).T
            # Standardize columns if present
            rename = {
                c: c.split(". ", 1)[1].capitalize() if ". " in c else c
                for c in df.columns
            }
            df = df.rename(columns=rename)
            for col in ("Open","High","Low","Close"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            if "Volume" in df.columns:
                df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
            return df[[c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]]
        except Exception:
            return None

    def fetch_quandl_dataset(self, dataset: str):
        try:
            url = f"https://www.quandl.com/api/v3/datasets/{dataset}/data.json"
            params = {"api_key": self.quandl_key, "limit": 200}
            r = self.session.get(url, params=params, timeout=20)
            j = r.json()
            if "dataset_data" not in j:
                return None
            cols = j["dataset_data"]["column_names"]
            data = j["dataset_data"]["data"]
            df = pd.DataFrame(data, columns=cols)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]) 
                df = df.set_index("Date").sort_index()
            return df
        except Exception:
            return None

    def series_for(self, commodity_name: str, days: int = 30):
        """Try real data for known commodities; else None."""
        # You can adjust the symbol mapping as needed for your account/data plan
        av_symbols = {
            "WTI Crude Oil": "CL=F",   # Front-month WTI (common ticker on some feeds)
            "Brent Crude Oil": "BZ=F", # Front-month Brent
        }
        if commodity_name in av_symbols:
            df = self.fetch_alpha_vantage_daily(av_symbols[commodity_name])
            if df is not None and not df.empty:
                # keep only the trailing window and fill any missing columns for consistency
                df = df.tail(days)
                for col in ("Open","High","Low","Close","Volume"):
                    if col not in df.columns:
                        df[col] = pd.NA
                return df
        # Example Quandl datasets for edible oils can be inserted here if you have access
        # e.g. df = self.fetch_quandl_dataset("COMMODITY/CODE"); return transformed OHLC if available
        return None

_API_FETCHER = CommodityDataFetcher()

def _maybe_fetch_or_simulate(name: str, days: int = 30):
    df = _API_FETCHER.series_for(name, days)
    if df is None or df.empty:
        return _COMMOD_GEN.generate_series(name, days)
    return df

# Sample regional edible oil data (can be wired to APIs later)
_REGIONAL_EDIBLE = {
    "North America": {"Palm Oil": 850.3, "Soybean Oil": 45.2, "Sunflower Oil": 900.1},
    "Europe": {"Palm Oil": 855.2, "Soybean Oil": 46.0, "Sunflower Oil": 895.4},
    "Asia": {"Palm Oil": 840.1, "Soybean Oil": 44.6, "Sunflower Oil": 910.3},
    "Middle East": {"Palm Oil": 845.6, "Soybean Oil": 44.9, "Sunflower Oil": 902.5},
}


def _commod_to_jsonable(dct):
    """Coerce a dict of DataFrames -> plain JSON structure."""
    base = {}
    for name, df in (dct or {}).items():
        if df is None or df.empty:
            base[name] = []
        else:
            tmp = df.reset_index().rename(columns={"Date": "date"})
            base[name] = tmp.to_dict("records")
    return base


def _commod_from_jsonable(data):
    import pandas as _pd
    out = {}
    for name, recs in (data or {}).items():
        if not recs:
            out[name] = _pd.DataFrame(columns=["Open","High","Low","Close","Volume"]).set_index(_pd.Index([], name="Date"))
        else:
            tmp = _pd.DataFrame(recs)
            if "date" in tmp.columns:
                tmp["date"] = _pd.to_datetime(tmp["date"])
                tmp = tmp.set_index("date").rename_axis("Date")
            out[name] = tmp
    return out
def clickable_stat_card(title: str, value_id: str, subtitle: str = "", value_class: str = "", click_id: str | None = None) -> html.Div:
    card = dbc.Card(
        [
            html.Div(title, className="text-muted mb-1"),
            html.Div(id=value_id, className=f"display-5 fw-semibold {value_class}".strip()),
            html.Div(subtitle, className="text-muted"),
        ],
        className="panel-card p-4 h-100 position-relative",
    )
    if click_id:
        card.children.append(
            html.Button(
                id=click_id,
                n_clicks=0,
                **{"aria-label": f"Show list for {title}"},
                style={"position": "absolute", "inset": 0, "opacity": 0, "border": 0, "background": "transparent", "cursor": "pointer"},
            )
        )
    return card


def stat_card(title: str, value_id: str, subtitle: str = "", value_class: str = "") -> html.Div:
    return dbc.Card(
        [
            html.Div(title, className="text-muted mb-1"),
            html.Div(id=value_id, className=f"display-5 fw-semibold {value_class}".strip()),
            html.Div(subtitle, className="text-muted"),
        ],
        className="panel-card p-4 h-100",
    )


def _root_cause_cards() -> html.Div:
    process = dbc.Card(
        [
            html.Div("Process Issues", className="fw-semibold mb-2 px-3 py-2 bg-light border-bottom"),
            dbc.Table(
                [html.Tbody([
                    html.Tr([html.Td("Risky Mixing Ratio"), html.Td("61.29% (285/465)", className="text-muted text-end")]),
                    # html.Tr([html.Td("Measured elongation ± 6%"), html.Td("100%", className="text-muted text-end")]),
                ])],
                bordered=False, hover=False, responsive=True, className="mb-0",
            ),
        ],
        className="panel-card p-0",
    )

    data_integrity = dbc.Card(
        [
            html.Div("Data Integrity", className="fw-semibold mb-2 px-3 py-2 bg-light border-bottom"),
            dbc.Table(
                [html.Tbody([
                    html.Tr([html.Td(html.Span("Suspect QA passes", className="text-decoration-underline")), html.Td("4%", className="text-muted text-end")]),
                    html.Tr([html.Td("Missing Tensioning Data"), html.Td("26.41%", className="text-muted text-end")]),
                    html.Tr([html.Td("Missing Vibration Data"), html.Td("53.68%", className="text-muted text-end")]),
                ])],
                bordered=False, hover=False, responsive=True, className="mb-0",
            ),
        ],
        className="panel-card p-0",
    )

    return html.Div(
        [
            dbc.Card([html.H4("Root Cause Analysis", className="mb-0")], className="panel-card p-3 mb-2"),
            dbc.Row([dbc.Col(process, md=6), dbc.Col(data_integrity, md=6)], className="g-3"),
        ]
    )


def layout():
    # Date range default: last 30 days ending today (UTC)
    today = pd.Timestamp.utcnow().normalize()
    start_default = (today - pd.Timedelta(days=29)).date()
    end_default = today.date()

    header_bar = html.Div(
        [
            html.H2("Live Commodity Price Dashboard", className="mb-0"),
            html.Div(
                [
                    html.Div("Date range", className="small text-muted text-end mb-1"),
                    dcc.DatePickerRange(
                        id="commod-date-range",
                        min_date_allowed=(today - pd.Timedelta(days=365)).date(),
                        max_date_allowed=end_default,
                        start_date=start_default,
                        end_date=end_default,
                        display_format="YYYY-MM-DD",
                        clearable=False,
                        updatemode="bothdates",
                    ),
                ],
                className="d-flex flex-column align-items-end",
                style={"minWidth": "280px"},
            ),
        ],
        className="header-bar mb-2",
    )

    # Stores & timer
    stores = html.Div([
        dcc.Store(id="commod-data-store"),
        dcc.Store(id="commod-analytics-store"),
        dcc.Interval(id="commod-interval", interval=5*60*1000, n_intervals=0),  # 5 minutes
    ])

    # KPI Cards
    def _kpi_card(title, value_id, sub_id):
        return dbc.Card(
            [
                html.Div(title, className="text-muted mb-1"),
                html.Div(id=value_id, className="display-5 fw-semibold"),
                html.Div(id=sub_id, className="text-muted"),
            ],
            className="panel-card p-4 h-100",
        )

    kpi_row = dbc.Row([
        dbc.Col(_kpi_card("WTI Crude Oil", "kpi-wti", "kpi-wti-sub"), md=3),
        dbc.Col(_kpi_card("Brent Crude Oil", "kpi-brent", "kpi-brent-sub"), md=3),
        dbc.Col(_kpi_card("Palm Oil", "kpi-palm", "kpi-palm-sub"), md=3),
        dbc.Col(_kpi_card("Soybean Oil", "kpi-soy", "kpi-soy-sub"), md=3),
    ], className="g-4 mb-3")

    kpi_row_2 = dbc.Row([
        dbc.Col(_kpi_card("Sunflower Oil", "kpi-sun", "kpi-sun-sub"), md=3),
        dbc.Col(
            dbc.Card([
                html.Div("Update Controls", className="text-muted mb-2"),
                dbc.Row([
                    dbc.Col(dbc.Button("Refresh Now", id="btn-refresh", color="info", className="me-2"), width="auto"),
                    dbc.Col(dbc.Checklist(
                        options=[{"label": " Auto-refresh (5m)", "value": "on"}],
                        value=["on"], id="chk-auto", switch=True,
                    ), width="auto"),
                    dbc.Col(dbc.Checklist(
                        options=[{"label": " Use Real APIs", "value": "real"}],
                        value=[], id="chk-real-apis", switch=True,
                    ), width="auto"),
                ], className="g-2 align-items-center"),
            ], className="panel-card p-4 h-100"), md=5),
        dbc.Col(
            dbc.Card([
                html.Div("Status", className="text-muted mb-1"),
                html.Div(id="commod-status", className="fw-semibold"),
            ], className="panel-card p-4 h-100"), md=4),
    ], className="g-4 mb-3")

    # Detail & Region controls
    controls_row = dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Div("Commodity Detail", className="text-muted mb-2"),
                dbc.Row([
                    dbc.Col(dcc.Dropdown(
                        id="commod-detail-select",
                        options=[{"label": c, "value": c} for c in COMMODITY_LIST],
                        value="WTI Crude Oil",
                        clearable=False,
                    ), md=6),
                    dbc.Col(dbc.Checklist(
                        id="detail-candlestick",
                        options=[{"label": " Candlestick mode", "value": "candle"}],
                        value=["candle"], switch=True,
                    ), md="auto"),
                ], className="g-3"),
                dbc.Checklist(
                    id="detail-overlays",
                    options=[
                        {"label": " SMA 7", "value": "sma7"},
                        {"label": " SMA 30", "value": "sma30"},
                        {"label": " EMA 12", "value": "ema12"},
                        {"label": " EMA 26", "value": "ema26"},
                    ],
                    value=["sma7", "sma30"], inline=True,
                ),
            ], className="panel-card p-4 h-100"), md=7),
        dbc.Col(
            dbc.Card([
                html.Div("Region Selector", className="text-muted mb-2"),
                dcc.Dropdown(
                    id="region-select",
                    options=[{"label": r, "value": r} for r in _REGIONAL_EDIBLE.keys()],
                    value="Asia", clearable=False,
                ),
            ], className="panel-card p-4 h-100"), md=5),
    ], className="g-4 mb-3")

    # Charts
    main_line = dbc.Card([
        html.Div("Live Prices (Close)", className="text-muted mb-2"),
        dcc.Graph(id="commod-price-line", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    change_heatmap = dbc.Card([
        html.Div("Daily % Change Heatmap", className="text-muted mb-2"),
        dcc.Graph(id="commod-change-heatmap", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    regional_card = dbc.Card([
        html.Div("Regional Snapshot (sampled)", className="text-muted mb-2"),
        dcc.Graph(id="commod-regional", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    analytics_card = dbc.Card([
        html.Div("Volatility & Trend", className="text-muted mb-2"),
        dcc.Graph(id="commod-analytics", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    # Detail chart & Edible oils per-region cards
    detail_card = dbc.Card([
        html.Div("Selected Commodity (Candlestick/Line + MAs)", className="text-muted mb-2"),
        dcc.Graph(id="commod-detail-chart", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    edible_region_card = dbc.Card([
        html.Div("Edible Oils by Region", className="text-muted mb-2"),
        dcc.Graph(id="edible-oil-region-graph", config={"displayModeBar": False}),
    ], className="panel-card p-4")

    charts = dbc.Row([
        dbc.Col(detail_card, md=12),
        dbc.Col(main_line, md=12),
        dbc.Col(change_heatmap, md=12),
        dbc.Col(edible_region_card, md=12),
        dbc.Col(regional_card, md=12),
        dbc.Col(analytics_card, md=12),
    ], className="g-3 mt-3")

    return html.Div([
        dbc.Card([header_bar], className="panel-card p-4 mb-3"),
        stores,
        kpi_row,
        kpi_row_2,
        controls_row,
        charts,
    ], className="p-4")


def register_callbacks(app):
    # --- Helpers to build figures ---
    def _build_price_line(data_map):
        fig = go.Figure()
        if not data_map:
            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            return fig
        for i, (name, df) in enumerate(data_map.items()):
            if df is None or df.empty:
                continue
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines+markers",
                name=name,
                line=dict(width=2, color=COMMODITY_COLORS[i % len(COMMODITY_COLORS)]),
                marker=dict(size=5),
                hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>",
            ))
        fig.update_layout(
            title=dict(text="Live Commodity Prices Comparison", x=0.5, xanchor="center"),
            xaxis_title=None,
            yaxis_title="Price (USD)",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=40, b=0, l=0, r=0),
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        return fig

    def _build_change_heatmap(data_map):
        import numpy as _np
        import pandas as _pd
        changes = {}
        for name, df in (data_map or {}).items():
            if df is None or df.empty:
                continue
            s = df["Close"].pct_change() * 100
            changes[name] = s.dropna()
        if not changes:
            return go.Figure()
        max_len = max(len(s) for s in changes.values())
        mat = []
        labels = []
        for name, s in changes.items():
            v = s.reset_index(drop=True)
            if len(v) < max_len:
                v = v.reindex(range(max_len))
            mat.append(v.values)
            labels.append(name)
        z = _np.array(mat)
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=list(range(z.shape[1])),
            y=labels,
            colorscale="RdYlGn",
            zmid=0,
            hovertemplate="Commodity: %{y}<br>Day: %{x}<br>Change: %{z:.2f}%<extra></extra>",
        ))
        fig.update_layout(template="plotly_white", height=350, margin=dict(t=40, b=0, l=0, r=0))
        fig.update_xaxes(title_text="Days Ago")
        fig.update_yaxes(title_text="Commodity")
        return fig

    def _build_regional():
        # Sampled static regional data (API wiring can replace this later)
        regional = {
            "North America": {"WTI": 75.50, "Brent": 78.20},
            "Europe": {"WTI": 76.10, "Brent": 78.20},
            "Asia": {"WTI": 75.80, "Brent": 78.50},
            "Middle East": {"WTI": 75.30, "Brent": 78.00},
        }
        fig = go.Figure()
        for region, prices in regional.items():
            fig.add_trace(go.Bar(
                name=region,
                x=list(prices.keys()),
                y=list(prices.values()),
                hovertemplate=f"<b>{region}</b><br>Oil: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>",
            ))
        fig.update_layout(
            title="Regional Oil Price Comparison",
            xaxis_title="Oil Type",
            yaxis_title="Price (USD)",
            barmode="group",
            template="plotly_white",
            height=420,
            margin=dict(t=40, b=0, l=0, r=0),
        )
        return fig

    def _build_analytics_scatter(analytics_df):
        fig = go.Figure()
        if analytics_df is None or analytics_df.empty:
            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            return fig
        fig.add_trace(go.Scatter(
            x=analytics_df["trend_vs_ma7"],
            y=analytics_df["trend_vs_ma30"],
            mode="markers+text",
            text=analytics_df.index,
            textposition="top center",
            marker=dict(size=14),
            name="Trend Position",
            hovertemplate=(
                "<b>%{text}</b><br>vs MA7: %{x:.2f}%<br>vs MA30: %{y:.2f}%<extra></extra>"
            ),
        ))
        fig.update_layout(
            template="plotly_white",
            height=420,
            margin=dict(t=40, b=0, l=0, r=0),
            xaxis_title="vs MA7 (%)",
            yaxis_title="vs MA30 (%)",
        )
        return fig

    # --- Data refresh & stores ---
    @app.callback(
        Output("commod-data-store", "data"),
        Output("commod-status", "children"),
        Input("commod-date-range", "start_date"),
        Input("commod-date-range", "end_date"),
        Input("commod-interval", "n_intervals"),
        Input("btn-refresh", "n_clicks"),
        Input("chk-real-apis", "value"),
        prevent_initial_call=False,
    )
    def refresh_data(start_date, end_date, n_intervals, n_clicks, real_toggle):
        # Respect auto-refresh toggle by disabling Interval elsewhere
        start = pd.to_datetime(start_date) if start_date else None
        end = pd.to_datetime(end_date) if end_date else None
        days = 30
        if start is not None and end is not None:
            days = max(2, int((end.normalize() - start.normalize()).days) + 1)
        use_real = bool(real_toggle and "real" in real_toggle)
        data_map = {}
        for name in COMMODITY_LIST:
            if use_real:
                df = _maybe_fetch_or_simulate(name, days)
            else:
                df = _COMMOD_GEN.generate_series(name, days)
            data_map[name] = df
        status = f"Updated {pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M UTC')} (window: {days} days){' [real API]' if use_real else ' [simulated]'}"
        return _commod_to_jsonable(data_map), status

    @app.callback(
        Output("commod-detail-chart", "figure"),
        Input("commod-data-store", "data"),
        Input("commod-detail-select", "value"),
        Input("detail-candlestick", "value"),
        Input("detail-overlays", "value"),
        prevent_initial_call=False,
    )
    def render_detail_chart(store, name, candle_toggle, overlays):
        df_map = _commod_from_jsonable(store)
        df = df_map.get(name)
        fig = go.Figure()
        if df is None or df.empty:
            fig.update_layout(template="plotly_white", height=420, margin=dict(t=40, b=0, l=0, r=0))
            return fig
        use_candle = bool(candle_toggle and "candle" in candle_toggle)
        if use_candle and all(col in df.columns for col in ("Open","High","Low","Close")):
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                name=name,
            ))
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name=f"{name} Close"))
        # Overlays
        ovs = set(overlays or [])
        def _ma(series, w, ema=False):
            if ema:
                return series.ewm(span=w, adjust=False, min_periods=1).mean()
            return series.rolling(window=min(w, len(series))).mean()
        if "sma7" in ovs:
            fig.add_trace(go.Scatter(x=df.index, y=_ma(df["Close"], 7), name="SMA 7", line=dict(dash="dash")))
        if "sma30" in ovs:
            fig.add_trace(go.Scatter(x=df.index, y=_ma(df["Close"], 30), name="SMA 30", line=dict(dash="dash")))
        if "ema12" in ovs:
            fig.add_trace(go.Scatter(x=df.index, y=_ma(df["Close"], 12, ema=True), name="EMA 12", line=dict(dash="dot")))
        if "ema26" in ovs:
            fig.add_trace(go.Scatter(x=df.index, y=_ma(df["Close"], 26, ema=True), name="EMA 26", line=dict(dash="dot")))
        fig.update_layout(template="plotly_white", height=420, margin=dict(t=40, b=0, l=0, r=0),
                          hovermode="x unified", xaxis_title=None, yaxis_title="Price (USD)")
        return fig

    @app.callback(
        Output("edible-oil-region-graph", "figure"),
        Input("region-select", "value"),
        prevent_initial_call=False,
    )
    def render_edible_by_region(region):
        # If single region selected, show bar of edible oils; could be extended to multi-select
        region = region or "Asia"
        data = _REGIONAL_EDIBLE.get(region, {})
        names = list(data.keys())
        vals = [data[k] for k in names]
        fig = go.Figure(go.Bar(x=names, y=vals))
        fig.update_layout(template="plotly_white", height=380, margin=dict(t=40, b=0, l=0, r=0),
                          xaxis_title="Edible Oil", yaxis_title="Price (USD)", title=f"{region}")
        return fig

    # Enable/disable interval based on toggle
    @app.callback(
        Output("commod-interval", "disabled"),
        Input("chk-auto", "value"),
        prevent_initial_call=False,
    )
    def toggle_interval(value):
        return False if (value and "on" in value) else True

    # KPIs + charts
    @app.callback(
        Output("kpi-wti", "children"),
        Output("kpi-wti-sub", "children"),
        Output("kpi-brent", "children"),
        Output("kpi-brent-sub", "children"),
        Output("kpi-palm", "children"),
        Output("kpi-palm-sub", "children"),
        Output("kpi-soy", "children"),
        Output("kpi-soy-sub", "children"),
        Output("kpi-sun", "children"),
        Output("kpi-sun-sub", "children"),
        Output("commod-price-line", "figure"),
        Output("commod-change-heatmap", "figure"),
        Output("commod-regional", "figure"),
        Output("commod-analytics", "figure"),
        Input("commod-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_views(store):
        import numpy as _np
        data_map = _commod_from_jsonable(store)

        # Compute KPI values
        def _kpi_for(name):
            df = data_map.get(name)
            if df is None or df.empty or "Close" not in df:
                return ("-", "")
            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else latest
            chg = ((latest - prev) / prev * 100.0) if prev else 0.0
            arrow = "▲" if chg >= 0 else "▼"
            color = "text-success" if chg >= 0 else "text-danger"
            return (f"${latest:.2f}", html.Span(f"{arrow} {chg:+.2f}% vs prev", className=color))

        wti_v, wti_s = _kpi_for("WTI Crude Oil")
        br_v, br_s = _kpi_for("Brent Crude Oil")
        pa_v, pa_s = _kpi_for("Palm Oil")
        so_v, so_s = _kpi_for("Soybean Oil")
        su_v, su_s = _kpi_for("Sunflower Oil")

        # Build figures
        line_fig = _build_price_line(data_map)
        heat_fig = _build_change_heatmap(data_map)
        regional_fig = _build_regional()

        # Analytics dataframe
        rows = []
        idx = []
        for name, df in data_map.items():
            if df is None or df.empty:
                continue
            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else latest
            ret = df["Close"].pct_change().dropna()
            vol = (ret.rolling(window=min(30, len(ret))).std().iloc[-1] * 100.0) if not ret.empty else 0.0
            ma7 = df["Close"].rolling(window=min(7, len(df))).mean().iloc[-1]
            ma30 = df["Close"].rolling(window=min(30, len(df))).mean().iloc[-1]
            t7 = ((latest - ma7) / ma7 * 100.0) if ma7 else 0.0
            t30 = ((latest - ma30) / ma30 * 100.0) if ma30 else 0.0
            rows.append({"trend_vs_ma7": t7, "trend_vs_ma30": t30, "volatility": vol})
            idx.append(name)
        analytics_df = pd.DataFrame(rows, index=idx)
        analytics_fig = _build_analytics_scatter(analytics_df)

        return (
            wti_v, wti_s,
            br_v, br_s,
            pa_v, pa_s,
            so_v, so_s,
            su_v, su_s,
            line_fig, heat_fig, regional_fig, analytics_fig,
        )
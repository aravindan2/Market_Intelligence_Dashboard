"""
Live Prices & News: scraped/simulated/dynamic prices + RSS news panel.
"""
from __future__ import annotations

import pandas as pd
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from data.price_scraper import get_all_historical, DEFAULT_TICKERS
from data.rss_feeds import get_news_items
from data.dynamic_pricing import get_dynamic_prices

# Reuse int helpers for simulated data and jsonable format
from pages import int as int_page

COMMODITY_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def _commod_to_jsonable(dct):
    base = {}
    for name, df in (dct or {}).items():
        if df is None or df.empty:
            base[name] = []
        else:
            tmp = df.reset_index().rename(columns={"Date": "date"})
            base[name] = tmp.to_dict("records")
    return base


def _build_price_line(data_map):
    fig = go.Figure()
    if not data_map:
        fig.update_layout(template="plotly_white", height=400, margin=dict(t=40, b=0, l=0, r=0))
        return fig
    for i, (name, df) in enumerate(data_map.items()):
        if df is None or df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines+markers", name=name,
            line=dict(width=2, color=COMMODITY_COLORS[i % len(COMMODITY_COLORS)]),
            hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        xaxis_title=None, yaxis_title="Price (USD)", hovermode="x unified",
        template="plotly_white", height=400, margin=dict(t=40, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def _build_change_heatmap(data_map):
    import numpy as np
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
    z = np.array(mat)
    fig = go.Figure(go.Heatmap(z=z, x=list(range(z.shape[1])), y=labels, colorscale="RdYlGn", zmid=0))
    fig.update_layout(template="plotly_white", height=320, margin=dict(t=40, b=0, l=0, r=0))
    return fig


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Live Prices & News", className="mb-0"),
                    html.Div(id="live-status", className="text-muted small mt-1"),
                ],
                className="header-bar mb-3",
            ),
            dcc.Store(id="live-data-store", data=None),
            dcc.Store(id="live-news-store", data=None),
            dcc.Interval(id="live-interval", interval=5 * 60 * 1000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    html.Div("Data source", className="text-muted mb-2"),
                                    dcc.Dropdown(
                                        id="live-source",
                                        options=[
                                            {"label": "Scraped (Yahoo)", "value": "scraped"},
                                            {"label": "Simulated", "value": "simulated"},
                                            {"label": "Dynamic (your code)", "value": "dynamic"},
                                        ],
                                        value="scraped",
                                        clearable=False,
                                    ),
                                    dbc.Button("Refresh", id="live-btn-refresh", color="primary", size="sm", className="mt-2"),
                                ],
                                className="panel-card p-4 mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Card([html.Div("WTI", className="text-muted small"), html.Div(id="live-kpi-wti", className="h5"), html.Div(id="live-kpi-wti-sub", className="small")], className="panel-card p-3"), md=3),
                                    dbc.Col(dbc.Card([html.Div("Brent", className="text-muted small"), html.Div(id="live-kpi-brent", className="h5"), html.Div(id="live-kpi-brent-sub", className="small")], className="panel-card p-3"), md=3),
                                    dbc.Col(dbc.Card([html.Div("Soybean Oil", className="text-muted small"), html.Div(id="live-kpi-soy", className="h5"), html.Div(id="live-kpi-soy-sub", className="small")], className="panel-card p-3"), md=3),
                                ],
                                className="g-2 mb-3",
                            ),
                            dbc.Card([html.Div("Live Prices (Close)", className="text-muted mb-2"), dcc.Graph(id="live-price-line", config={"displayModeBar": False})], className="panel-card p-4 mb-3"),
                            dbc.Card([html.Div("Daily % Change Heatmap", className="text-muted mb-2"), dcc.Graph(id="live-heatmap", config={"displayModeBar": False})], className="panel-card p-4"),
                        ],
                        md=7,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("News", className="text-muted mb-2"),
                                html.Div(id="live-news-panel", className="overflow-auto", style={"maxHeight": "600px"}),
                            ],
                            className="panel-card p-4 h-100",
                        ),
                        md=5,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="p-4",
    )


def register_callbacks(app):
    @app.callback(
        Output("live-data-store", "data"),
        Output("live-news-store", "data"),
        Output("live-status", "children"),
        Input("live-source", "value"),
        Input("live-interval", "n_intervals"),
        Input("live-btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_live(source, n_intervals, n_clicks):
        source = source or "scraped"
        data_map = {}
        if source == "scraped":
            data_map = get_all_historical(DEFAULT_TICKERS, days=90)
        elif source == "simulated":
            data_map = int_page._COMMOD_GEN.generate_all(90)
        elif source == "dynamic":
            dyn = get_dynamic_prices()
            if dyn is not None:
                if isinstance(dyn, dict):
                    for name, price in dyn.items():
                        if isinstance(price, (int, float)):
                            dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=30, freq="D")
                            data_map[name] = pd.DataFrame({"Open": price, "High": price, "Low": price, "Close": price, "Volume": 0}, index=dates)
                            data_map[name].index.name = "Date"
            if not data_map:
                data_map = get_all_historical(DEFAULT_TICKERS, days=90)
        try:
            news = get_news_items(max_items=25)
        except Exception:
            news = []
        ts = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        status = f"Last updated {ts} · Source: {source}"
        return _commod_to_jsonable(data_map), news, status

    @app.callback(
        Output("live-kpi-wti", "children"),
        Output("live-kpi-wti-sub", "children"),
        Output("live-kpi-brent", "children"),
        Output("live-kpi-brent-sub", "children"),
        Output("live-kpi-soy", "children"),
        Output("live-kpi-soy-sub", "children"),
        Output("live-price-line", "figure"),
        Output("live-heatmap", "figure"),
        Input("live-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_live_views(store):
        data_map = int_page._commod_from_jsonable(store)

        def kpi(name):
            df = data_map.get(name)
            if df is None or df.empty:
                return ("–", "")
            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else latest
            chg = ((latest - prev) / prev * 100.0) if prev else 0.0
            arrow = "▲" if chg >= 0 else "▼"
            sub = html.Span(f"{arrow} {chg:+.2f}%", className="text-success" if chg >= 0 else "text-danger")
            return (f"${latest:.2f}", sub)

        wti_v, wti_s = kpi("WTI Crude Oil")
        br_v, br_s = kpi("Brent Crude Oil")
        soy_v, soy_s = kpi("Soybean Oil")
        line_fig = _build_price_line(data_map)
        heat_fig = _build_change_heatmap(data_map)
        return wti_v, wti_s, br_v, br_s, soy_v, soy_s, line_fig, heat_fig

    @app.callback(
        Output("live-news-panel", "children"),
        Input("live-news-store", "data"),
        prevent_initial_call=False,
    )
    def update_news(news):
        if not news:
            return html.Div("No news items.", className="text-muted small")
        return html.Ul(
            [
                html.Li(
                    [html.A(item.get("title", "—"), href=item.get("link", "#"), target="_blank", rel="noopener", className="text-decoration-none"), html.Div([item.get("source", ""), " · ", item.get("published", "")], className="small text-muted mt-1")],
                    className="mb-3 border-bottom pb-2",
                )
                for item in news[:20]
            ],
            className="list-unstyled mb-0",
        )

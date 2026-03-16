"""
Markets Deep Dive: correlation matrix, volatility, tables from scraped series.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from data.price_scraper import get_all_historical, get_latest_prices, DEFAULT_TICKERS


def layout():
    return html.Div(
        [
            html.H2("Markets Deep Dive", className="mb-2"),
            html.P("Correlation, volatility, and latest levels.", className="text-muted mb-3"),
            dcc.Store(id="deep-data-store", data=None),
            dcc.Interval(id="deep-interval", interval=5 * 60 * 1000, n_intervals=0),
            dbc.Button("Refresh", id="deep-btn-refresh", color="primary", size="sm", className="mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Correlation matrix", className="text-muted mb-2"),
                                dcc.Graph(id="deep-correlation", config={"displayModeBar": False}),
                            ],
                            className="panel-card p-4",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Rolling volatility (30d)", className="text-muted mb-2"),
                                dcc.Graph(id="deep-volatility", config={"displayModeBar": False}),
                            ],
                            className="panel-card p-4",
                        ),
                        md=6,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div("Latest levels & change", className="text-muted mb-2"),
                            dbc.Table(id="deep-levels-table", bordered=False, hover=True, className="mb-0"),
                        ],
                        className="panel-card p-4",
                    ),
                ),
            ),
        ],
        className="p-4",
    )


def _data_to_jsonable(data_map):
    out = {}
    for name, df in (data_map or {}).items():
        if df is None or df.empty:
            out[name] = []
        else:
            tmp = df.reset_index().rename(columns={"Date": "date"})
            out[name] = tmp.to_dict("records")
    return out


def _jsonable_to_data(data):
    out = {}
    for name, recs in (data or {}).items():
        if not recs:
            out[name] = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"]).set_index(pd.Index([], name="Date"))
        else:
            tmp = pd.DataFrame(recs)
            if "date" in tmp.columns:
                tmp["date"] = pd.to_datetime(tmp["date"])
                tmp = tmp.set_index("date").rename_axis("Date")
            out[name] = tmp
    return out


def register_callbacks(app):
    @app.callback(
        Output("deep-data-store", "data"),
        Input("deep-interval", "n_intervals"),
        Input("deep-btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_deep(n_intervals, n_clicks):
        data_map = get_all_historical(DEFAULT_TICKERS, days=90)
        return _data_to_jsonable(data_map)

    @app.callback(
        Output("deep-correlation", "figure"),
        Output("deep-volatility", "figure"),
        Output("deep-levels-table", "children"),
        Input("deep-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_deep_views(store):
        data_map = _jsonable_to_data(store)
        if not data_map:
            empty = go.Figure()
            empty.update_layout(template="plotly_white", height=350, margin=dict(t=20, b=0, l=0, r=0))
            return empty, empty, [html.Thead(html.Tr([html.Th("Name"), html.Th("Last"), html.Th("Change %")])), html.Tbody([html.Tr([html.Td("No data")])])]

        # Correlation matrix: daily returns
        closes = pd.DataFrame({name: df["Close"] for name, df in data_map.items() if df is not None and not df.empty})
        if closes.empty or len(closes) < 2:
            corr_fig = go.Figure()
            corr_fig.update_layout(template="plotly_white", height=350)
        else:
            ret = closes.pct_change().dropna()
            corr = ret.corr()
            corr_fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, colorscale="RdBu", zmid=0, zmin=-1, zmax=1))
            corr_fig.update_layout(template="plotly_white", height=350, margin=dict(t=40, b=0, l=0, r=0), xaxis_title="", yaxis_title="")

        # Rolling volatility (30d std of daily return * sqrt(252) or just daily %)
        vol_series = {}
        for name, df in data_map.items():
            if df is None or df.empty or "Close" not in df.columns:
                continue
            r = df["Close"].pct_change().dropna()
            vol_series[name] = r.rolling(30).std() * 100
        if vol_series:
            vol_df = pd.DataFrame(vol_series).dropna(how="all")
            vol_fig = go.Figure()
            for col in vol_df.columns:
                vol_fig.add_trace(go.Scatter(x=vol_df.index, y=vol_df[col], mode="lines", name=col))
            vol_fig.update_layout(template="plotly_white", height=350, margin=dict(t=40, b=0, l=0, r=0), yaxis_title="Vol %", legend=dict(orientation="h"))
        else:
            vol_fig = go.Figure()
            vol_fig.update_layout(template="plotly_white", height=350)

        # Table: latest level, change %
        rows = []
        for name, df in data_map.items():
            if df is None or df.empty:
                rows.append(html.Tr([html.Td(name), html.Td("–"), html.Td("–")]))
                continue
            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else latest
            chg = ((latest - prev) / prev * 100.0) if prev else 0.0
            chg_cls = "text-success" if chg >= 0 else "text-danger"
            rows.append(html.Tr([html.Td(name), html.Td(f"${latest:.2f}"), html.Td(html.Span(f"{chg:+.2f}%", className=chg_cls))]))
        thead = html.Thead(html.Tr([html.Th("Commodity"), html.Th("Last price"), html.Th("Change %")]))
        tbody = html.Tbody(rows)
        return corr_fig, vol_fig, [thead, tbody]

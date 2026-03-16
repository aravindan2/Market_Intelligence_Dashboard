"""
Global Command Center: KPIs from scraper, world map, news ticker.
"""
from __future__ import annotations

from datetime import datetime

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from data.price_scraper import get_latest_prices, DEFAULT_TICKERS
from data.rss_feeds import get_news_items

# Country ISO -> price index for map (derived from regional; can use scraped later)
COUNTRY_PRICE_MAP = {
    "USA": 75.5, "CAN": 75.5, "MEX": 75.8,
    "GBR": 78.2, "DEU": 78.0, "FRA": 78.1, "ITA": 77.9, "ESP": 77.8,
    "RUS": 76.5, "CHN": 75.8, "IND": 76.2, "JPN": 78.5, "KOR": 77.0,
    "SAU": 76.0, "ARE": 76.2, "IRQ": 75.8, "IRN": 75.5,
    "BRA": 75.2, "ZAF": 76.8, "AUS": 77.5, "NGA": 75.0,
}


def _build_map_figure(prices: dict) -> go.Figure:
    """Choropleth: countries with color = price level."""
    if not prices:
        locs, z = list(COUNTRY_PRICE_MAP.keys()), list(COUNTRY_PRICE_MAP.values())
    else:
        # Use first available price as baseline and scale regionally
        vals = [v for v in prices.values() if isinstance(v, (int, float))]
        baseline = sum(vals) / len(vals) if vals else 76.0
        locs = list(COUNTRY_PRICE_MAP.keys())
        z = [COUNTRY_PRICE_MAP[c] for c in locs]
    fig = go.Figure(
        go.Choropleth(
            locations=locs,
            z=z,
            locationmode="ISO-3",
            colorscale="Reds",
            colorbar=dict(title="Price index"),
            hovertemplate="%{location}<br>Index: %{z:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(t=20, b=0, l=0, r=0),
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        height=420,
        template="plotly_white",
    )
    return fig


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Global Command Center", className="mb-0"),
                    html.Div(
                        [
                            html.Span("Last updated: ", className="text-muted small"),
                            html.Span(id="global-last-updated", className="small fw-semibold"),
                        ],
                        className="mt-1",
                    ),
                ],
                className="header-bar mb-3",
            ),
            dcc.Store(id="global-prices-store", data=None),
            dcc.Store(id="global-news-store", data=None),
            dcc.Interval(id="global-interval", interval=5 * 60 * 1000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("WTI Crude", className="text-muted small"),
                                html.Div(id="global-kpi-wti", className="h4 mb-0"),
                                html.Div(id="global-kpi-wti-sub", className="text-muted small"),
                            ],
                            className="panel-card p-3 h-100",
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Brent Crude", className="text-muted small"),
                                html.Div(id="global-kpi-brent", className="h4 mb-0"),
                                html.Div(id="global-kpi-brent-sub", className="text-muted small"),
                            ],
                            className="panel-card p-3 h-100",
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Soybean Oil", className="text-muted small"),
                                html.Div(id="global-kpi-soy", className="h4 mb-0"),
                                html.Div(id="global-kpi-soy-sub", className="text-muted small"),
                            ],
                            className="panel-card p-3 h-100",
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("News items", className="text-muted small"),
                                html.Div(id="global-kpi-news", className="h4 mb-0"),
                            ],
                            className="panel-card p-3 h-100",
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dbc.Button("Refresh now", id="global-btn-refresh", color="primary", size="sm", className="mt-3"),
                        md=2,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Global price map", className="text-muted mb-2"),
                                dcc.Graph(id="global-map", config={"displayModeBar": False}),
                            ],
                            className="panel-card p-4",
                        ),
                        md=7,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("News feed", className="text-muted mb-2 d-flex justify-content-between"),
                                html.Div(id="global-news-ticker", className="overflow-auto", style={"maxHeight": "400px"}),
                            ],
                            className="panel-card p-4",
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
        Output("global-prices-store", "data"),
        Output("global-news-store", "data"),
        Output("global-last-updated", "children"),
        Input("global-interval", "n_intervals"),
        Input("global-btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_global_data(n_intervals, n_clicks):
        try:
            prices = get_latest_prices(DEFAULT_TICKERS, use_cache=(n_clicks is None or n_clicks == 0))
            news = get_news_items(max_items=25)
        except Exception:
            prices = {}
            news = []
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        return (
            {k: {"price": v.get("price"), "change_pct": v.get("change_pct")} for k, v in prices.items()},
            news,
            ts,
        )

    @app.callback(
        Output("global-kpi-wti", "children"),
        Output("global-kpi-wti-sub", "children"),
        Output("global-kpi-brent", "children"),
        Output("global-kpi-brent-sub", "children"),
        Output("global-kpi-soy", "children"),
        Output("global-kpi-soy-sub", "children"),
        Output("global-kpi-news", "children"),
        Input("global-prices-store", "data"),
        Input("global-news-store", "data"),
        prevent_initial_call=False,
    )
    def update_kpis(prices, news):
        def fmt(name):
            if not prices or name not in prices:
                return ("–", "")
            p = prices[name]
            price = p.get("price")
            chg = p.get("change_pct")
            if price is None:
                return ("–", "")
            val = f"${float(price):.2f}"
            sub = ""
            if chg is not None:
                arrow = "▲" if chg >= 0 else "▼"
                sub = html.Span(f"{arrow} {float(chg):+.2f}%", className="text-success" if chg >= 0 else "text-danger")
            return (val, sub)
        wti_v, wti_s = fmt("WTI Crude Oil")
        br_v, br_s = fmt("Brent Crude Oil")
        soy_v, soy_s = fmt("Soybean Oil")
        news_count = len(news) if news else 0
        return wti_v, wti_s, br_v, br_s, soy_v, soy_s, str(news_count)

    @app.callback(
        Output("global-map", "figure"),
        Input("global-prices-store", "data"),
        prevent_initial_call=False,
    )
    def update_map(prices):
        return _build_map_figure(prices or {})

    @app.callback(
        Output("global-news-ticker", "children"),
        Input("global-news-store", "data"),
        prevent_initial_call=False,
    )
    def update_news_ticker(news):
        if not news:
            return html.Div("No news items loaded.", className="text-muted small")
        return html.Ul(
            [
                html.Li(
                    [
                        html.A(item.get("title", "—"), href=item.get("link", "#"), target="_blank", rel="noopener", className="text-decoration-none"),
                        html.Div([item.get("source", ""), " · ", item.get("published", "")], className="small text-muted mt-1"),
                    ],
                    className="mb-3 border-bottom pb-2",
                )
                for item in news[:20]
            ],
            className="list-unstyled mb-0",
        )

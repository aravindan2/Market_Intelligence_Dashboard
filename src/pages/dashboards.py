from dash import html, Input, Output, dcc
import dash_bootstrap_components as dbc

_DASHBOARDS = [
    {
        "title": "Global Command Center",
        "href": "/dashboards/global",
        "description": "World view: KPIs, global price map, and live news ticker.",
        "icon": "bi-globe2",
    },
    {
        "title": "Live Prices & News",
        "href": "/dashboards/live",
        "description": "Scraped prices, candlesticks, heatmaps, and RSS news panel.",
        "icon": "bi-graph-up-arrow",
    },
    {
        "title": "Live Commodity Price Dashboard",
        "href": "/dashboards/int",
        "description": "Classic commodity KPIs, regional snapshot, and analytics.",
        "icon": "bi-bar-chart-line",
    },
    {
        "title": "India Supply Chain",
        "href": "/dashboards/india",
        "description": "India map, extraction → refining → distribution flow.",
        "icon": "bi-diagram-3",
    },
    {
        "title": "Markets Deep Dive",
        "href": "/dashboards/deep",
        "description": "Correlation matrix, volatility, and multi-timeframe analytics.",
        "icon": "bi-speedometer2",
    },
]


def _make_card(d):
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        html.I(className=f"bi {d['icon']} me-2"),
                        className="text-primary mb-2",
                    ),
                    html.H5(d["title"], className="card-title"),
                    html.P(d["description"], className="card-text text-muted small"),
                    dbc.NavLink(
                        "Open →",
                        href=d["href"],
                        className="stretched-link p-0 mt-2 fw-semibold",
                    ),
                ]
            )
        ],
        className="panel-card h-100",
        style={"minHeight": "160px"},
    )


def layout():
    return html.Div(
        [
            html.H2("Dashboards", className="mb-2 px-4 pt-2"),
            html.P(
                "Market intelligence: global view, live prices, news, India supply chain, and analytics.",
                className="text-muted px-4 mb-4",
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    id="dashboards-search",
                                    type="search",
                                    placeholder="Search dashboards…",
                                    className="mb-3",
                                ),
                                md=6,
                            ),
                        ],
                        className="g-2 mb-3",
                    ),
                    dbc.Row(id="dashboards-cards", className="g-4"),
                ],
                fluid=True,
                className="px-4 pb-4",
            ),
        ],
        className="p-0",
    )


def register_callbacks(app):
    @app.callback(
        Output("dashboards-cards", "children"),
        Input("dashboards-search", "value"),
        prevent_initial_call=False,
    )
    def filter_dashboards(q):
        q = (q or "").strip().lower()
        items = [
            d
            for d in _DASHBOARDS
            if q in d["title"].lower() or q in (d.get("description") or "").lower()
        ]
        return [dbc.Col(_make_card(d), md=6, lg=4) for d in items]

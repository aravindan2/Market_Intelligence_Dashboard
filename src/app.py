from dash import Dash, html, dcc, Input, Output, no_update
import dash_bootstrap_components as dbc

from ui.chrome import build_header, build_sidebar, build_breadcrumb
from pages import dashboards, alerts, int, global_dashboard, live_news, india_supply_chain, markets_deep

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="NIX Demo",
)

header = build_header(asset_url=app.get_asset_url)
sidebar = build_sidebar()
breadcrumb = build_breadcrumb()

content = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        breadcrumb,
        html.Div(id="content-body"),
    ],
    id="content",
    className="content-area",
)

app.layout = html.Div([header, sidebar, content])

DEFAULT_PATH = "/dashboards"

@app.callback(Output("url", "pathname"), Input("url", "pathname"))
def redirect_home(pathname):
    if pathname in (None, "/"):
        return DEFAULT_PATH
    return no_update

@app.callback(
    Output("content-body", "children"),
    Output("breadcrumb", "items"),
    Input("url", "pathname"),
)
def render_page(pathname):
    # Alerts detail
    if pathname and pathname.startswith("/alerts/"):
        alert_id = pathname.split("/")[2]
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Alerts", "href": "/alerts"},
            {"label": f"#{alert_id}", "active": True},
        ]
        return alerts.layout_detail(alert_id), crumbs

    # Alerts overview
    if pathname and pathname.startswith("/alerts"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Alerts", "active": True},
        ]
        return alerts.layout_overview(), crumbs
    
    # Live Commodity Price Dashboard
    if pathname and pathname.startswith("/dashboards/int"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Dashboards", "href": "/dashboards"},
            {"label": "Live Commodity Price Dashboard", "active": True},
        ]
        return int.layout(), crumbs

    # Global Command Center
    if pathname and pathname.startswith("/dashboards/global"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Dashboards", "href": "/dashboards"},
            {"label": "Global Command Center", "active": True},
        ]
        return global_dashboard.layout(), crumbs

    # Live Prices & News
    if pathname and pathname.startswith("/dashboards/live"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Dashboards", "href": "/dashboards"},
            {"label": "Live Prices & News", "active": True},
        ]
        return live_news.layout(), crumbs

    # India Supply Chain
    if pathname and pathname.startswith("/dashboards/india"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Dashboards", "href": "/dashboards"},
            {"label": "India Supply Chain", "active": True},
        ]
        return india_supply_chain.layout(), crumbs

    # Markets Deep Dive
    if pathname and pathname.startswith("/dashboards/deep"):
        crumbs = [
            {"label": "Workspaces", "href": "#"},
            {"label": "#1"},
            {"label": "Dashboards", "href": "/dashboards"},
            {"label": "Markets Deep Dive", "active": True},
        ]
        return markets_deep.layout(), crumbs

    # Dashboards list (default)
    crumbs = [
        {"label": "Workspaces", "href": "#"},
        {"label": "#1"},
        {"label": "Dashboards", "active": True},
    ]
    return dashboards.layout(), crumbs

# page-specific callbacks
dashboards.register_callbacks(app)
alerts.register_callbacks(app)
int.register_callbacks(app)
global_dashboard.register_callbacks(app)
live_news.register_callbacks(app)
india_supply_chain.register_callbacks(app)
markets_deep.register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True,port="8052")
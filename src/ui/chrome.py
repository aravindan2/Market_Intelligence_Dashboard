from dash import html
import dash_bootstrap_components as dbc

def nav_item(href, label, icon):
    return dbc.NavLink(
        [html.I(className=f"bi {icon}"), html.Span(label, className="link-text")],
        href=href,
        active="partial",       # keep active on subpaths like /alerts/1
        className="sidebar-link",
    )

def nav_section(title, items):
    return html.Div(
        [html.Div(title, className="section-title"),
         dbc.Nav(items, vertical=True, className="sidebar-nav")],
        className="sidebar-section",
    )

def build_header(asset_url):
    return dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Img(src=asset_url("nix-full-icon.svg"),
                                 className="brand-logo", alt="Neuralix logo"),
                        html.Div(
                            [html.Span("Powered by", className="brand-powered-text"),
                             html.Img(src=asset_url("nix-icon.svg"),
                                      className="brand-powered-icon", alt="NIX icon")],
                            className="brand-powered-row",
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    [
                        html.Button(html.I(className="bi bi-plus-lg"),
                                    className="icon-btn plus-btn", id="add-btn"),
                        html.Button(html.I(className="bi bi-moon"),
                                    className="icon-btn", id="theme-btn"),
                        html.Div(html.I(className="bi bi-person-fill"), className="avatar"),
                    ],
                    className="header-actions",
                ),
            ],
            fluid=True, className="px-3",
        ),
        color="white", dark=False, fixed="top", className="app-header",
    )

def build_sidebar():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(className="workspace-icon"),
                    html.Div([html.Div("Oil Market Intelligence Demo", className="workspace-title"),
                              html.Div("Manufacturing", className="workspace-subtitle")],
                             className="workspace-text"),
                ],
                className="workspace-card",
            ),
            nav_section("Monitoring", [
                nav_item("/dashboards", "Dashboards", "bi-graph-up"),
                nav_item("/dashboards/global", "Global Command Center", "bi-globe2"),
                nav_item("/dashboards/live", "Live Prices & News", "bi-graph-up-arrow"),
                nav_item("/dashboards/int", "Commodity Dashboard", "bi-bar-chart-line"),
                nav_item("/dashboards/india", "India Supply Chain", "bi-diagram-3"),
                nav_item("/dashboards/deep", "Markets Deep Dive", "bi-speedometer2"),
                nav_item("/alerts", "Alerts", "bi-bell"),
                nav_item("/notification-groups", "Notification Groups", "bi-ui-checks-grid"),
                nav_item("/metrics", "Metrics", "bi-speedometer2"),
            ]),
            nav_section("Data Ingestion", [
                nav_item("/connections", "Connections", "bi-plug"),
                nav_item("/datasources", "Datasources", "bi-database"),
                nav_item("/data-stores", "Data Stores", "bi-collection"),
            ]),
            nav_section("Training, Deployment & Inference", [
                nav_item("/model-defs", "Model Definitions", "bi-cpu"),
                nav_item("/feature-stores", "Feature Stores", "bi-grid"),
                nav_item("/experiments", "Experiments", "bi-flask"),
                nav_item("/deployments", "Model Deployments", "bi-hdd-network"),
                nav_item("/inferences", "Inferences", "bi-activity"),
                nav_item("/inference-store", "Inference Store", "bi-archive"),
            ]),
            nav_section("Administration", [nav_item("/admin", "Admin", "bi-gear")]),
        ],
        id="sidebar", className="sidebar",
    )

def build_breadcrumb():
    return dbc.Breadcrumb(id="breadcrumb", items=[], className="px-4 pt-4")

"""
India Supply Chain dashboard: map, flow, table.
"""
from __future__ import annotations

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data.india_supply_chain import get_india_supply_chain_data

# State name (ST_NM) -> value for choropleth (sample; match GeoJSON properties.ST_NM)
# GeoJSON: https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/...
INDIA_STATE_VALUES = {
    "Andaman and Nicobar Island": 50, "Andhra Pradesh": 300, "Arunachal Pradesh": 20,
    "Assam": 120, "Bihar": 80, "Chandigarh": 10, "Chhattisgarh": 90,
    "Dadra and Nagar Haveli": 5, "Daman and Diu": 5, "Delhi": 40,
    "Goa": 15, "Gujarat": 450, "Haryana": 100, "Himachal Pradesh": 25,
    "Jammu and Kashmir": 30, "Jharkhand": 85, "Karnataka": 180,
    "Kerala": 120, "Ladakh": 5, "Lakshadweep": 2, "Madhya Pradesh": 150,
    "Maharashtra": 400, "Manipur": 15, "Meghalaya": 20, "Mizoram": 10,
    "Nagaland": 15, "Odisha": 100, "Puducherry": 8, "Punjab": 95,
    "Rajasthan": 180, "Sikkim": 5, "Tamil Nadu": 250, "Telangana": 130,
    "Tripura": 15, "Uttar Pradesh": 200, "Uttarakhand": 35, "West Bengal": 150,
}
GEOJSON_URL = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"


def layout():
    return html.Div(
        [
            html.H2("India Supply Chain", className="mb-2"),
            html.P("Production, refining, and distribution across regions.", className="text-muted mb-3"),
            dcc.Store(id="india-data-store", data=None),
            dcc.Interval(id="india-interval", interval=10 * 60 * 1000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div("Regional map (production index)", className="text-muted mb-2"),
                                dcc.Graph(id="india-map", config={"displayModeBar": False}),
                            ],
                            className="panel-card p-4",
                        ),
                        md=7,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    html.Div("Supply chain", className="text-muted mb-2"),
                                    dcc.Graph(id="india-sankey", config={"displayModeBar": False}),
                                ],
                                className="panel-card p-4 mb-3",
                            ),
                            dbc.Card(
                                [
                                    html.Div("Summary", className="text-muted mb-2"),
                                    html.Div(id="india-summary"),
                                ],
                                className="panel-card p-4",
                            ),
                        ],
                        md=5,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div("Regional data", className="text-muted mb-2"),
                            dbc.Table(id="india-regional-table", bordered=False, hover=True, className="mb-0"),
                        ],
                        className="panel-card p-4",
                    ),
                ),
            ),
        ],
        className="p-4",
    )


def register_callbacks(app):
    @app.callback(
        Output("india-data-store", "data"),
        Input("india-interval", "n_intervals"),
        prevent_initial_call=False,
    )
    def load_india_data(n):
        return get_india_supply_chain_data()

    @app.callback(
        Output("india-map", "figure"),
        Input("india-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_india_map(data):
        if not data:
            return go.Figure()
        df = pd.DataFrame([
            {"state": k, "value": v} for k, v in INDIA_STATE_VALUES.items()
        ])
        fig = px.choropleth(
            df,
            geojson=GEOJSON_URL,
            featureidkey="properties.ST_NM",
            locations="state",
            color="value",
            color_continuous_scale="Blues",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=420)
        return fig

    @app.callback(
        Output("india-sankey", "figure"),
        Input("india-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_sankey(data):
        if not data or "stages" not in data:
            return go.Figure()
        stages = data["stages"]
        n = len(stages)
        if n < 2:
            return go.Figure()
        labels = [s["label"] for s in stages]
        # Sankey: source -> target (0->1, 1->2, 2->3)
        source = list(range(n - 1))
        target = list(range(1, n))
        value = [stages[i]["volume_kt"] for i in range(n - 1)]
        fig = go.Figure(data=[go.Sankey(node=dict(label=labels), link=dict(source=source, target=target, value=value))])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=280)
        return fig

    @app.callback(
        Output("india-summary", "children"),
        Output("india-regional-table", "children"),
        Input("india-data-store", "data"),
        prevent_initial_call=False,
    )
    def update_summary_and_table(data):
        if not data:
            return "", []
        summary = data.get("summary", {})
        summary_html = html.Div([
            html.P([html.Strong("Monthly crude processed: "), f"{summary.get('monthly_crude_processed_kt', '–')} kT"]),
            html.P([html.Strong("Indigenous production: "), f"{summary.get('indigenous_production_kt', '–')} kT"]),
            html.P(html.Small(summary.get("last_updated", ""), className="text-muted")),
        ])
        regional = data.get("regional", [])
        if not regional:
            return summary_html, [html.Thead(html.Tr([html.Th("Region"), html.Th("Production (kT)"), html.Th("Refining (kT)")])), html.Tbody([])]
        thead = html.Thead(html.Tr([html.Th("Region"), html.Th("Production (kT)"), html.Th("Refining capacity (kT)")]))
        tbody = html.Tbody([
            html.Tr([html.Td(r["region"]), html.Td(r.get("production_kt", "–")), html.Td(r.get("refining_capacity_kt", "–"))])
            for r in regional
        ])
        return summary_html, [thead, tbody]

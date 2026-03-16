from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from dash.dependencies import ALL, MATCH
from dash.exceptions import PreventUpdate
from datetime import date

# =========================
# In-process Alerts (card 1)
# =========================
_INPROC_ALERTS = [
    {"site":"Anara","date":"2025-07-31","batch":"2502","severity":"Medium","process":"Batching","details":"Deviation in Cement is 2.5% more","action":"Destroy mix & restart process","status":"Acknowledged"},
    {"site":"Anara","date":"2025-07-30","batch":"183","severity":"High","process":"Batching","details":"Deviation in Water is 5% more","action":"Destroy mix & restart process","status":"Not Resolved"},
    {"site":"Anara","date":"2025-07-29","batch":"200","severity":"Low","process":"Tensioning","details":"Elongation length 6% more","action":"Return wires & restart process","status":"Not Resolved"},
    {"site":"Anara","date":"2025-07-28","batch":"587","severity":"Medium","process":"Vibration","details":"Vibration in vibrator 8 is 7% more","action":"Check callibration- Vibrator 8","status":"Resolved"},
    {"site":"Anara","date":"2025-07-27","batch":"201","severity":"Low","process":"Steam Curing","details":"Steam curing stopped at 12.5 hours","action":"Ambient Temperature 1 hour process pending","status":"Resolved"},
    {"site":"Anara","date":"2025-07-26","batch":"2472","severity":"Medium","process":"Steam Cube","details":"Strength = 38 N","action":"1 additional hour of Steam Curing","status":"Acknowledged"},
    {"site":"Anara","date":"2025-07-25","batch":"80","severity":"Low","process":"Green SBT","details":"Strength = 35 N","action":"1 new sleeper for testing","status":"Not Resolved"},
    {"site":"Anara","date":"2025-07-24","batch":"150","severity":"High","process":"Normal SBT","details":"CT = 380","action":"1 new sleeper for testing","status":"Resolved"},
    {"site":"UDV","date":"2025-07-23","batch":"80","severity":"Low","process":"Green SBT","details":"Strength = 35 N","action":"1 new sleeper for testing","status":"Not Resolved"},
    {"site":"TMQ","date":"2025-07-22","batch":"150","severity":"High","process":"Normal SBT","details":"CT = 380","action":"1 new sleeper for testing","status":"Resolved"},
]
_INPROC_GROUPS = sorted({a["site"] for a in _INPROC_ALERTS})
_INPROC_GROUPS_DEFAULT = _INPROC_GROUPS[:]
_INPROC_SEVERITIES = ["Low", "Medium", "High"]
_INPROC_STATUSES = ["Resolved", "Acknowledged", "Not Resolved"]

# Column schema for card 1
_INPROC_COLS = [
    ("site", "Site"),
    ("date", "Date"),
    ("batch", "Batch Number"),
    ("severity", "Severity"),
    ("process", "Process"),
    ("details", "Details"),
    ("action", "Action"),
    ("status", "Status"),
]

# ===========================
# Manufacturing Alerts (card 2)
# ===========================
_MFG_ALERTS = [
    {"site":"Anara","date":"2025-07-31","stage":"Pre-Production","category":"Material Certificate","trigger":"Steel “relaxation test” certificate > 6 months old","severity":"Medium","action":"Re-test material or quarantine stock"},
    {"site":"UDV","date":"2025-07-30","stage":"Pre-Production","category":"Material Certificate","trigger":"Cement stock > 3 months old","severity":"Medium","action":"Perform fresh physical-property test"},
    {"site":"TMQ","date":"2025-07-29","stage":"Pre-Production","category":"Material Certificate","trigger":"Admixture shelf life ≤ 14 days","severity":"High","action":"Replace or re-certify admixture"},
    {"site":"Anara","date":"2025-07-28","stage":"Pre-Production","category":"Mix Design Approval","trigger":"New/revised mix design not signed off by RDSO","severity":"High","action":"Halt production until approval"},
    {"site":"UDV","date":"2025-07-27","stage":"Pre-Production","category":"Aggregate Quality","trigger":"Granulometric curve drift outside approved envelope","severity":"Medium","action":"Review aggregate source & retest"},
    {"site":"TMQ","date":"2025-07-26","stage":"Pre-Production","category":"Equipment Calibration","trigger":"Batcher or weights calibration overdue","severity":"Low","action":"Schedule calibration"},
    # {"site":"Anara","date":"2025-07-25","stage":"In-Process","category":"Tensioning","trigger":"Jack load-cutoff not reached within ±2% of target force","severity":"High","action":"Inspect jack & prestress controls"},
    # {"site":"UDV","date":"2025-07-24","stage":"In-Process","category":"Prestress Hold","trigger":"> 2 h between wire stressing and concrete placement","severity":"Medium","action":"Re-validate prestress integrity"},
    # {"site":"TMQ","date":"2025-07-23","stage":"In-Process","category":"Mix Water-Cement Ratio","trigger":"Real-time batch W/C < 0.35 or > 0.45","severity":"High","action":"Adjust water dosing immediately"},
    # {"site":"Anara","date":"2025-07-22","stage":"In-Process","category":"Vibrator RPM","trigger":"Consolidation vibrator speed < 9 000 rpm – 4%","severity":"Medium","action":"Check vibrator motor & bearings"},
    # {"site":"UDV","date":"2025-07-21","stage":"In-Process","category":"Slump/Compaction","trigger":"Slump > 25 mm or compacting factor < 0.75","severity":"Medium","action":"Review mix consistency & admixture"},
    # {"site":"TMQ","date":"2025-07-20","stage":"In-Process","category":"Steam-Curing Temperature","trigger":"Chamber temp ramp > 15 °C/hr or soak outside 55–60 °C or cooldown > 15 °C/hr","severity":"High","action":"Adjust chamber controls"},
    # {"site":"Anara","date":"2025-07-19","stage":"In-Process","category":"Premature Detensioning","trigger":"Detensioning before cube strength ≥ 40 N/mm² at test age","severity":"High","action":"Delay detensioning"},
    # {"site":"UDV","date":"2025-07-18","stage":"Quality Control","category":"Cube-Test Failure Rate","trigger":"> 2.5% water-cured cubes below fck at 15 days","severity":"High","action":"Investigate batching & curing"},
    # {"site":"TMQ","date":"2025-07-17","stage":"Quality Control","category":"Cube-Test Variability","trigger":"Coefficient of variation of cube strengths ≥ 7%","severity":"Medium","action":"Tighten process controls"},
    # {"site":"Anara","date":"2025-07-16","stage":"Quality Control","category":"Dimensional Rejection Rate","trigger":"> 0% rejects pre-stabilization or > 2% post-stabilization","severity":"Medium","action":"Calibrate moulds & guides"},
    # {"site":"UDV","date":"2025-07-15","stage":"Quality Control","category":"Static Bend Test Failure","trigger":"MR or MF below drawing spec on sampled sleeper","severity":"High","action":"Hold lot for review"},
    # {"site":"TMQ","date":"2025-07-14","stage":"Quality Control","category":"Electrical Resistance (FTC)","trigger":"Resistance > 200 Ω (lamp comparator)","severity":"Medium","action":"Route sleeper to quarantine station"},
]
_MFG_GROUPS = sorted({a["site"] for a in _MFG_ALERTS})
_MFG_GROUPS_DEFAULT = _MFG_GROUPS[:]
_MFG_STAGES = sorted({a["stage"] for a in _MFG_ALERTS})
_MFG_CATEGORIES = sorted({a["category"] for a in _MFG_ALERTS})
_MFG_SEVERITIES = ["Low", "Medium", "High"]

# Column schema for card 2
_MFG_COLS = [
    ("site", "Site"),
    ("date", "Date"),
    ("stage", "Stage"),
    ("category", "Category"),
    ("trigger", "Trigger Condition"),
    ("severity", "Severity"),
    ("action", "Recommended Action"),
]

# -----------------
# Global date range (controls both cards)
# -----------------
_all_dates = [a["date"] for a in _INPROC_ALERTS] + [a["date"] for a in _MFG_ALERTS]
_DATE_MIN = date.fromisoformat(min(_all_dates))
_DATE_MAX = date.fromisoformat(max(_all_dates))

# -----------------
# Helpers / badges
# -----------------
_SEV_COLOR = {"Low": "success", "Medium": "warning", "High": "danger"}
_STATUS_COLOR = {"Resolved": "success", "Acknowledged": "warning", "Not Resolved": "danger"}

def _sev_badge(level: str):
    return dbc.Badge(level, color=_SEV_COLOR.get(level, "secondary"), pill=True, className="badge-soft")

def _status_badge(level: str):
    return dbc.Badge(level, color=_STATUS_COLOR.get(level, "secondary"), pill=True, className="badge-soft")

def _row_inproc(a: dict):
    return html.Tr([
        html.Td(a["site"]),
        html.Td(a["date"]),
        html.Td(a["batch"]),
        html.Td(_sev_badge(a["severity"])),
        html.Td(a["process"]),
        html.Td(a["details"]),
        html.Td(a["action"]),
        html.Td(_status_badge(a["status"])),
    ])

def _row_mfg(a: dict):
    return html.Tr([
        html.Td(a["site"]),
        html.Td(a["date"]),
        html.Td(a["stage"]),
        html.Td(a["category"]),
        html.Td(a["trigger"]),
        html.Td(_sev_badge(a["severity"])),
        html.Td(a["action"]),
    ])

def _uniq(rows, key):
    return sorted({r[key] for r in rows})

def _header_cell(table: str, key: str, label: str, options: list[str]):
    """
    Build a <th> with a small filter button that opens a popover.
    The popover contains a multi-select checklist + Select all / Clear actions.
    """
    btn_id = {"type": "col-filter-btn", "table": table, "col": key}
    pop_id = {"type": "col-filter-pop", "table": table, "col": key}
    chk_id = {"type": "col-filter-values", "table": table, "col": key}
    all_id = {"type": "col-filter-all", "table": table, "col": key}
    none_id = {"type": "col-filter-none", "table": table, "col": key}
    opts = [{"label": o, "value": o} for o in options]
    default_vals = [o["value"] for o in opts]

    return html.Th(
        [
            html.Div(
                [
                    html.Span(label),
                    dbc.Button(
                        html.I(className="bi bi-funnel"),
                        id=btn_id,
                        size="sm",
                        color="light",
                        className="ms-2 filter-btn",
                        n_clicks=0,
                    ),
                ],
                className="d-flex align-items-center justify-content-between gap-2",
            ),
            dbc.Popover(
                [
                    dbc.PopoverHeader(f"Filter {label}"),
                    dbc.PopoverBody(
                        [
                            dcc.Checklist(
                                id=chk_id,
                                options=opts,
                                value=default_vals,
                                inputStyle={"marginRight": "8px"},
                                style={"maxHeight": "240px", "overflow": "auto"},
                            ),
                            html.Div(
                                [
                                    dbc.Button("Select all", id=all_id, size="sm", color="secondary", outline=True),
                                    dbc.Button("Clear", id=none_id, size="sm", color="secondary", outline=True, className="ms-2"),
                                ],
                                className="mt-2",
                            ),
                        ]
                    ),
                ],
                id=pop_id,
                target=btn_id,           # attaches to the funnel button
                placement="bottom-end",
                is_open=False,
            ),
        ]
    )

# =========
# Layouts
# =========
def layout_overview():
    # --- Card 0: header line with title (left) + date picker (right)
    header_bar = html.Div(
        [
            html.H2("Alerts", className="mb-0"),
            html.Div(
                [
                    html.Div("Date range", className="small text-muted text-end mb-1"),
                    dcc.DatePickerRange(
                        id="alerts-date-range",
                        min_date_allowed=_DATE_MIN,
                        max_date_allowed=_DATE_MAX,
                        start_date=_DATE_MIN,
                        end_date=_DATE_MAX,
                        display_format="YYYY-MM-DD",
                        with_portal=False,
                        clearable=False,
                    ),
                ],
                className="d-flex flex-column align-items-end",
                style={"minWidth": "280px"},
            ),
        ],
        className="header-bar mb-2",
    )
    card_0 = dbc.Card([header_bar], className="panel-card p-4 mb-4")

    # --- Card 1 controls (top row)
    header_row_1 = dbc.Row(
        [
            dbc.Col(
                dbc.Input(
                    id="alerts-search",
                    type="search",
                    placeholder="Search alerts by name",
                    className="mb-3 search-input",
                ),
                md=6,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div("Sites", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="alerts-group-filter",
                            options=[{"label": g, "value": g} for g in _INPROC_GROUPS],
                            value=_INPROC_GROUPS_DEFAULT,
                            multi=True,
                            clearable=False,
                            placeholder="Select Sites",
                            className="dd-compact",
                        ),
                    ],
                    className="d-flex justify-content-end align-items-end gap-2 mb-3",
                ),
                md=6,
            ),
        ],
        className="g-2",
    )

    # --- Card 1 table header with filter menus
    inproc_head = [
        _header_cell(
            "inproc", k, lbl,
            _INPROC_SEVERITIES if k == "severity" else
            _INPROC_STATUSES if k == "status" else
            _uniq(_INPROC_ALERTS, k)
        )
        for k, lbl in _INPROC_COLS
    ]

    table_1 = dbc.Table(
        [
            html.Thead(html.Tr(inproc_head)),
            html.Tbody(id="alerts-rows"),
        ],
        bordered=False, hover=True, responsive=True, className="bg-white table-modern",
    )

    card_1 = dbc.Card(
        [
            html.H2("In-process Alerts", className="mb-2"),
            header_row_1,
            table_1,
        ],
        className="panel-card p-4 mb-4",
    )

    # --- Card 2 controls (top row)
    header_row_2 = dbc.Row(
        [
            dbc.Col(
                dbc.Input(
                    id="mfg-search",
                    type="search",
                    placeholder="Search alerts by name",
                    className="mb-3 search-input",
                ),
                md=6,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div("Sites", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="mfg-group-filter",
                            options=[{"label": g, "value": g} for g in _MFG_GROUPS],
                            value=_MFG_GROUPS_DEFAULT,
                            multi=True,
                            clearable=False,
                            placeholder="Select Sites",
                            className="dd-compact",
                        ),
                    ],
                    className="d-flex justify-content-end align-items-end gap-2 mb-3",
                ),
                md=6,
            ),
        ],
        className="g-2",
    )

    # --- Card 2 table header with filter menus
    mfg_head = [
        _header_cell(
            "mfg", k, lbl,
            _MFG_SEVERITIES if k == "severity" else
            _uniq(_MFG_ALERTS, k)
        )
        for k, lbl in _MFG_COLS
    ]

    table_2 = dbc.Table(
        [
            html.Thead(html.Tr(mfg_head)),
            html.Tbody(id="mfg-rows"),
        ],
        bordered=False, hover=True, responsive=True, className="bg-white table-modern",
    )

    card_2 = dbc.Card(
        [
            html.H2("Manufacturing Alerts", className="mb-2"),
            header_row_2,
            table_2,
        ],
        className="panel-card p-4 mb-4",
    )

    return html.Div([card_0, card_1, card_2], className="p-4")

# =========
# Callbacks
# =========
def register_callbacks(app):
    # --- Open/close any column filter popover (both tables)
    @app.callback(
        Output({"type": "col-filter-pop", "table": MATCH, "col": MATCH}, "is_open"),
        Input({"type": "col-filter-btn", "table": MATCH, "col": MATCH}, "n_clicks"),
        State({"type": "col-filter-pop", "table": MATCH, "col": MATCH}, "is_open"),
        prevent_initial_call=True,
    )
    def _toggle_pop(n, is_open):
        if n:
            return not is_open
        return is_open

    # --- Handle Select all / Clear inside any popover (both tables)
    @app.callback(
        Output({"type": "col-filter-values", "table": MATCH, "col": MATCH}, "value"),
        Input({"type": "col-filter-all", "table": MATCH, "col": MATCH}, "n_clicks"),
        Input({"type": "col-filter-none", "table": MATCH, "col": MATCH}, "n_clicks"),
        State({"type": "col-filter-values", "table": MATCH, "col": MATCH}, "options"),
        prevent_initial_call=True,
    )
    def _select_all_none(n_all, n_none, options):
        if not (n_all or n_none):
            raise PreventUpdate
        all_vals = [o["value"] for o in (options or [])]
        # Choose latest by count; good enough without ctx
        if (n_all or 0) >= (n_none or 0):
            return all_vals
        return []

    # --- Card 1 rows
    @app.callback(
        Output("alerts-rows", "children"),
        # top-row
        Input("alerts-search", "value"),
        Input("alerts-group-filter", "value"),
        Input("alerts-date-range", "start_date"),
        Input("alerts-date-range", "end_date"),
        # per-column selections (values + ids so we know which column they belong to)
        Input({"type": "col-filter-values", "table": "inproc", "col": ALL}, "value"),
        State({"type": "col-filter-values", "table": "inproc", "col": ALL}, "id"),
        prevent_initial_call=False,
    )
    def filter_inproc(q, selected_groups, start_date, end_date, col_values, col_ids):
        q = (q or "").strip().lower()
        sd = start_date or _DATE_MIN.isoformat()
        ed = end_date or _DATE_MAX.isoformat()
        selected_top = set(selected_groups or _INPROC_GROUPS_DEFAULT)

        # Build a dict like {'site': {...}, 'date': {...}, ...}
        by_col = {}
        for vals, cid in zip(col_values or [], col_ids or []):
            col = cid.get("col")
            by_col[col] = set(vals) if vals else set()

        def ok(a):
            # intersect site with header filter
            if a["site"] not in selected_top:
                return False
            if not (sd <= a["date"] <= ed):
                return False
            # per-column exact match filters (if any are deselected)
            for key, _label in _INPROC_COLS:
                sel = by_col.get(key)
                if sel is not None and len(sel) > 0 and a[key] not in sel:
                    return False
            if q:
                blob = " ".join([a["site"], a["date"], a["batch"], a["severity"],
                                 a["process"], a["details"], a["action"], a["status"]]).lower()
                if q not in blob:
                    return False
            return True

        rows = [a for a in _INPROC_ALERTS if ok(a)]
        return [_row_inproc(a) for a in rows]

    # --- Card 2 rows
    @app.callback(
        Output("mfg-rows", "children"),
        # top-row
        Input("mfg-search", "value"),
        Input("mfg-group-filter", "value"),
        Input("alerts-date-range", "start_date"),
        Input("alerts-date-range", "end_date"),
        # per-column selections
        Input({"type": "col-filter-values", "table": "mfg", "col": ALL}, "value"),
        State({"type": "col-filter-values", "table": "mfg", "col": ALL}, "id"),
        prevent_initial_call=False,
    )
    def filter_mfg(q, selected_groups, start_date, end_date, col_values, col_ids):
        q = (q or "").strip().lower()
        sd = start_date or _DATE_MIN.isoformat()
        ed = end_date or _DATE_MAX.isoformat()
        selected_top = set(selected_groups or _MFG_GROUPS_DEFAULT)

        by_col = {}
        for vals, cid in zip(col_values or [], col_ids or []):
            col = cid.get("col")
            by_col[col] = set(vals) if vals else set()

        def ok(a):
            if a["site"] not in selected_top:
                return False
            if not (sd <= a["date"] <= ed):
                return False
            for key, _label in _MFG_COLS:
                sel = by_col.get(key)
                if sel is not None and len(sel) > 0 and a[key] not in sel:
                    return False
            if q:
                blob = " ".join([a["site"], a["date"], a["stage"], a["category"],
                                 a["trigger"], a["severity"], a["action"]]).lower()
                if q not in blob:
                    return False
            return True

        rows = [a for a in _MFG_ALERTS if ok(a)]
        return [_row_mfg(a) for a in rows]

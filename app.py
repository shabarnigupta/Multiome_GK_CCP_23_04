from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess

# --------- LOAD & PREP DATA ---------

# Read your Excel file in the same folder as this script
df_wide = pd.read_excel("Multiome_GK.xlsx")

# First column is the time column (your "Time (Days)" – with the odd space)
time_col = df_wide.columns[0]

# All other columns are mice
mouse_cols = [c for c in df_wide.columns if c != time_col]

# Convert to long format: Time, Mouse, Volume
df = df_wide.melt(
    id_vars=time_col,
    value_vars=mouse_cols,
    var_name="Mouse",
    value_name="Volume"
)

# Drop rows with no measurement
df = df.dropna(subset=["Volume"])

# Mice to show as dashed lines
DASHED_MICE = {"TP1-PT", "TP2-PT", "TP3-V", "TP5-V"}

# --------- DASH APP LAYOUT ---------

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Tumour growth kinetics_CCP_23_04"),

    html.Div([
        html.Div([
            html.Label("Select mouse/mice"),
            dcc.Dropdown(
                id="mouse-select",
                options=[{"label": m, "value": m} for m in sorted(df["Mouse"].unique())],
                value=sorted(df["Mouse"].unique()),
                multi=True
            ),
        ], style={"width": "48%", "display": "inline-block"}),

        html.Div([
            html.Label("Curve type"),
            dcc.RadioItems(
                options=[
                    {"label": "Raw (lines + markers)", "value": "raw"},
                    {"label": "LOWESS smoothed", "value": "smooth"},
                ],
                value="smooth",
                id="curve-type",
                labelStyle={"display": "block"}
            ),
        ], style={
            "width": "48%",
            "display": "inline-block",
            "verticalAlign": "top"
        }),
    ], style={"padding": "10px 5px"}),

    dcc.Graph(id="tumour-graph")
])


# --------- CALLBACK: UPDATE FIGURE ---------

@callback(
    Output("tumour-graph", "figure"),
    Input("mouse-select", "value"),
    Input("curve-type", "value")
)
def update_tumour_graph(selected_mice, curve_type):
    if not selected_mice:
        return go.Figure()

    # Ensure selected_mice is a list
    if isinstance(selected_mice, str):
        selected_mice = [selected_mice]

    fig = go.Figure()

    for mouse in selected_mice:
        dff = df[df["Mouse"] == mouse].sort_values(time_col)

        # choose dash style based on mouse name
        dash_style = "dash" if mouse in DASHED_MICE else "solid"

        if curve_type == "smooth" and len(dff) > 2:
            sm = lowess(dff["Volume"], dff[time_col], frac=0.35)
            fig.add_trace(go.Scatter(
                x=sm[:, 0],
                y=sm[:, 1],
                mode="lines",
                name=f"{mouse} (smoothed)",
                line=dict(dash=dash_style)
            ))
        else:
            fig.add_trace(go.Scatter(
                x=dff[time_col],
                y=dff["Volume"],
                mode="lines+markers",
                name=mouse,
                line=dict(dash=dash_style)
            ))

    # ---- Add shaded chemo windows on the x-axis ----
    # Chemo given from days 37–57 and 65–85
    chemo_windows = [(37, 57), (65, 85)]
    for start, end in chemo_windows:
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor="lightgrey",   # light grey shade
            opacity=0.5,             # 50% transparent
            layer="below",           # behind the tumour lines
            line_width=0             # no border
        )

    # Layout
    fig.update_layout(
    height=800,             # makes Y-axis visually longer
    xaxis_title="Days",
    yaxis_title="Tumour Volume (mm³)",
    hovermode="x unified",
    margin={"l": 50, "r": 10, "t": 40, "b": 40}
)


    return fig


if __name__ == "__main__":
    app.run(debug=True)

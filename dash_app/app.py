import dash
import pandas as pd
import numpy as np
import pathlib
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
import plotly.express as px
import plotly.graph_objects as go

from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash.exceptions import PreventUpdate
# from helpers import make_dash_table, create_plot

from os import path # path
import os
import subprocess  #to run executable
from datetime import date
import datetime    #to convert date to doy or vice versa
import calendar
import re

from navbar import Navbar

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.12.1/css/all.css",
    ],
  #  meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    prevent_initial_callbacks=True,  #to prevent "Callback failed: the server did not respond." message thttps://community.plotly.com/t/callback-error-when-the-app-is-started/46345/2
)

server = app.server

DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()

DSSAT_FILES_DIR_SHORT = "/dssat_files_dir/"  #for linux systemn

DSSAT_FILES_DIR = os.getcwd() + DSSAT_FILES_DIR_SHORT   #for linux systemn

#https://community.plotly.com/t/loading-when-opening-localhost/7284
#I suspect that this is related to the JS assets from the CDN not loading properly - perhaps because they are blocked by your firewall or some other reason.
#You can load the assets locally by setting:
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

#column names for scenario summary table:EJ(5/3/2021)
sce_col_names=[ "sce_name", "Crop", "Cultivar","stn_name", "Plt-date", "FirstYear", "LastYear", "soil","iH2O","iNO3","TargetYr",
                "Fert_1_DOY","Fert_1_Kg","Fert_2_DOY","Fert_2_Kg","Fert_3_DOY","Fert_3_Kg","Fert_4_DOY","Fert_4_Kg",
                "CropPrice", "NFertCost", "SeedCost","OtherVariableCosts","FixedCosts"
]

cultivar_options = {
    # "MZ": ["CIMT01 BH540-Kassie","CIMT02 MELKASA-Kassi","CIMT17 BH660-FAW-40%", "CIMT19 MELKASA2-FAW-40%", "CIMT21 MELKASA-LowY"],
    "MZ": ["CIMT01 BH540","CIMT02 MELKASA-1","CIMT17 BH660-FAW-40%", "CIMT19 MELKASA2-FAW-40%", "CIMT21 MELKASA-LowY"],
    "WH": ["CI2021 KT-KUB", "CI2022 RMSI", "CI2023 Meda wolabu", "CI2024 Sofumer", "CI2025 Hollandi", "CI2018 ET-MED", "CI2019 ET-LNG"],
    "SG": ["IB0020 ESH-1","IB0020 ESH-2","IB0027 Dekeba","IB0027 Melkam","IB0027 Teshale"]
}
# Wdir_path = "C:\\IRI\\Python_Dash\\ET_DSS_hist\\TEST\\"
Wdir_path = DSSAT_FILES_DIR    #for linux systemn

SIMAGRI_LOGOS = app.get_asset_url("../assets/ethioagroclimate.png")

app.layout = html.Div( ## MAIN APP DIV
[
  dcc.Store(id="memory-yield-table"),  #to save fertilizer application table
  dcc.Store(id="memory-sorted-yield-table"),  #to save fertilizer application table
  dcc.Store(id="memory-EB-table"),  #to save fertilizer application table

  # NAVBAR
  Navbar(SIMAGRI_LOGOS),

  html.Div( ## HISTORICAL: INPUT AND GRAPHS
    dbc.Row([ 
      dbc.Col([ ## LEFT HAND SIDE
        html.Div(
          html.Div([
            html.Header(
              html.B(
                "Simulation Input",
              ),
            className=" card-header",
            ),

            dbc.Form([ ## INPUT FORM
              html.Div( # SCROLLABLE FORM
                html.Div([ # FORM START
                  dbc.FormGroup([ # Scenario
                    dbc.Label("1) Scenario Name", html_for="sce-name", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dbc.Input(type="text", id="sce-name", value="", minLength=4, maxLength=4, required="required", ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Station
                    dbc.Label("2) Station", html_for="ETstation", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.Dropdown(
                        id="ETstation",
                        options=[
                          {"label": "Melkasa", "value": "MELK"},
                          {"label": "Mieso", "value": "MEIS"},
                          {"label": "Awassa", "value": "AWAS"},
                          {"label": "Asella", "value": "ASEL"},
                          {"label": "Bako", "value": "BAKO"},
                          {"label": "Mahoni", "value": "MAHO"},
                          {"label": "Kobo", "value": "KOBO"}
                        ],
                        value="MELK",
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Crop
                    dbc.Label("3) Crop", html_for="crop-radio", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.RadioItems(
                        id="crop-radio",
                        # options=[{"label": k, "value": k} for k in cultivar_options.keys()],
                        options = [
                          {"label": "Maize", "value": "MZ"}, 
                          {"label": "Wheat", "value": "WH"}, 
                          {"label": "Sorghum", "value": "SG"},
                        ],
                        labelStyle = {"display": "inline-block","margin-right": 10},
                        value="MZ",
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Cultivar
                    dbc.Label("4) Cultivar", html_for="cultivar-dropdown", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.Dropdown(
                        id="cultivar-dropdown", 
                        options=[
                          {"label": "CIMT01 BH540", "value": "CIMT01 BH540-Kassie"},
                          {"label": "CIMT02 MELKASA-1", "value": "CIMT02 MELKASA-Kassi"},
                          {"label": "CIMT17 BH660-FAW-40%", "value": "CIMT17 BH660-FAW-40%"},
                          {"label": "CIMT19 MELKASA2-FAW-40%", "value": "CIMT19 MELKASA2-FAW-40%"},
                          {"label": "CIMT21 MELKASA-LowY", "value": "CIMT21 MELKASA-LowY"},], 
                        value="CIMT19 MELKASA2-FAW-40%",
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Start Year
                    dbc.Label("5) Start Year", html_for="year1", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dbc.Input(type="number", id="year1", placeholder="YYYY", value="1981", min=1981, max=2018, required="required", ),
                      dbc.FormText("(No earlier than 1981)"),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # End Year
                    dbc.Label("6) End Year", html_for="year2", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dbc.Input(type="number", id="year2", placeholder="YYYY", value="2018", min=1981, max=2018, required="required", ),
                      dbc.FormText("(No later than 2018)"),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Year to Highlight
                    dbc.Label("7) Year to Highlight", html_for="target-year", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dbc.Input(type="number", id="target-year", placeholder="YYYY", value="2015",min=1981, max=2018, required="required", ),
                      dbc.FormText("Type a specific year you remember (e.g., drought year) and want to compare with a full climatology distribution"),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Soil Type
                    dbc.Label("8) Soil Type", html_for="ETsoil", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.Dropdown(
                        id="ETsoil", 
                        options=[
                          {"label": "ETET000010(AWAS,L)", "value": "ETET000010"},
                          {"label": "ETET000_10(AWAS,L, shallow)", "value": "ETET000_10"},
                          {"label": "ETET000011(BAKO,C)", "value": "ETET000011"},
                          {"label": "ETET001_11(BAKO,C,shallow)", "value": "ETET001_11"},
                          {"label": "ETET000018(MELK,L)", "value": "ETET000018"},
                          {"label": "ETET001_18(MELK,L,shallow)", "value": "ETET001_18"},
                          {"label": "ETET000015(KULU,C)", "value": "ETET000015"},
                          {"label": "ETET001_15(KULU,C,shallow)", "value": "ETET001_15"},
                          {"label": "ET00990066(MAHO,C)", "value": "ET00990066"},
                          {"label": "ET00990_66(MAHO,C,shallow)", "value": "ET00990_66"},
                          {"label": "ET00920067(KOBO,CL)", "value": "ET00920067"},
                          {"label": "ET00920_67(KOBO,CL,shallow)", "value": "ET00920_67"},
                          {"label": "ETET000022(MIES, C)", "value": "ETET000022"},
                          {"label": "ETET001_22(MIES, C, shallow", "value": "ETET001_22"},
                        ],
                        value="ETET001_18",
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Initial Soil Water Condition
                    dbc.Label("9) Initial Soil Water Condition", html_for="ini-H2O", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.Dropdown(
                        id="ini-H2O", 
                        options=[
                          {"label": "30% of AWC", "value": "0.3"},
                          {"label": "50% of AWC", "value": "0.5"},
                          {"label": "70% of AWC", "value": "0.7"},
                          {"label": "100% of AWC", "value": "1.0"},
                        ], 
                        value="0.5",
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Initial NO3 Condition
                    dbc.Label("10) Initial NO3 Condition", html_for="ini-NO3", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.Dropdown(
                        id="ini-NO3", 
                        options=[
                          {"label": "High(65 N kg/ha)", "value": "H"},
                          {"label": "Low(23 N kg/ha)", "value": "L"},
                        ], 
                        value="L",
                      ),                
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Planting Date
                    dbc.Label("11) Planting Date", html_for="plt-date-picker", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.DatePickerSingle(
                      id="plt-date-picker",
                      min_date_allowed=date(2021, 1, 1),
                      max_date_allowed=date(2021, 12, 31),
                      initial_visible_month=date(2021, 6, 5),
                      display_format="DD/MM/YYYY",
                      date=date(2021, 6, 15),
                      ),
                      dbc.FormText("Only Month and Date are counted"),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  # type="number"    
                  dbc.FormGroup([ # Planting Density
                    dbc.Label(["12) Planting Density", html.Span(" (plants/m"), html.Sup("2"), html.Span(")"), ], html_for="plt-density", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dbc.Input(type="number", id="plt-density", value=5, min=1, max=300, step=0.1, required="required", ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Fertilizer Application
                    dbc.Label("13) Fertilizer Application", html_for="fert_input", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.RadioItems(
                        id="fert_input",
                        options=[
                          {"label": "Fertilizer", "value": "Fert"},
                          {"label": "No Fertilizer", "value": "No_fert"},
                        ],
                        labelStyle = {"display": "inline-block","margin-right": 10},
                        value="No_fert",
                      ),
                      html.Div([ # FERTILIZER INPUT TABLE
                        dbc.Row([
                          dbc.Col(
                            dbc.Label("Days After Planting", className="text-center", ),
                          ),
                          dbc.Col(
                            dbc.Label("Amount of N (kg/ha)", className="text-center", ),
                          ),
                        ],),
                        dbc.Row([
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("1st", html_for="fert-day1", ),
                              dbc.Input(type="number", id="fert-day1", value=0, min="0", max="365", required="required", ),
                            ],),
                          ),
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("1st", html_for="fert-amt1", ),
                              dbc.Input(type="number", id="fert-amt1", value=0, min="0", step="0.1", required="required", ),
                            ],),
                          ),
                        ],),
                        dbc.Row([
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("2nd", html_for="fert-day2", ),
                              dbc.Input(type="number", id="fert-day2", value=0, min="0", max="365", required="required", ),
                            ],),
                          ),
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("2nd", html_for="fert-amt2", ),
                              dbc.Input(type="number", id="fert-amt2", value=0, min="0", step="0.1", required="required", ),
                            ],),
                          ),
                        ],),
                        dbc.Row([
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("3rd", html_for="fert-day3", ),
                              dbc.Input(type="number", id="fert-day3", value=0, min="0", max="365", required="required", ),
                            ],),
                          ),
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("3rd", html_for="fert-amt3", ),
                              dbc.Input(type="number", id="fert-amt3", value=0, min="0", step="0.1", required="required", ),
                            ],),
                          ),
                        ],),
                        dbc.Row([
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("4th", html_for="fert-day4", ),
                              dbc.Input(type="number", id="fert-day4", value=0, min="0", max="365", required="required", ),
                            ],),
                          ),
                          dbc.Col(
                            dbc.FormGroup([
                              dbc.Label("4th", html_for="fert-amt4", ),
                              dbc.Input(type="number", id="fert-amt4", value=0, min="0", step="0.1", required="required", ),
                            ],),
                          ),
                        ],),
                      ],
                      id="fert-table-Comp", 
                      className="w-100",
                      style={"display": "none"},
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  dbc.FormGroup([ # Enterprise Budgeting?
                    dbc.Label("14) Enterprise Budgeting?", html_for="EB_radio", sm=3, className="p-0", align="start", ),
                    dbc.Col([
                      dcc.RadioItems(
                        id="EB_radio",
                        options=[
                          {"label": "Yes", "value": "EB_Yes"},
                          {"label": "No", "value": "EB_No"},
                        ],
                        labelStyle = {"display": "inline-block","margin-right": 10},
                        value="EB_No",
                      ),
                      html.Div([ # ENTERPRISE BUDGETING TABLE
                        dbc.Row([
                          dbc.Col([  
                            dbc.FormGroup([
                              dbc.Label("Crop Price", html_for="crop-price", style={"height": "7vh"}, align="start", ),
                              dbc.Input(type="number", id="crop-price", value="0", min="0", step="0.1", required="required", ),
                              dbc.FormText("[ETB/kg]"),
                            ]),
                          ],),
                          dbc.Col([  
                            dbc.FormGroup([
                              dbc.Label("Fertilizer Price", html_for="fert-cost", style={"height": "7vh"}, align="start", ),
                              dbc.Input(type="number", id="fert-cost", value="0", min="0", step="0.1", required="required", ),
                              dbc.FormText("[ETB/N kg]"),
                            ]),
                          ],),
                          dbc.Col([  
                            dbc.FormGroup([
                              dbc.Label("Seed Cost", html_for="seed-cost", style={"height": "7vh"}, align="start", ),
                              dbc.Input(type="number", id="seed-cost", value="0", min="0", step="0.1", required="required", ),
                              dbc.FormText("[ETB/ha]"),
                            ]),
                          ],),
                          dbc.Col([  
                            dbc.FormGroup([
                              dbc.Label("Other Variable Costs", html_for="variable-costs", style={"height": "7vh"}, align="start", ),
                              dbc.Input(type="number", id="variable-costs", value="0", min="0", step="0.1", required="required", ),
                              dbc.FormText("[ETB/ha]"),
                            ]),
                          ],),
                          dbc.Col([  
                            dbc.FormGroup([
                              dbc.Label("Fixed Costs", html_for="fixed-costs", style={"height": "7vh"}, align="start", ),
                              dbc.Input(type="number", id="fixed-costs", value="0", min="0", step="0.1", required="required", ),
                              dbc.FormText("[ETB/ha]"),
                            ]),
                          ],),
                        ],),
                        dbc.FormText("See the Tutorial for more details of calculation"),
                      ],
                      id="EB-table-Comp", 
                      className="w-100",
                      style={"display": "none"},
                      ),
                    ],
                    xl=9,
                    ),
                  ],
                  row=True
                  ),
                  # INPUT FORM END
                ], 
                className="p-3"
                ),
              className="overflow-auto",
              style={"height": "63vh"},
              ),

              html.Div([ # SCENARIO TABLE
                # Deletable summary table : EJ(5/3/2021)
                html.Header(html.B("Scenarios"), className="card-header",),
                dbc.FormGroup([ # SUBMIT - ADD SCENARIO
                  dbc.Button(id="write-button-state", 
                  n_clicks=0, 
                  # type="submit",
                  children="Create or Add a new Scenario", 
                  className="w-75 d-block mx-auto my-3",
                  color="primary"
                  ),
                ]),
                dash_table.DataTable(
                id="scenario-table",
                columns=([
                  {"id": "sce_name", "name": "Scenario Name"},
                  {"id": "Crop", "name": "Crop"},
                  {"id": "Cultivar", "name": "Cultivar"},
                  {"id": "stn_name", "name": "Station"},
                  {"id": "Plt-date", "name": "Planting Date"},
                  {"id": "FirstYear", "name": "First Year"},
                  {"id": "LastYear", "name": "Last Year"},
                  {"id": "soil", "name": "Soil Type"},
                  {"id": "iH2O", "name": "Initial Soil Water Content"},
                  {"id": "iNO3", "name": "Initial Soil Nitrate Content"},
                  {"id": "TargetYr", "name": "Target Year"},
                  {"id": "Fert_1_DOY", "name": "DOY 1st Fertilizer Applied"},
                  {"id": "Fert_1_Kg", "name": "1st Amount Applied (Kg/ha)"},
                  {"id": "Fert_2_DOY", "name": "DOY 2nd Fertilizer Applied"},
                  {"id": "Fert_2_Kg", "name": "2nd Amount Applied(Kg/ha)"},
                  {"id": "Fert_3_DOY", "name": "DOY 3rd Fertilizer Applied"},
                  {"id": "Fert_3_Kg", "name": "3rd Amount Applied(Kg/ha)"},
                  {"id": "Fert_4_DOY", "name": "DOY 4th Fertilizer Applied"},
                  {"id": "Fert_4_Kg", "name": "4th Amount Applied(Kg/ha)"},
                  {"id": "CropPrice", "name": "Crop Price"},
                  {"id": "NFertCost", "name": "Fertilizer Cost"},
                  {"id": "SeedCost", "name": "Seed Cost"},
                  {"id": "OtherVariableCosts", "name": "Other Variable Costs"},
                  {"id": "FixedCosts", "name": "Fixed Costs"},
                ]),
                data=[
                  dict(**{param: "N/A" for param in sce_col_names}) for i in range(1, 2)
                ],
                style_table = {
                  "overflowX": "auto",
                  "minWidth": "100%",
                },
                fixed_columns = { "headers": True, "data": 1 },
                style_cell = {   # all three widths are needed
                  "minWidth": "120px", "width": "120px", "maxWidth": "150px",
                  "overflow": "hidden",
                  "textOverflow": "ellipsis", 
                },
                # editable=True,
                row_deletable=True
                )                # end of Deletable summary table : EJ(5/3/2021)
              ]),
            ]),

            html.Div([ # AFTER SCENARIO TABLE
              dbc.FormGroup([ # Approximate Growing Season
                dbc.Label("15) Critical growing period to relate rainfall amount with crop yield", html_for="season-slider"),
                dbc.FormText("Selected period is used to sort drier/wetter years based on the seasonal total rainfall"),
                dcc.RangeSlider(
                  id="season-slider",
                  min=1, max=12, step=1,
                  marks={1: "Jan", 2: "Feb",3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"},
                  value=[6, 9]
                ),
              ],
              ),
              html.Br(),
              html.Div( ## RUN DSSAT BUTTON
                dbc.Button(id="simulate-button-state", 
                children="Simulate all scenarios (Run DSSAT)",
                className="w-75 d-block mx-auto",
                color="success",
                ),
              )
            ],
            className="p-3",
            ),

          ], 
          ),
        className="block card",
        ),
      ], 
      md=5,
      className="p-1",
      ),
      dbc.Col([ ## RIGHT HAND SIDE -- CARDS WITH SIMULATION ETC
        html.Div([
          html.Div( # SIMULATIONS
            html.Div([
              html.Header(
                html.B("Simulation Graphs"),
              className=" card-header"
              ),
              html.Div(
                html.Div([
                  html.Div(
                    html.Div([
                      dbc.Spinner(children=[html.Div(id="yieldbox-container")], size="lg", color="primary", type="border", fullscreen=True,),
                      html.Div(id="yieldcdf-container"),  #exceedance curve
                      html.Div(id="yieldtimeseries-container"),  #time-series
                      dbc.Row([
                        dbc.Col(
                          html.Div(id="yield-BN-container", 
                          ),
                        md=4),
                        dbc.Col(
                          html.Div(id="yield-NN-container", 
                          ),
                        md=4),
                        dbc.Col(
                          html.Div(id="yield-AN-container", 
                          ),
                        md=4),
                      ]),
                    ], 
                    className="plot-container plotly"),
                  className="js-plotly-plot"
                  )
                ], 
                id="simulation-graphs", 
                # className="dash-graph ddk-graph", 
                className="overflow-auto",
                style={"height": "94vh"},
                ),
              ),
            ], 
            ),
          ),
          
          # CSV FOR SIMULATED YIELD
          html.Div( # ORIGINAL CSV
            html.Div([
              html.Header(
                html.B("Simulated Yield Original CSV"),
              className=" card-header"
              ),
              html.Div(
                html.Div([
                  html.Div([
                    html.Div([ # ORIGINAL CSV STUFF
                      dbc.Row([
                        dbc.Col(
                          dbc.Button(id="btn_csv_yield", 
                          children="Download CSV for Simulated Yield", 
                          className="w-100 d-block mx-auto",
                          color="secondary",
                          ),
                        md=4,
                        ),
                        dbc.Col(
                          dbc.Button(id="btn_csv_Pexe", 
                          children="Download CSV for Prob. of Exceedance", 
                          className="w-100 d-block mx-auto",
                          color="secondary",
                          ),
                        md=4,
                        ),
                        dbc.Col(
                          dbc.Button(id="btn_csv_rain", 
                          children="Download CSV for Seasonal Rainfall", 
                          className="w-100 d-block mx-auto",
                          color="secondary",
                          ),
                        md=4,
                        ),
                      ],
                      className="m-3",
                      ),
                      # dcc.Download(id="download-dataframe-csv"),
                      Download(id="download-dataframe-csv-yield"),
                      Download(id="download-dataframe-csv-rain"),
                      Download(id="download-dataframe-csv-Pexe"),
                      html.Div(
                        dash_table.DataTable(
                          columns = [{"id": "YEAR", "name": "YEAR"}],
                          id="yield-table",
                          style_table = {"height": "10vh"},
                        ),
                      id="yieldtables-container", 
                      ),  #yield simulated output
                    ], ),
                  ],
                  ),
                ], 
                id="original-yield-csv-table", 
                className="dash-table-container"
                ),
              ),
            ], 
            ),
          ),
          
          html.Div( # SORTED CSV
            html.Div([
              html.Header(
                html.B("Simulated Yield Sorted CSV"),
              className=" card-header"
              ),
              html.Div(
                html.Div([
                  html.Div([
                    html.Div([ # SORTING CONTROLS AND BUTTON
                      html.Br(),
                      html.Div([
                        html.Span("(i) Select a column name to sort: "),
                        html.Div([dcc.Dropdown(id="column-dropdown", options=[{"label": "YEAR", "value": "YEAR"},],value="YEAR")]),
                      ],
                      ),
                      html.Br(),
                      html.Div([
                        html.Span("(ii) Yield adjustment factor: "),
                        dbc.Input(id="yield-multiplier", type="text", placeholder="Enter ", value = "1"),
                        html.Span(" (e.g., 90% reduction => 0.9)"),  
                      ]),
                      html.Br(),
                      dbc.Button(id="btn_table_sort", 
                      children="Click to update and sort the Datatable by the selected column name", 
                      className="w-75 d-block mx-auto",
                      color="info"
                      ),
                      html.Br(),   
                      #EJ(6/7/2021) to download each column separately into a csv
                      dbc.Button(id="btn_csv2_yield", 
                      children="Download CSV for SORTED simulated Yield", 
                      className="w-75 d-block mx-auto",
                      color="secondary"
                      ),
                      html.Br(),
                      dbc.Button(id="btn_csv2_rain", 
                      children="Download CSV for SORTED seasonal rainfall", 
                      className="w-75 d-block mx-auto",
                      color="secondary"
                      ),
                      html.Br(),
                      dbc.Button(id="btn_csv2_Pexe", 
                      children="Download CSV for SORTED prob. of exceedance", 
                      className="w-75 d-block mx-auto",
                      color="secondary"
                      ),
                      #   Download(id="download-dataframe-csv2"),
                      Download(id="download-dataframe-csv2-yield"),
                      Download(id="download-dataframe-csv2-rain"),
                      Download(id="download-dataframe-csv2-Pexe"),
                    
                      #end of EJ(6/7/2021) update
                      html.Div(id="yieldtables-container2", 
                      className="overflow-auto",
                      style={"height": "20vh"},
                      ),  #sorted yield simulated output
                    ],
                    ),
                  ],
                  ),
                ], 
                id="sorted-yield-csv-table", className="dash-table-container"
                ),
              ),
            ], 
            ),
          className="d-none",
          ),
      

          html.Div( # ENTERPRISE BUDGETING
            html.Div([
              html.Header(
                html.B("Enterprise Budgeting"),
              className=" card-header",
              ),
              html.Div([
                html.Br(),
                dbc.Button(id="EB-button-state", 
                children="Display figures for Enterprise Budgets", 
                className="w-75 d-block mx-auto",
                color="danger"
                ),

                html.Div([
                  html.Div(
                    html.Div([
                      html.Div(id="EBbox-container"), 
                      html.Div(id="EBcdf-container"),  #exceedance curve
                      html.Div(id="EBtimeseries-container"), #exceedance curve

                    ], 
                    className="plot-container plotly"),
                  className="js-plotly-plot"
                  )
                ], 
                id="enterprise-budgeting", 
                className="overflow-auto",
                style={"height": "94vh"},
                ),

                html.Div([
                  html.Br(),
                  dbc.Button(id="btn_csv_EB", 
                  children="Download CSV file for Enterprise Budgeting", 
                  className="w-75 d-block mx-auto",
                  color="secondary"
                  ),
                  # dcc.Download(id="download-dataframe-csv"),
                  Download(id="download-dataframe-csv_EB"),
                  html.Div(id="EBtables-container", 
                  className="overflow-auto",
                  style={"height": "20vh"},
                  ),   #yield simulated output
                ]),
              ]),
            ],
            id="EB-figures",
            style={"display": "none"},
            ),
          ),
        ], 
        className="block card"
        )
      ],
      md=7,
      className="p-1",
      ),
    ],
    className="m-1"
    ),
  ),


  html.Div([ # NAVIGATE TO THESE SECTIONS
    html.Div( ## FORECAST -- HIDDEN FOR NOW
      "HISTORICAL",
    className="d-none",
    ),
    html.Div( ## ABOUT SIMAGRI -- HIDDEN FOR NOW
      dbc.Row( # HEADER AND DESCRIPTION
        dbc.Col([
          dbc.Row(
            # dbc.Col(
            #   html.Div([
            #     html.H4("Climate-Agriculture Modeling Decision Support Tool for Ethiopia"),
            #     html.H4("(Historical Analysis)"),
            #   ],
            #   className="card text-uppercase",
            #   ),
            # md=9,
            # className="mx-auto"
            # )
          ),
          html.Br(),
          html.Div(
            children= """
                        CAMDT is a tool designed to guide decision-makers in adopting appropriate crop and management practices that can improve crop yields given a seasonal climatic condition.
                      """, 
          ),
          html.Br(),
          html.Div(
            children= """
                        Smart planning of annual crop production requires consideration of possible scenarios.
                        The CAMDT tool adopts crop simulation models included in the DSSAT package (Decision Support System for Agrotechnology Transfer). 
                        The methodology was developed by the IRI (International Research Institute for Climate and Society / Columbia University) 
                        in collaboration with the Ethiopian Institute of Agricultural Research (EIAR). 
                        The purpose of this tool is to support decision-making of the producer or technical advisor, which facilitates discussion of optimal production strategies, risks of technology adoption, 
                        and evaluation of long-term effects, considering interactions of various factors.
                      """, 
          ),
          html.Br(),
        ],
        className="text-center"
        )
      ),
    className="d-none",
    ),
  ],
  ),

],
)

#==============================================================
#==============================================================


#==============================================================
#Dynamic call back for sorting datatable by a column name
@app.callback(Output(component_id="yieldtables-container2", component_property="children"),
                Output("memory-sorted-yield-table", "data"),
                # Input("column-dropdown", "value"),
                Input("btn_table_sort", "n_clicks"),
                State("memory-yield-table", "data"),
                State("yield-multiplier", "value"),
                State("column-dropdown", "value"),
                prevent_initial_call=True,
            )
def sort_table(n_clicks, yield_table, multiplier, col_name):
    if n_clicks: 
        df =pd.DataFrame(yield_table)
        df_out = df.sort_values(by=[col_name])
        col = df_out.columns
        for i in range(1,len(col),3):
            temp=df_out.iloc[:,[i]].mul(float(multiplier))  #multiply yield adjustment factor
            temp=temp.astype(int)
            # temp.round(0)  #Round a DataFrame to a variable number of decimal places.
            df_out.iloc[:,i]=temp.values
        return [
            dash_table.DataTable(columns=[{"name": i, "id": i} for i in df_out.columns],data=df_out.to_dict("records"),
                style_table={"overflowX": "auto"}, 
                style_cell={   # all three widths are needed
                    "minWidth": "10px", "width": "10px", "maxWidth": "30px",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis", }),
            df_out.to_dict("records")
            ]

# #call back to save df into a csv file
# @app.callback(
#     Output("download-dataframe-csv2", "data"),
#     Input("btn_csv2", "n_clicks"),
#     State("memory-sorted-yield-table", "data"),
#     prevent_initial_call=True,
# )
# def func(n_clicks, yield_data):
#     df =pd.DataFrame(yield_data)
#     return dcc.send_data_frame(df.to_csv, "simulated_yield_sorted.csv")
#============EJ(6/7/2021)
#1) for yield - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv2-yield", "data"),
    Input("btn_csv2_yield", "n_clicks"),
    State("memory-sorted-yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021)
    col_names = [df.columns[0]]   #list for col names - first column for YEAR
    for i in range(1,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    # df_out.iloc[:,0]=df.iloc[:,[0]].values  #first column for YEAR
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(1,len(col),3):  #for YIELD
        temp=df.iloc[:,i]
        temp=temp.astype(int)
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "simulated_yield_sorted.csv")
#==============================================================
#2) for rainfall - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv2-rain", "data"),
    Input("btn_csv2_rain", "n_clicks"),
    State("memory-sorted-yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021) 
    col_names = [df.columns[0]]   #first column for YEAR
    for i in range(3,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(3,len(col),3):  #for YIELD
        # temp=df.iloc[:,[i]]
        temp=df.iloc[:,i]
        temp=temp.astype(int)
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "seasonal_rainfall_sorted.csv")
#=================================================    
#3) for prob of exceedance - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv2-Pexe", "data"),
    Input("btn_csv2_Pexe", "n_clicks"),
    State("memory-sorted-yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021) 
    col_names = [df.columns[0]]   #first column for YEAR
    for i in range(2,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(2,len(col),3):  #for YIELD
        temp=df.iloc[:,i]
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "prob_of_exceedance_sorted.csv")
#============end of EJ(6/7/2021)
#=================================================    
#==============================================================
#==============================================================
#Dynamic call back for different cultivars for a selected target crop
@app.callback(
    Output("cultivar-dropdown", "options"),
    Input("crop-radio", "value"))
def set_cultivar_options(selected_crop):
    return [{"label": i, "value": i} for i in cultivar_options[selected_crop]]

@app.callback(
    Output("cultivar-dropdown", "value"),
    Input("cultivar-dropdown", "options"))
def set_cultivar_value(available_options):
    return available_options[0]["value"]
#==============================================================
# #call back to save df into a csv file
# @app.callback(
#     Output("download-dataframe-csv", "data"),
#     Input("btn_csv", "n_clicks"),
#     State("memory-yield-table", "data"),
#     prevent_initial_call=True,
# )
# def func(n_clicks, yield_data):
#     df =pd.DataFrame(yield_data)
#     return dcc.send_data_frame(df.to_csv, "simulated_yield.csv")
#============EJ(6/7/2021)
#1) for yield - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv-yield", "data"),
    Input("btn_csv_yield", "n_clicks"),
    State("yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021)
    col_names = [df.columns[0]]   #list for col names - first column for YEAR
    for i in range(1,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    # df_out.iloc[:,0]=df.iloc[:,[0]].values  #first column for YEAR
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(1,len(col),3):  #for YIELD
        temp=df.iloc[:,i]
        temp=temp.astype(int)
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "simulated_yield.csv")
#==============================================================
#2) for rainfall - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv-rain", "data"),
    Input("btn_csv_rain", "n_clicks"),
    State("yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021) 
    col_names = [df.columns[0]]   #first column for YEAR
    for i in range(3,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(3,len(col),3):  #for YIELD
        # temp=df.iloc[:,[i]]
        temp=df.iloc[:,i]
        temp=temp.astype(int)
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "seasonal_rainfall.csv")
#=================================================    
#3) for prob of exceedance - call back to save df into a csv file
@app.callback(
    Output("download-dataframe-csv-Pexe", "data"),
    Input("btn_csv_Pexe", "n_clicks"),
    State("yield-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, yield_data):
    df =pd.DataFrame(yield_data)
    col = df.columns  #EJ(6/7/2021) 
    col_names = [df.columns[0]]   #first column for YEAR
    for i in range(2,len(col),3):  
        col_names.append(df.columns[i])
      
    #make a new filtered dataframe to save into a csv
    df_out = pd.DataFrame(columns = col_names)
    df_out.iloc[:,0] = df.iloc[:,0].values  #first column for YEAR
    k=1
    for i in range(2,len(col),3):  #for YIELD
        temp=df.iloc[:,i]
        df_out.iloc[:,k]=temp.values
        k=k+1 #column index for a new df
    return dcc.send_data_frame(df_out.to_csv, "prob_of_exceedance.csv")
#============end of EJ(6/7/2021)
#=================================================    
#==============================================================
#call back to save Enterprise Budgeting df into a csv file
@app.callback(
    Output("download-dataframe-csv_EB", "data"),
    Input("btn_csv_EB", "n_clicks"),
    State("memory-EB-table", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, EB_data):
    df =pd.DataFrame(EB_data)
    return dcc.send_data_frame(df.to_csv, "simulated_yield_EB.csv")
#=================================================   
#call back to "show/hide" fertilizer input table
@app.callback(Output("fert-table-Comp", component_property="style"),
              Input("fert_input", component_property="value"))
def show_hide_table(visibility_state):
    if visibility_state == "Fert":
        return {"width": "30%","display": "block"}  #{"display": "block"}   
    if visibility_state == "No_fert":
        return {"width": "30%","display": "none"} #"display": "none"} 
#==============================================================
#call back to "show/hide" Enterprise Budgetting input table
@app.callback(Output("EB-table-Comp", component_property="style"),
              Input("EB_radio", component_property="value"))
def show_hide_EBtable(visibility_state):
    if visibility_state == "EB_Yes":
        return {"width": "80%","display": "block"}  #{"display": "block"}   
    if visibility_state == "EB_No":
        return {"width": "80%","display": "none"} #"display": "none"} 
#==============================================================
#call back to "show/hide" Enterprise Budgetting graphs
@app.callback(Output("EB-figures", component_property="style"),
              Input("EB_radio", component_property="value"),
              Input("scenario-table","data"),
)
def show_hide_EBtable(EB_radio, scenarios):
    existing_sces = pd.DataFrame(scenarios)
    if EB_radio == "EB_Yes":
        return {}
    else:
        return {"display": "none"} if existing_sces.sce_name.values[0] == "N/A" or set(existing_sces.CropPrice.values) == {"-99"} else {}

#==============================================================
@app.callback(Output("scenario-table", "data"),
                # Output("intermediate-value", "children"),
                Input("write-button-state", "n_clicks"),
                State("ETstation", "value"),  #input 1
                State("year1", "value"),      #input 2
                State("year2", "value"),      #input 3
                State("plt-date-picker", "date"),  #input 4
                # State("ETMZcultivar", "value"),   #input 5
                State("crop-radio", "value"),  #input 50
                State("cultivar-dropdown", "value"),   #input 5
                State("ETsoil", "value"),         #input 6
                State("ini-H2O", "value"),        #input 7           
                State("ini-NO3", "value"),        #input 8
                State("plt-density", "value"),    #input 9
                State("sce-name", "value"),       #input 10
                State("target-year", "value"),    #input 11
                # State("intermediate-value", "children"),  #input 12 scenario summary table
                State("fert_input", "value"),     ##input 13 fertilizer yes or no
                # State("fert-table","data"), ###input 14 fert input table
                State("fert-day1","value"), ###input 14 fert input table
                State("fert-amt1","value"), ###input 14 fert input table
                State("fert-day2","value"), ###input 14 fert input table
                State("fert-amt2","value"), ###input 14 fert input table
                State("fert-day3","value"), ###input 14 fert input table
                State("fert-amt3","value"), ###input 14 fert input table
                State("fert-day4","value"), ###input 14 fert input table
                State("fert-amt4","value"), ###input 14 fert input table
                State("EB_radio", "value"),     ##input 15 Enterprise budgeting yes or no
                # State("EB-table","data"), #Input 16 Enterprise budget input
                State("crop-price","value"), #Input 16 Enterprise budget input
                State("seed-cost","value"), #Input 16 Enterprise budget input
                State("fert-cost","value"), #Input 16 Enterprise budget input
                State("fixed-costs","value"), #Input 16 Enterprise budget input
                State("variable-costs","value"), #Input 16 Enterprise budget input
                State("scenario-table","data") ###input 17 scenario summary table
            )
def make_sce_table(
    n_clicks, station, start_year, end_year, planting_date, crop, cultivar, soil_type, 
    initial_soil_moisture, initial_soil_no3_content, planting_density, scenario, target_year, 
    fert_app, 
    # fert_in_table, 
    fd1, fa1,
    fd2, fa2,
    fd3, fa3,
    fd4, fa4,
    EB_radio,
    # EB_in_table,
    crop_price,
    seed_cost,
    fert_cost,
    fixed_costs,
    variable_costs,
    sce_in_table
):

    existing_sces = pd.DataFrame(sce_in_table)

    if ( # first check that all required inputs have been given
            scenario == None
        or  start_year == None
        or  end_year == None
        or  target_year == None
        or  planting_date == None
        or  planting_density == None
        or (
                fert_app == "Fert"
            and (
                    fd1 == None or fa1 == None
                or  fd2 == None or fa2 == None
                or  fd3 == None or fa3 == None
                or  fd4 == None or fa4 == None
            ) 
        )
        or (
                EB_radio == "EB_Yes"
            and (
                    crop_price == None
                or  seed_cost == None
                or  fert_cost == None
                or  fixed_costs == None
                or  variable_costs == None
            )
        )        
    ):
        return existing_sces

    # convert integer inputs to string
    start_year = str(start_year)
    end_year = str(end_year)
    target_year = str(target_year)
    planting_density = str(planting_density)

    # Make a new dataframe to return to scenario-summary table
    current_sce = pd.DataFrame({
        "sce_name": [scenario], "Crop": [crop], "Cultivar": [cultivar[7:]], "stn_name": [station], "Plt-date": [planting_date[5:]], 
        "FirstYear": [start_year], "LastYear": [end_year], "soil": [soil_type], "iH2O": [initial_soil_moisture], 
        "iNO3": [initial_soil_no3_content], "plt_density": [planting_density], "TargetYr": [target_year], 
        "Fert_1_DOY": ["-99"], "Fert_1_Kg": ["-99"], "Fert_2_DOY": ["-99"], "Fert_2_Kg": ["-99"], 
        "Fert_3_DOY": ["-99"], "Fert_3_Kg": ["-99"], "Fert_4_DOY": ["-99"], "Fert_4_Kg": ["-99"], 
        "CropPrice": ["-99"], "NFertCost": ["-99"], "SeedCost": ["-99"], "OtherVariableCosts": ["-99"], "FixedCosts": ["-99"],  
    })

    #=====================================================================
    # #Update dataframe for fertilizer inputs
    fert_valid = True
    current_fert = pd.DataFrame(columns=["DAP", "NAmount"])
    if fert_app == "Fert":
        # Read fertilizer application information
        # currrent_fert = pd.DataFrame(fert_in_table)
        current_fert = pd.DataFrame({
            "DAP": [fd1, fd2, fd3, fd4, ],
            "NAmount": [fa1, fa2, fa3, fa4, ],
        })

        fert_frame =  pd.DataFrame({
            "Fert_1_DOY": [fd1], "Fert_1_Kg": [fa1],
            "Fert_2_DOY": [fd2], "Fert_2_Kg": [fa2],
            "Fert_3_DOY": [fd3], "Fert_3_Kg": [fa3],
            "Fert_4_DOY": [fd4], "Fert_4_Kg": [fa4],
        })
        current_sce.update(fert_frame)

    #=====================================================================
    # Write SNX file
    writeSNX_main_hist(Wdir_path,station,start_year,end_year,planting_date,crop, cultivar,soil_type,initial_soil_moisture,initial_soil_no3_content,
                        planting_density,scenario,fert_app, current_fert)
    #=====================================================================
    # #Update dataframe for Enterprise Budgeting inputs
    EB_valid = True
    if EB_radio == "EB_Yes":
        # Read Enterprise budget input
        # current_EB = pd.DataFrame(EB_in_table)
        
        EB_frame =  pd.DataFrame({
            "CropPrice": [crop_price],
            "NFertCost": [seed_cost],
            "SeedCost": [fert_cost],
            "OtherVariableCosts": [fixed_costs],
            "FixedCosts": [variable_costs],
        })
        current_sce.update(EB_frame)
    # else:
    #     current_EB = pd.DataFrame(
    #         columns=["sce_name","Crop", "Cultivar","stn_name", "Plt-date", "FirstYear", "LastYear", "soil","iH2O","iNO3","plt_density","TargetYr",
    #             "Fert_1_DOY","Fert_1_Kg","Fert_2_DOY","Fert_2_Kg","Fert_3_DOY","Fert_3_Kg","Fert_4_DOY","Fert_4_Kg",
    #             "CropPrice", "NFertCost", "SeedCost","OtherVariableCosts","FixedCosts"
    #         ]
    #     )

    form_valid = (
            re.match("....", current_sce.sce_name.values[0]) 
        and int(current_sce.FirstYear.values[0]) >= 1981 and int(current_sce.FirstYear.values[0]) <= 2018 
        and int(current_sce.LastYear.values[0]) >= 1981 and int(current_sce.LastYear.values[0]) <= 2018 
        and int(current_sce.TargetYr.values[0]) >= 1981 and int(current_sce.TargetYr.values[0]) <= 2018 
        and float(current_sce.plt_density.values[0]) >= 1 and float(current_sce.plt_density.values[0]) <= 300
        and fert_valid and EB_valid
    )

    if form_valid:
        # Read previously saved scenario summaries  https://dash.plotly.com/sharing-data-between-callbacks
        # all_sces = pd.read_json(intermediate, orient="split")
            
        if n_clicks == 1 or existing_sces.sce_name.values[0] == "N/A": # overwrite if a row of "N/A" values present. should only happen first time
            data = current_sce.to_dict("rows")
        else:
            if scenario in existing_sces.sce_name.values: # prevent adding scenarios with the same name.
                data = existing_sces.to_dict("rows")
            else:
                all_sces = current_sce.append(existing_sces, ignore_index=True)
                data = all_sces.to_dict("rows")
        return data
    else:
        # TODO: Alert about errors in form
        return existing_sces.to_dict("rows")


#===============================
#2nd callback to run ALL scenarios
@app.callback(Output(component_id="yieldbox-container", component_property="children"),
                Output(component_id="yieldcdf-container", component_property="children"),
                Output(component_id="yieldtimeseries-container", component_property="children"),
                Output(component_id="yield-BN-container", component_property="children"),
                Output(component_id="yield-NN-container", component_property="children"),
                Output(component_id="yield-AN-container", component_property="children"),
                Output(component_id="yieldtables-container", component_property="children"),
                Output("memory-yield-table", "data"),
                Output("column-dropdown", "options"), #EJ(5/19/2021) update dropdown list for sorting a datatable
                Input("simulate-button-state", "n_clicks"),
                # State("target-year", "value"),       #input 11
                # State("intermediate-value", "children") #scenario summary table
                State("scenario-table","data"), ### scenario summary table
                State("season-slider", "value"), #EJ (5/13/2021) for seasonal total rainfall
                prevent_initial_call=True,
              )

def run_create_figure(n_clicks, sce_in_table, slider_range):
    if n_clicks is None:
        raise PreventUpdate
        return 
    else: 
        # 1) Read saved scenario summaries and get a list of scenarios to run
        # dff = pd.read_json(intermediate, orient="split")
        dff = pd.DataFrame(sce_in_table)  #read dash_table.DataTable into pd df #J(5/3/2021)
        sce_numbers = len(dff.sce_name.values)
        # Wdir_path = "C:\\IRI\\Python_Dash\\ET_DSS_hist\\TEST\\"
        Wdir_path = DSSAT_FILES_DIR   #for linux system
        TG_yield = []

        #EJ(5/3/2021) run DSSAT for each scenarios with individual V47
            #EJ(5/18/2021)variables for extracting seasonal total rainfall
        m1, m2 = slider_range
        m_doys_list = [1,32,60,91,121,152,182,213,244,274,305,335]
        m_doye_list = [31,59,90,120,151,181,212,243,273,304,334,365]
        sdoy = m_doys_list[m1-1]  #first doy of the target season
        edoy = m_doye_list[m2-1]  #last doy of the target season

        for i in range(sce_numbers):
            # EJ(5/18/2021) extract seasonal rainfall total
            firstyear = int(dff.FirstYear[i])
            lastyear = int(dff.LastYear[i])
            WTD_fname = path.join(Wdir_path, dff.stn_name[i]+".WTD")
            df_obs = read_WTD(WTD_fname,firstyear, lastyear)  # === Read daily observations into a dataframe (note: Feb 29th was skipped in df_obs)
            df_season_rain = season_rain_rank(df_obs, sdoy, edoy)  #get indices of the sorted years based on SCF1 => df_season_rain.columns = ["YEAR","season_rain", "Rank"]  
            #==============end of # EJ(5/18/2021) extract seasonal rainfall total

            # 2) Write V47 file
            if dff.Crop[i] == "WH":
                temp_dv7 = path.join(Wdir_path, "DSSBatch_template_WH.V47")
            elif dff.Crop[i] == "MZ":
                temp_dv7 = path.join(Wdir_path, "DSSBatch_template_MZ.V47")
            else:  # SG
                temp_dv7 = path.join(Wdir_path, "DSSBatch_template_SG.V47")

            dv7_fname = path.join(Wdir_path, "DSSBatch.V47")
            fr = open(temp_dv7, "r")  # opens temp DV4 file to read
            fw = open(dv7_fname, "w")
            # read template and write lines
            for line in range(0, 10):
                temp_str = fr.readline()
                fw.write(temp_str)

            temp_str = fr.readline()
            sname = dff.sce_name.values[i]
            # SNX_fname = path.join(Wdir_path, "ETMZ"+sname+".SNX")
            if dff.Crop[i] == "WH":
                SNX_fname = path.join(Wdir_path, "ETWH"+sname+".SNX")
            elif dff.Crop[i] == "MZ":
                SNX_fname = path.join(Wdir_path, "ETMZ"+sname+".SNX")
            else:  # SG
                SNX_fname = path.join(Wdir_path, "ETSG"+sname+".SNX")

            # On Linux system, we don"t need to do this:
            # SNX_fname = SNX_fname.replace("/", "\\")
            new_str2 = "{0:<95}{1:4s}".format(SNX_fname, repr(1).rjust(4)) + temp_str[99:]
            fw.write(new_str2)
            fr.close()
            fw.close()
            #=====================================================================
            #3) Run DSSAT executable
            os.chdir(Wdir_path)  #change directory  #check if needed or not
            # if dff.Crop[i] == "WH":
            #     args = "DSCSM047.EXE CSCER047 B DSSBatch.v47"
            #     fout_name = path.join(Wdir_path, "ETWH"+sname+".OSU")
            # elif dff.Crop[i] == "MZ":
            #     args = "DSCSM047.EXE MZCER047 B DSSBatch.v47"
            #     fout_name = path.join(Wdir_path, "ETMZ"+sname+".OSU")
            # else:  # SG
            #     args = "DSCSM047.EXE SGCER047 B DSSBatch.v47"
            #     fout_name = path.join(Wdir_path, "ETSG"+sname+".OSU")
            # subprocess.call(args) ##Run executable with argument  , stdout=FNULL, stderr=FNULL, shell=False)
            #===========>for linux system
            if dff.Crop[i] == "WH":
                args = "./DSCSM047.EXE CSCER047 B DSSBatch.V47"
                # args = "./DSCSM047.EXE B DSSBatch.V47"
                fout_name = "ETWH"+sname+".OSU"
                arg_mv = "cp Summary.OUT "+ "ETWH"+sname+".OSU" #"cp Summary.OUT $fout_name"
                # fout_name = path.join(Wdir_path, "ETWH"+sname+".OSU")
            elif dff.Crop[i] == "MZ":
                args = "./DSCSM047.EXE MZCER047 B DSSBatch.V47"
                fout_name = "ETMZ"+sname+".OSU"
                arg_mv = "cp Summary.OUT "+ "ETMZ"+sname+".OSU" #"cp Summary.OUT $fout_name"
                # fout_name = path.join(Wdir_path, "ETMZ"+sname+".OSU")
            else:  # SG
                args = "./DSCSM047.EXE SGCER047 B DSSBatch.V47"
                fout_name = "ETSG"+sname+".OSU"
                arg_mv = "cp Summary.OUT "+ "ETSG"+sname+".OSU"# "cp Summary.OUT $fout_name"
                # fout_name = path.join(Wdir_path, "ETSG"+sname+".OSU")

            os.system(args) 
            os.system(arg_mv) 
            #===========>end of for linux system

            #4) read DSSAT output => Read Summary.out from all scenario output
            # fout_name = path.join(Wdir_path, "SUMMARY.OUT")
            df_OUT=pd.read_csv(fout_name,delim_whitespace=True ,skiprows=3)
            HWAM = df_OUT.iloc[:,20].values  #read 21th column only
            EXPERIMENT = df_OUT.iloc[:,7].values  #read 4th column only
            PDAT = df_OUT.iloc[:,13].values  #read 14th column only
            ADAT = df_OUT.iloc[:,15].values  #read 14th column only
            MDAT = df_OUT.iloc[:,16].values  #read 14th column only    
            YEAR = df_OUT.iloc[:,13].values//1000
            if int(dff.TargetYr[i]) <= int(dff.LastYear[i]):
                doy = repr(PDAT[0])[4:]
                target = dff.TargetYr[i] + doy
                yr_index = np.argwhere(PDAT == int(target))
        
                TG_yield_temp = HWAM[yr_index[0][0]]
            else: 
                TG_yield_temp = np.nan

            # Make a new dataframe for plotting
            data = {"EXPERIMENT":EXPERIMENT, "YEAR":YEAR, "PDAT": PDAT, "ADAT":ADAT, "HWAM":HWAM,"RAIN":df_season_rain.season_rain.values,"RANK":df_season_rain.Rank.values}
            temp_df = pd.DataFrame (data, columns = ["EXPERIMENT","YEAR", "PDAT","ADAT","HWAM", "RAIN", "RANK"])

            if i==0:
                df = temp_df.copy()
            else:
                df = df.append(temp_df, ignore_index=True)
                
            TG_yield.append(TG_yield_temp)

        df = df.round({"RAIN": 0})  #Round a DataFrame to a variable number of decimal places.
        yield_min = np.min(df.HWAM.values)  #to make a consistent yield scale for exceedance curve =>Fig 4,5,6
        yield_max = np.max(df.HWAM.values)
        x_val = np.unique(df.EXPERIMENT.values)
        
        #4) Make a boxplot
        # df = px.data.tips()
        # fig = px.box(df, x="time", y="total_bill")
        # fig.show()s
        # fig.update_layout(transition_duration=500)
        # df = px.data.tips()
        # fig = px.box(df, x="Scenario Name", y="Yield [kg/ha]")
        yld_box = px.box(df, x="EXPERIMENT", y="HWAM", title="Yield Boxplot")
        yld_box.add_scatter(x=x_val,y=TG_yield, mode="markers") #, mode="lines+markers") #"lines")
        yld_box.update_xaxes(title= "Scenario Name [*Note:Red dot(s) represents yield(s) based on the weather of target year]")
        yld_box.update_yaxes(title= "Yield [kg/ha]")
        # # return fig

        yld_exc = go.Figure()
        for i in x_val:
            x_data = df.HWAM[df["EXPERIMENT"]==i].values
            x_data = np.sort(x_data)
            fx_scf = [1.0/len(x_data)] * len(x_data) #pdf
            Fx_scf= 1.0-np.cumsum(fx_scf)  #for exceedance curve

            yld_exc.add_trace(go.Scatter(x=x_data, y=Fx_scf,
                        mode="lines+markers",
                        name=i[4:]))
        # Edit the layout
        yld_exc.update_layout(title="Yield Exceedance Curve",
                        xaxis_title="Yield [kg/ha]",
                        yaxis_title="Probability of Exceedance [-]")

        #make a new dataframe to save into CSV
        yr_val = np.unique(df.YEAR.values)
        df_out = pd.DataFrame({"YEAR":yr_val})

        yld_t_series = go.Figure()
        BN_exc = go.Figure() #yield exceedance curve using only BN category
        NN_exc = go.Figure()  #yield exceedance curve using only NN category
        AN_exc = go.Figure()  #yield exceedance curve using only AN category
        for i in x_val:
            x_data = df.YEAR[df["EXPERIMENT"]==i].values
            y_data = df.HWAM[df["EXPERIMENT"]==i].values
            yield_rank = y_data.argsort().argsort() + 1 #<<<<<<==================
            yield_Pexe = np.around(1-[1.0/len(y_data)] * yield_rank, 2) #<<<<<<=====probability of exceedance,  round to the given number of decimals.
            rain_data = df.RAIN[df["EXPERIMENT"]==i].values  # EJ(5/18/2021) seasonal rainfall total
            rain_rank = df.RANK[df["EXPERIMENT"]==i].values  # EJ(5/18/2021) rank of seasonal rainfall total

            ##make a new dataframe to save into CSV 
            col_name0 = "Yield_" + i[4:]
            col_name1 = "Y_Pexe_" + i[4:]
            col_name2 = "Rain_" + i[4:]
            df_temp = pd.DataFrame({col_name0:y_data, col_name1:yield_Pexe, col_name2:rain_data})  # EJ(5/18/2021) seasonal rainfall total
            df_out = pd.concat([df_out, df_temp], axis=1)

            yld_t_series.add_trace(go.Scatter(x=x_data, y=y_data,
                        mode="lines+markers",
                        name=i[4:]))
            #==================================================
            #exceedance curve for BN
            BN_thres = len(rain_rank)//3  #Return the largest integer smaller or equal to the division of the inputs. 
            NN_thres = len(rain_rank) - BN_thres
            #1)BN
            x_data = y_data[rain_rank <= BN_thres]
            x_data = np.sort(x_data)
            fx_scf = [1.0/len(x_data)] * len(x_data) #pdf
            Fx_scf= 1.0-np.cumsum(fx_scf)  #for exceedance curve
            BN_exc.add_trace(go.Scatter(x=x_data, y=Fx_scf, mode="lines+markers", name=i[4:]))
            #2)NN
            mask = np.logical_and(rain_rank > BN_thres, rain_rank <= NN_thres)
            x_data = y_data[mask]
            # x_data = y_data[rain_rank > BN_thres & rain_rank <= NN_thres]
            x_data = np.sort(x_data)
            fx_scf = [1.0/len(x_data)] * len(x_data) #pdf
            Fx_scf= 1.0-np.cumsum(fx_scf)  #for exceedance curve
            NN_exc.add_trace(go.Scatter(x=x_data, y=Fx_scf, mode="lines+markers", name=i[4:]))
            #3)AN
            x_data = y_data[rain_rank > NN_thres]
            x_data = np.sort(x_data)
            fx_scf = [1.0/len(x_data)] * len(x_data) #pdf
            Fx_scf= 1.0-np.cumsum(fx_scf)  #for exceedance curve
            AN_exc.add_trace(go.Scatter(x=x_data, y=Fx_scf, mode="lines+markers", name=i[4:]))
            #====================================================                
        # Edit the layout
        yld_t_series.update_layout(title="Yield Time-Series",
                        xaxis_title="Year",
                        yaxis_title="Yield [kg/ha]")
        BN_exc.update_layout(title="Yield Exceedance [Dry category]",
                        xaxis_title="Yield [kg/ha]",
                        yaxis_title="Probability of Exceedance [-]",
                        legend=dict(yanchor="bottom", y=0.1, xanchor="left", x=0.01))
        BN_exc.update_xaxes(range=[yield_min, yield_max])
        NN_exc.update_layout(title="Yield Exceedance [Normal category]",
                        xaxis_title="Yield [kg/ha]",
                        yaxis_title="Probability of Exceedance [-]",
                        legend=dict(yanchor="bottom", y=0.1, xanchor="left", x=0.01))
        NN_exc.update_xaxes(range=[yield_min, yield_max])
        AN_exc.update_layout(title="Yield Exceedance [Wet category]",
                        xaxis_title="Yield [kg/ha]",
                        yaxis_title="Probability of Exceedance [-]",
                        legend=dict(yanchor="bottom", y=0.1, xanchor="left", x=0.01))
        AN_exc.update_xaxes(range=[yield_min, yield_max])

        #save simulated yield outputs into a csv file <<<<<<=======================
        fname = path.join(Wdir_path, "simulated_yield.csv")
        df_out.to_csv(fname, index=False)
        #print({"label": i, "value": i} for i in list(df_out.columns))

        return [
            dcc.Graph(id="yield-boxplot",figure=yld_box), 
            dcc.Graph(id="yield-exceedance",figure=yld_exc),
            dcc.Graph(id="yield-ts",figure=yld_t_series),
            dcc.Graph(id="yield-BN_exceedance",figure=BN_exc),
            dcc.Graph(id="yield-NN_exceedance",figure=NN_exc),
            dcc.Graph(id="yield-AN_exceedance",figure=AN_exc),
            dash_table.DataTable(columns = [{"name": i, "id": i} for i in df_out.columns],data=df_out.to_dict("records"),
              id="yield-table",
              sort_action = "native",
              sort_mode = "single",
              style_table = {
                "maxHeight": "30vh",
                "overflow": "auto",
                "minWidth": "100%",
              },
              fixed_rows = { "headers": True, "data": 0 },
              fixed_columns = { "headers": True, "data": 1 },
              style_cell = {   # all three widths are needed
                "minWidth": "120px", "width": "120px", "maxWidth": "150px",
                "overflow": "hidden",
                "textOverflow": "ellipsis", 
              }
            ),
            df_out.to_dict("records"),
            [{"label": i, "value": i} for i in list(df_out.columns)]
            ]
#==============================================================
#==============================================================
#Dynamic call back for update dropdown values, before datatable filtering by col name
# @app.callback(
#     Output("column-dropdown", "options"),
#     Input("btn_table_sort", "n_clicks"),
#     State("memory-yield-table", "data"),
#     prevent_initial_call=True,
#     )
# def set_column_options(n_clicks, yield_table):
#     df =pd.DataFrame(yield_table)
#     return [{"label": i, "value": i} for i in list(df.columns)]
#==============================================================
#==============================================================
@app.callback(
    Output("column-dropdown", "value"),
    Input("column-dropdown", "options"))
def set_column_value(available_options):
    # return cultivar_options[0]["value"]
    return [available_options[i]["value"] for i in range(len(available_options))]

#Last callback to create figures for Enterprise budgeting
@app.callback(Output(component_id="EBbox-container", component_property="children"),
                Output(component_id="EBcdf-container", component_property="children"),
                Output(component_id="EBtimeseries-container", component_property="children"),
                Output(component_id="EBtables-container", component_property="children"),
                Output("memory-EB-table", "data"),
                Input("EB-button-state", "n_clicks"),
                State('yield-multiplier', 'value'), #EJ(6/5/2021)
                State("scenario-table","data") ### scenario summary table
              )

def EB_figure(n_clicks, multiplier, sce_in_table): #EJ(6/5/2021) added multiplier
    if n_clicks is None:
        raise PreventUpdate
        return 
    else: 
        # 1) Read saved scenario summaries and get a list of scenarios to run
        dff = pd.DataFrame(sce_in_table)  #read dash_table.DataTable into pd df #J(5/3/2021)
        sce_numbers = len(dff.sce_name.values)
        # Wdir_path = "C:\\IRI\\Python_Dash\\ET_DSS_hist\\TEST\\"
        Wdir_path = DSSAT_FILES_DIR  #for linux system
        os.chdir(Wdir_path)  #change directory  #check if needed or not
        TG_GMargin = []

        #EJ(5/3/2021) Read DSSAT output for each scenarios
        for i in range(sce_numbers):
            sname = dff.sce_name.values[i]
            if dff.Crop[i] == "WH":
                fout_name = path.join(Wdir_path, "ETWH"+sname+".OSU")
            elif dff.Crop[i] == "MZ":
                fout_name = path.join(Wdir_path, "ETMZ"+sname+".OSU")
            else:  # SG
                fout_name = path.join(Wdir_path, "ETSG"+sname+".OSU")

            #4) read DSSAT output => Read Summary.out from all scenario output
            df_OUT=pd.read_csv(fout_name,delim_whitespace=True ,skiprows=3)
            HWAM = df_OUT.iloc[:,20].values  #read 21th column only
            HWAM = np.multiply(HWAM, float(multiplier)) #EJ(6/5/2021) added multiplier
            EXPERIMENT = df_OUT.iloc[:,7].values  #read 4th column only
            PDAT = df_OUT.iloc[:,13].values  #read 14th column only
            ADAT = df_OUT.iloc[:,15].values  #read 14th column only
            MDAT = df_OUT.iloc[:,16].values  #read 14th column only    
            YEAR = df_OUT.iloc[:,13].values//1000
            NICM = df_OUT.iloc[:,39].values  #read 40th column only,  #NICM   Tot N app kg/ha Inorganic N applied (kg [N]/ha)
            HWAM[HWAM < 0]=0 #==> if HWAM == -99, consider it as "0" yield (i.e., crop failure)
            #Compute gross margin
            GMargin=HWAM*float(dff.CropPrice[i])- float(dff.NFertCost[i])*NICM - float(dff.SeedCost[i]) - float(dff.OtherVariableCosts[i]) - float(dff.FixedCosts[i])
            # GMargin_data[0:len(HWAM),x]
            if int(dff.TargetYr[i]) <= int(dff.LastYear[i]):
                doy = repr(PDAT[0])[4:]
                target = dff.TargetYr[i] + doy
                yr_index = np.argwhere(PDAT == int(target))
                TG_GMargin_temp = GMargin[yr_index[0][0]]
            else: 
                TG_GMargin_temp = np.nan

            # # Make a new dataframe for plotting
            # df1 = pd.DataFrame({"EXPERIMENT":EXPERIMENT})
            # df2 = pd.DataFrame({"PDAT":PDAT})
            # df3 = pd.DataFrame({"ADAT":ADAT})
            # df4 = pd.DataFrame({"HWAM":HWAM})
            # df5 = pd.DataFrame({"YEAR":YEAR})
            # df6 = pd.DataFrame({"NICM":NICM})
            # df7 = pd.DataFrame({"GMargin":GMargin})
            # temp_df = pd.concat([df1.EXPERIMENT,df5.YEAR, df2.PDAT, df3.ADAT, df4.HWAM, df6.NICM, df7.GMargin], ignore_index=True, axis=1)

            data = {"EXPERIMENT":EXPERIMENT, "YEAR":YEAR, "PDAT": PDAT, "ADAT":ADAT, "HWAM":HWAM,"NICM":NICM, "GMargin":GMargin}  #EJ(6/5/2021) fixed
            temp_df = pd.DataFrame (data, columns = ["EXPERIMENT","YEAR", "PDAT","ADAT","HWAM","NICM","GMargin"])  #EJ(6/5/2021) fixed

            if i==0:
                df = temp_df.copy()
            else:
                df = df.append(temp_df, ignore_index=True)

            TG_GMargin.append(TG_GMargin_temp)

        # adding column name to the respective columns
        df.columns =["EXPERIMENT", "YEAR","PDAT", "ADAT","HWAM","NICM","GMargin"]
        x_val = np.unique(df.EXPERIMENT.values)
        fig = px.box(df, x="EXPERIMENT", y="GMargin", title="Gross Margin Boxplot")
        fig.add_scatter(x=x_val,y=TG_GMargin, mode="markers") #, mode="lines+markers") #"lines")
        fig.update_xaxes(title= "Scenario Name")
        fig.update_yaxes(title= "Gross Margin[Birr/ha]")

        fig2 = go.Figure()
        for i in x_val:
            x_data = df.GMargin[df["EXPERIMENT"]==i].values
            x_data = np.sort(x_data)
            fx_scf = [1.0/len(x_data)] * len(x_data) #pdf
            Fx_scf= 1.0-np.cumsum(fx_scf)  #for exceedance curve

            fig2.add_trace(go.Scatter(x=x_data, y=Fx_scf,
                        mode="lines+markers",
                        name=i))
        # Edit the layout
        fig2.update_layout(title="Gross Margin Exceedance Curve",
                        xaxis_title="Gross Margin[Birr/ha]",
                        yaxis_title="Probability of Exceedance [-]")

        #make a new dataframe to save into CSV
        yr_val = np.unique(df.YEAR.values)
        df_out = pd.DataFrame({"YEAR":yr_val})

        fig3 = go.Figure()
        for i in x_val:
            x_data = df.YEAR[df["EXPERIMENT"]==i].values
            y_data = df.GMargin[df["EXPERIMENT"]==i].values
            y_data = y_data.astype(int) #EJ(6/5/2021)

            ##make a new dataframe to save into CSV
            df_temp = pd.DataFrame({i:y_data})
            df_out = pd.concat([df_out, df_temp], axis=1)

            fig3.add_trace(go.Scatter(x=x_data, y=y_data,
                        mode="lines+markers",
                        name=i))
        # Edit the layout
        fig3.update_layout(title="Gross Margin Time-Series",
                        xaxis_title="Year",
                        yaxis_title="Gross Margin[Birr/ha]")
        #save simulated yield outputs into a csv file <<<<<<=======================
        fname = path.join(Wdir_path, "simulated_yield_GMargin.csv")
        df_out.to_csv(fname, index=False)
        return [
            dcc.Graph(id="EB-boxplot",figure=fig), 
            dcc.Graph(id="EB-exceedance",figure=fig2),
            dcc.Graph(id="EB-ts",figure=fig3),
            dash_table.DataTable(columns=[{"name": i, "id": i} for i in df_out.columns],
                data=df_out.to_dict("records"),
                style_cell={"whiteSpace": "normal","height": "auto",},),
            df_out.to_dict("records")
            ]

# =============================================
# def writeSNX_main_hist(Wdir_path,station,start_year,end_year,planting_date,cultivar,soil_type,initial_soil_moisture,initial_soil_no3_content,planting_density,scenario):
def writeSNX_main_hist(Wdir_path,station,start_year,end_year,planting_date,crop,cultivar,soil_type,initial_soil_moisture,initial_soil_no3_content,
                       planting_density,scenario,fert_app, df_fert):    
    WSTA = station
    NYERS = repr(int(end_year) - int(start_year) + 1)
    plt_year = start_year
    if planting_date is not None:
        date_object = date.fromisoformat(planting_date)
        date_string = date_object.strftime("%B %d, %Y")
        plt_doy = date_object.timetuple().tm_yday
    PDATE = plt_year[2:] + repr(plt_doy).zfill(3)
        #   IC_date = first_year * 1000 + (plt_doy - 1)
        #   PDATE = repr(first_year)[2:] + repr(plt_doy).zfill(3)
        # ICDAT = repr(IC_date)[2:]
    ICDAT = plt_year[2:] + repr(plt_doy-1).zfill(3)  #Initial condition => 1 day before planting
    SDATE = ICDAT
    INGENO = cultivar[0:6]  
    CNAME = cultivar[7:]  
    ID_SOIL = soil_type
    PPOP = planting_density  #planting density
    i_NO3 = initial_soil_no3_content  # self.label_04.cget("text")[0:1]  #self.NO3_soil.getvalue()[0][0:1] #"H" #or "L"
    IC_w_ratio = float(initial_soil_moisture)
    # crop = "MZ" #EJ(1/6/2021) temporary

    #1) make SNX
    if crop == "WH":
        temp_snx = path.join(Wdir_path, "TEMP_ETWH.SNX")
        snx_name = "ETWH"+scenario[:4]+".SNX"
    elif crop == "MZ":
        temp_snx = path.join(Wdir_path, "TEMP_ETMZ.SNX")
        snx_name = "ETMZ"+scenario[:4]+".SNX"
    else:  # SG
        temp_snx = path.join(Wdir_path, "TEMP_ETSG.SNX")
        snx_name = "ETSG"+scenario[:4]+".SNX"
    # # temp_snx = path.join(Wdir_path, "ETMZTEMP.SNX")
    # temp_snx = path.join(Wdir_path, "TEMP_ETMZ.SNX")
    # snx_name = "ETMZ"+scenario[:4]+".SNX"
    SNX_fname = path.join(Wdir_path, snx_name)
    fr = open(temp_snx, "r")  # opens temp SNX file to read
    fw = open(SNX_fname, "w")  # opens SNX file to write
    # read lines 1-9 from temp file
    for line in range(0, 14):
        temp_str = fr.readline()
        fw.write(temp_str)

    MI = "0" 
    if fert_app == "Fert":
        MF = "1"
    else: 
        MF = "0"
    # MF = "1"
    SA = "0"
    IC = "1"
    MP = "1"
    MR = "0"
    MC = "0"
    MT = "0"
    ME = "0"
    MH = "0"
    SM = "1"
    temp_str = fr.readline()
    FL = "1"
    fw.write("{0:3s}{1:31s}{2:3s}{3:3s}{4:3s}{5:3s}{6:3s}{7:3s}{8:3s}{9:3s}{10:3s}{11:3s}{12:3s}{13:3s}".format(
        FL.rjust(3), "1 0 0 ET-SIMAGRI                 1",
        FL.rjust(3), SA.rjust(3), IC.rjust(3), MP.rjust(3), MI.rjust(3), MF.rjust(3), MR.rjust(3), MC.rjust(3),
        MT.rjust(3), ME.rjust(3), MH.rjust(3), SM.rjust(3)))
    fw.write(" \n")

    # read lines from temp file
    for line in range(0, 3):
        temp_str = fr.readline()
        fw.write(temp_str)

    # write *CULTIVARS
    temp_str = fr.readline()
    new_str = temp_str[0:3] + crop + temp_str[5:6] + INGENO + temp_str[12:13] + CNAME
    fw.write(new_str)
    fw.write(" \n")

    # read lines from temp file
    for line in range(0, 3):
        temp_str = fr.readline()
        fw.write(temp_str)
    # ================write *FIELDS
    # Get soil info from *.SOL
    SOL_file = path.join(Wdir_path, "ET.SOL")
    # soil_depth, wp, fc, nlayer = get_soil_IC(SOL_file, ID_SOIL)
    soil_depth, wp, fc, nlayer, SLTX = get_soil_IC(SOL_file, ID_SOIL)
    SLDP = repr(soil_depth[-1])
    ID_FIELD = WSTA + "0001"
    WSTA_ID =  WSTA
    # This line must not be changed for Linux version - DSSAt seems to be sensitive to spacing
    fw.write(
        "{0:2s} {1:8s}{2:5s}{3:3s}{4:6s}{5:4s}  {6:10s}{7:4s}".format(FL.rjust(2), ID_FIELD, WSTA_ID.rjust(5),
                                                                        "       -99   -99   -99   -99   -99   -99 ",
                                                                        SLTX.ljust(6), SLDP.rjust(4), ID_SOIL,
                                                                        " -99"))
    fw.write(" \n")
    temp_str = fr.readline()  # 1 -99      CCER       -99   -99 DR000   -99   -99
    temp_str = fr.readline()  # @L ...........XCRD ...........YCRD .....ELEV
    fw.write(temp_str)
    temp_str = fr.readline()  # 1             -99             -99       -99   ==> skip
    # ================write *FIELDS - second section
    # This line must not be changed for Linux version - DSSAt seems to be sensitive to spacing
    fw.write("{0:2s} {1:89s}".format(FL.rjust(2),
                                    "            -99             -99       -99               -99   -99   -99   -99   -99   -99"))
    fw.write(" \n")
    fw.write(" \n")

    # read lines from temp file
    for line in range(0, 3):
        temp_str = fr.readline()
        fw.write(temp_str)

    # write *INITIAL CONDITIONS
    temp_str = fr.readline()
    new_str = temp_str[0:9] + ICDAT + temp_str[14:]
    fw.write(new_str)
    temp_str = fr.readline()  # @C  ICBL  SH2O  SNH4  SNO3
    fw.write(temp_str)
    temp_str = fr.readline()
    for nline in range(0, nlayer):
        if nline == 0:  # first layer
            temp_SH2O = IC_w_ratio * (fc[nline] - wp[nline]) + wp[nline]  # EJ(6/25/2015): initial AWC=70% of maximum AWC
            if i_NO3 == "H":
                SNO3 = "15"  # **EJ(4/29/2020) used one constant number regardless of soil types
            else:  # i_NO3 == "L":
                SNO3 = "5"  # **EJ(5/27/2015)
        elif nline == 1:  # second layer
            temp_SH2O = IC_w_ratio * (fc[nline] - wp[nline]) + wp[nline]  # EJ(6/25/2015): initial AWC=70% of maximum AWC
            if i_NO3 == "H":
                SNO3 = "2"  # **EJ(4/29/2020) used one constant number regardless of soil types
            else:  # elif i_NO3 == "L":
                SNO3 = ".5"  # **EJ(4/29/2020) used one constant number regardless of soil types
        else:
            temp_SH2O = fc[nline]  # float
            SNO3 = "0"  # **EJ(5/27/2015)
        SH2O = repr(temp_SH2O)[0:5]  # convert float to string
        new_str = temp_str[0:5] + repr(soil_depth[nline]).rjust(3) + " " + SH2O.rjust(5) + temp_str[14:22] + SNO3.rjust(4) + "\n"
        fw.write(new_str)
    fw.write("  \n")
    for nline in range(0, 10):
        temp_str = fr.readline()
        if temp_str[0:9] == "*PLANTING":
            break

    fw.write(temp_str)  # *PLANTING DETAILS
    temp_str = fr.readline()  # @P PDATE EDATE
    fw.write(temp_str)
    # write *PLANTING DETAILS
    temp_str = fr.readline()
    PPOE = PPOP #planting density 
    new_str = temp_str[0:3] + PDATE + "   -99" + PPOP.rjust(6) + PPOE.rjust(6) + temp_str[26:]
    fw.write(new_str)
    fw.write("  \n")
    # write *IRRIGATION AND WATER MANAGEMENT, if irrigation on reported dates
    # skip irrigation for now   #EJ(1/6/2021) temporary

    # write *FERTILIZERS (INORGANIC)
    #get fertilizer info using dash_table.DataTable(https://dash.plotly.com/datatable/callbacks
    #use editable datatable https://dash.plotly.com/datatable/editable
    for nline in range(0, 20):
        temp_str = fr.readline()
        if temp_str[0:12] == "*FERTILIZERS":
            break
    fw.write(temp_str)  # *FERTILIZERS (INORGANIC)
    temp_str = fr.readline()  # @F FDATE  FMCD  FACD 
    fw.write(temp_str)
    temp_str = fr.readline()  #1     0 FE005 AP001     5    30   -99   -99   -99   -99   -99   -99
#-0------------        # write *FERTILIZERS (INORGANIC)
    if fert_app == "Fert":
        df_fert = df_fert.astype(float)
        df_filtered = df_fert[(df_fert["DAP"] >= 0) & (df_fert["NAmount"] >= 0)]
        fert_count = len(df_filtered)  #Get the number of rows: len(df)  => May need more error-checking
        FDATE = df_filtered.DAP.values
        FMCD = "FE005"  #Urea
        FACD = "AP001"  #Broadcast, not incorporated    
        FDEP = "5"   #5cm depth
        FAMN = df_filtered.NAmount.values
        FAMP = "-99"
        FAMK = "-99"

        if fert_count > 0:   # fertilizer applied
            for i in range(fert_count):
                new_str = temp_str[0:5] + repr(int(FDATE[i])).rjust(3) + " " + FMCD.rjust(5) + " " + FACD.rjust(5) + " " + FDEP.rjust(5) + " " + repr(FAMN[i]).rjust(5) + " " + FAMP.rjust(5) + " " + FAMK.rjust(5) + temp_str[44:]
                fw.write(new_str)
            fw.write(" \n")
#-------------------------------------------
    # else: #if no fertilzier applied
    #     temp_str = fr.readline()  #  1     0 FE005 AP002 
    #     fw.write(temp_str)
    #     temp_str = fr.readline()  #  1    45 FE005 AP002
    #     fw.write(temp_str)

    fw.write("  \n")
    for nline in range(0, 20):
        temp_str = fr.readline()
        if temp_str[0:11] == "*SIMULATION":
            break
    fw.write(temp_str)  # *SIMULATION CONTROLS
    temp_str = fr.readline()
    fw.write(temp_str)  # @N GENERAL     NYERS NREPS START SDATE RSEED SNAME
    # write *SIMULATION CONTROLS
    temp_str = fr.readline()
    new_str = temp_str[0:18] + NYERS.rjust(2) + temp_str[20:33] + SDATE + temp_str[38:]
    fw.write(new_str)
    temp_str = fr.readline()  # @N OPTIONS
    fw.write(temp_str)
    temp_str = fr.readline()  # 1 OP
    fw.write(" 1 OP              Y     Y     Y     N     N     N     N     N     D"+ "\n")
    temp_str = fr.readline()  # @N METHODS
    fw.write(temp_str)
    temp_str = fr.readline()  # 1 ME
    fw.write(temp_str)
    temp_str = fr.readline()  # @N MANAGEMENT
    fw.write(temp_str)
    temp_str = fr.readline()  # 1 MA
    # new_str = temp_str[0:25] + IRRIG + temp_str[26:31] + FERTI + temp_str[32:]
    # fw.write(new_str)
    fw.write(temp_str)
    temp_str = fr.readline()  # @N OUTPUTS
    fw.write(temp_str)
    temp_str = fr.readline()  # 1 OU
    fw.write(temp_str)

    # read lines from temp file
    for line in range(0, 5):
        temp_str = fr.readline()
        fw.write(temp_str)
    # irrigation method
    temp_str = fr.readline()  # 1 IR
    fw.write(temp_str)

    # read lines from temp file
    for line in range(0, 7):
        temp_str = fr.readline()
        fw.write(temp_str)

    fr.close()
    fw.close()
    return
# ============================================
#===============================================================
def get_soil_IC(SOL_file, ID_SOIL):
    # SOL_file=Wdir_path.replace("/","\\") + "\\SN.SOL"
    # initialize
    depth_layer = []
    ll_layer = []
    ul_layer = []
    n_layer = 0
    soil_flag = 0
    count = 0
    fname = open(SOL_file, "r")  # opens *.SOL
    for line in fname:
        if ID_SOIL in line:
            soil_depth = line[33:38]#37]
            s_class = line[25:29]
            soil_flag = 1
        if soil_flag == 1:
            count = count + 1
            if count >= 7:
                depth_layer.append(int(line[0:6]))
                ll_layer.append(float(line[13:18]))
                ul_layer.append(float(line[19:24]))
                n_layer = n_layer + 1
                if line[3:6].strip() == soil_depth.strip():
                    fname.close()
                    break
    return depth_layer, ll_layer, ul_layer, n_layer, s_class
#===============================================================
#===============================================================
def season_rain_rank(WTD_df, sdoy, edoy): 
    #sdoy: starting doy of the target period
    #edoy: ending doy of the target period
    #===================================================
    sdoy = int(sdoy) #convert into integer just in case
    edoy = int(edoy)
    #3-1) Extract daily weather data for the target period
    # count how many years are recorded
    year_array = WTD_df.YEAR.unique()
    nyears = year_array.shape[0]

    #Make 2D array and aggregate during the specified season/months (10/15/2020)
    rain_array = np.reshape(WTD_df.RAIN.values, (nyears,365))
    if edoy > sdoy: #all months within the target season is within one year
        season_rain_sum = np.sum(rain_array[:,(sdoy-1):edoy], axis=1)
    else: #seasonal sum goes beyond the first year  #   if edoy < sdoy:
        a= rain_array[:-1,(sdoy-1):]
        b = rain_array[1:,0:edoy]
        rain_array2 = np.concatenate((a,b), axis = 1)
        # season_rain_sum = np.sum(rain_array[:-1,(sdoy-1):(sdoy+edoy)], axis=1)    
        season_rain_sum = np.sum(rain_array2, axis=1) #check !
        nyears = nyears - 1
    #================================================================
    # #save dataframe into a csv file [Note: Feb 29th was excluded]
    # df_season_rain = pd.DataFrame(np.zeros((nyears, 3)))   
    # df_season_rain.columns = ["YEAR","season_rain", "rank"]  #iyear => ith year
    # df_season_rain.name = "season_rain_sorted"+str(sdoy)
    # df_season_rain.YEAR.iloc[:]= year_array[0:nyears][np.argsort(season_rain_sum)]
    # df_season_rain.season_rain.iloc[:]= season_rain_sum[np.argsort(season_rain_sum)]
    # df_season_rain.sindex.iloc[:]= np.argsort(season_rain_sum)
    rain_rank = season_rain_sum.argsort().argsort()+1  #<<<<<<==================
    # rain_rank = rain_rank +1  #to start from 1, not 0
    data = {"YEAR":year_array[0:nyears], "season_rain": season_rain_sum, "Rank":rain_rank}
    df_season_rain = pd.DataFrame (data, columns = ["YEAR","season_rain", "Rank"])
    #write dataframe into CSV file for debugging
    df_season_rain.to_csv("C:\\IRI\\Python_Dash\\ET_DSS_hist\\TEST\\df_season_rain.csv", index=False)
    return df_season_rain
#===============================================================
#====================================================================
# === Read daily observations into a dataframe (note: Feb 29th was skipped in df_obs)
def read_WTD(fname,firstyear, lastyear):  
    #1) Read daily observations into a matrix (note: Feb 29th was skipped)
    # WTD_fname = r"C:\Users\Eunjin\IRI\Hybrid_WGEN\CNRA.WTD"
    #1) read observed weather *.WTD (skip 1st row - heading)
    data1 = np.loadtxt(fname,skiprows=1)
    #convert numpy array to dataframe
    WTD_df = pd.DataFrame({"YEAR":data1[:,0].astype(int)//1000,    #python 3.6: / --> //
                    "DOY":data1[:,0].astype(int)%1000,
                    "SRAD":data1[:,1],
                    "TMAX":data1[:,2],
                    "TMIN":data1[:,3],
                    "RAIN":data1[:,4]})

    #=== Extract only years with full 365/366 days:  by checking last obs year if it is incomplete or not
    WTD_last_year = WTD_df.YEAR.values[-1] 
    WTD_last_doy = WTD_df.DOY[WTD_df["YEAR"] == WTD_last_year].values[-1]
    if calendar.isleap(WTD_last_year):
        if WTD_last_doy < 366:
            indexNames = WTD_df[WTD_df["YEAR"] == WTD_last_year].index
            WTD_df.drop(indexNames , inplace=True) # Delete these row indexes from dataFrame
    else:
        if WTD_last_doy < 365:
            indexNames = WTD_df[WTD_df["YEAR"] == WTD_last_year].index
            WTD_df.drop(indexNames , inplace=True)    
    #=== Extract only years with full 365/366 days:  by checking first obs year if it is incomplete or not
    WTD_first_year = WTD_df.YEAR.values[0] 
    WTD_first_date = WTD_df.DOY[WTD_df["YEAR"] == WTD_first_year].values[0]
    if WTD_first_date > 1:
        if calendar.isleap(WTD_first_year):
            indexNames = WTD_df[WTD_df["YEAR"] == WTD_first_year].index
            WTD_df.drop(indexNames , inplace=True)
        else:
            indexNames = WTD_df[WTD_df["YEAR"] == WTD_first_year].index
            WTD_df.drop(indexNames , inplace=True) 
    #========================
    rain_WTD = WTD_df.RAIN.values
    srad_WTD = WTD_df.SRAD.values
    Tmax_WTD = WTD_df.TMAX.values
    Tmin_WTD = WTD_df.TMIN.values
    year_WTD = WTD_df.YEAR.values
    doy_WTD = WTD_df.DOY.values
    obs_yrs = np.unique(year_WTD).shape[0]
    #Exclude Feb. 29th in leapyears
    temp_indx = [1 if (calendar.isleap(year_WTD[i])) & (doy_WTD[i] == 29) else 0 for i in range(len(year_WTD))] #[f(x) if condition else g(x) for x in sequence]
    # Get the index of elements with value 15  result = np.where(arr == 15)
    rain_array = rain_WTD[np.where(np.asarray(temp_indx) == 0)]
    rain_array = np.reshape(rain_array, (obs_yrs,365))
    srad_array = srad_WTD[np.where(np.asarray(temp_indx) == 0)]
    srad_array = np.reshape(srad_array, (obs_yrs,365))
    Tmax_array = Tmax_WTD[np.where(np.asarray(temp_indx) == 0)]
    Tmax_array = np.reshape(Tmax_array, (obs_yrs,365))
    Tmin_array = Tmin_WTD[np.where(np.asarray(temp_indx) == 0)]
    Tmin_array = np.reshape(Tmin_array, (obs_yrs,365))

    #save dataframe into a csv file [Note: Feb 29th was excluded]
    df_obs = pd.DataFrame(np.zeros((obs_yrs*365, 6)))   
    df_obs.columns = ["YEAR","DOY","SRAD","TMAX","TMIN","RAIN"]  #iyear => ith year
    df_obs.name = "WTD_observed_365"
    k = 0
    for i in range(obs_yrs):
        iyear = np.unique(year_WTD)[i]
        df_obs.YEAR.iloc[k:365*(i+1)] = np.tile(iyear,(365,))
        df_obs.DOY.iloc[k:365*(i+1)]= np.asarray(range(1,366))
        df_obs.SRAD.iloc[k:365*(i+1)]= np.transpose(srad_array[i,:])
        df_obs.TMAX.iloc[k:365*(i+1)]= np.transpose(Tmax_array[i,:])
        df_obs.TMIN.iloc[k:365*(i+1)]= np.transpose(Tmin_array[i,:])
        df_obs.RAIN.iloc[k:365*(i+1)]= np.transpose(rain_array[i,:])
        k=k+365
     
    #EJ(5/18/2021) Filter df by condition (from firstyear to lastyear)
    df_obs_filter = df_obs.loc[(df_obs["YEAR"] >= firstyear) & (df_obs["YEAR"] <= lastyear)] 

    ## df_obs.to_csv(wdir +"//"+ df_obs.name + ".csv", index=False)
    del rain_WTD; del srad_WTD; del Tmax_WTD; del Tmin_WTD; del year_WTD; del doy_WTD
    del rain_array; del srad_array; del Tmax_array; del Tmin_array
    # return WTD_df_orig, df_obs
    return df_obs_filter
#====================================================================
# End of reading observations (WTD file) into a matrix 
#====================================================================
#===============================================================
# if __name__ == "__main__":
#     # app.run_server(debug=True)
#     app.run_server(debug=False)  #https://github.com/plotly/dash/issues/108

#===>for linux system
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run_server(debug=False,
                   host="0.0.0.0",
                   port=port)
#===>end of for linux system
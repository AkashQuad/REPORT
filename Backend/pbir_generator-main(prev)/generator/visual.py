# # visual_generator.py

# """
# Full visual generation module
# - Tableau JSON -> Power BI visual mapping
# - Safe fallbacks
# - Correct bindings per visual
# """

# # ------------------ Tableau -> Power BI Visual Mapping ------------------

# TABLEAU_TO_POWERBI_VISUALS = {
#     # BAR / COLUMN
#     "bar chart": "clusteredBarChart",
#     "bar": "clusteredBarChart",
#     "stacked bar": "stackedBarChart",

#     "column chart": "clusteredColumnChart",
#     "column": "clusteredColumnChart",
#     "stacked column": "stackedColumnChart",

#     # LINE / AREA
#     "line chart": "lineChart",
#     "line": "lineChart",

#     "area chart": "areaChart",
#     "area": "areaChart",
#     "stacked area": "stackedAreaChart",

#     # PIE / DONUT
#     "pie chart": "pieChart",
#     "pie": "pieChart",
#     "donut chart": "donutChart",
#     "donut": "donutChart",

#     # TABLE / MATRIX
#     "table": "tableEx",
#     "text table": "tableEx",
#     "crosstab": "matrix",

#     # KPI / CARD
#     "kpi": "kpi",
#     "card": "card",

#     # MAP
#     "map": "map",
#     "filled map": "filledMap",

#     # SCATTER
#     "scatter plot": "scatterChart",
#     "scatter": "scatterChart",

#     # OTHER
#     "treemap": "treemap",
#     "waterfall": "waterfallChart",
#     "funnel": "funnel"
# }


# # ------------------ Visual Generator ------------------

# def generate_visual(ws: dict, table_name: str, x: int, y: int) -> dict:
#     """
#     Generate a Power BI visual definition from Tableau worksheet JSON
#     """

#     # Normalize visual type
#     tableau_type = (
#         ws.get("visualType")
#         or ws.get("type")
#         or ws.get("chartType")
#         or ws.get("vizType")
#         or "table"
#     ).strip().lower()

#     visual_type = TABLEAU_TO_POWERBI_VISUALS.get(tableau_type, "tableEx")

#     columns = ws.get("columns", []) or []

#     width = 500
#     height = 300

#     # ------------------ Bindings ------------------

#     if visual_type == "tableEx":
#         bindings = {
#             "Values": [
#                 {"table": col.get("table", table_name), "column": col.get("column")}
#                 for col in columns
#             ]
#         }
#         height = 350

#     elif visual_type in (
#         "clusteredBarChart",
#         "clusteredColumnChart",
#         "stackedBarChart",
#         "stackedColumnChart",
#         "lineChart",
#         "areaChart",
#         "stackedAreaChart"
#     ):
#         bindings = {
#             "Category": {
#                 "table": columns[1].get("table", table_name),
#                 "column": columns[1].get("column")
#             } if len(columns) > 1 else {"table": table_name, "column": "Category"},
#             "Values": {
#                 "table": columns[0].get("table", table_name),
#                 "column": columns[0].get("column")
#             } if columns else {"table": table_name, "column": "Value"}
#         }

#     elif visual_type in ("pieChart", "donutChart"):
#         bindings = {
#             "Legend": {
#                 "table": columns[1].get("table", table_name),
#                 "column": columns[1].get("column")
#             } if len(columns) > 1 else {"table": table_name, "column": "Legend"},
#             "Values": {
#                 "table": columns[0].get("table", table_name),
#                 "column": columns[0].get("column")
#             } if columns else {"table": table_name, "column": "Value"}
#         }

#     elif visual_type == "matrix":
#         bindings = {
#             "Rows": {
#                 "table": columns[1].get("table", table_name),
#                 "column": columns[1].get("column")
#             } if len(columns) > 1 else {"table": table_name, "column": "Row"},
#             "Values": {
#                 "table": columns[0].get("table", table_name),
#                 "column": columns[0].get("column")
#             } if columns else {"table": table_name, "column": "Value"}
#         }

#     else:
#         # Final safety fallback
#         visual_type = "tableEx"
#         bindings = {
#             "Values": [
#                 {"table": col.get("table", table_name), "column": col.get("column")}
#                 for col in columns
#             ]
#         }

#     # ------------------ Return Visual ------------------

#     return {
#         "visualType": visual_type,
#         "title": ws.get("name", "Auto Visual"),
#         "layout": {
#             "x": x,
#             "y": y,
#             "width": width,
#             "height": height
#         },
#         "bindings": bindings
#     }


#----------------------------------added excel


# visual_generator.py

import pandas as pd
import requests
from io import BytesIO

"""
Full visual generation module
- Fetches Tableau -> Power BI visual mapping from public Google Sheet
- Caches mapping for performance
- Supports ALL Power BI visual types and their specific data binding rules
"""

# ✅ Your exact Google Sheet File ID
GOOGLE_DRIVE_FILE_ID = "1wDJUMRudC_qZnK69jhxmIuq72JZE8IJvA9LNyA9BRYw" 

_MAPPING_CACHE = {}

def get_mapping_dictionary() -> dict:
    """
    Downloads the Google Sheet, converts it to a dictionary, and caches it.
    """
    global _MAPPING_CACHE
    
    if _MAPPING_CACHE:
        return _MAPPING_CACHE

    try:
        # ✅ Correct URL format for exporting a Google Sheet as an Excel file
        download_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_FILE_ID}/export?format=xlsx"
        
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Read the downloaded bytes into pandas
        df = pd.read_excel(BytesIO(response.content))
        df.columns = df.columns.str.strip()
        
        # Create mapping dictionary mapping Tableau Type -> Power BI Type
        mapping_dict = dict(zip(
            df['Tableau Type'].astype(str).str.strip().str.lower(), 
            df['Power BI Type'].astype(str).str.strip()
        ))
        
        _MAPPING_CACHE = mapping_dict
        print("✅ Visual mapping successfully loaded from Google Sheets!")
        return _MAPPING_CACHE
        
    except Exception as e:
        print(f"❌ Failed to load mapping from Google Sheets: {e}")
        # Core fallback dictionary in case the network fails
        return {
            "table": "table",
            "bar chart": "clusteredBarChart",
            "column chart": "clusteredColumnChart",
            "line chart": "lineChart",
            "pie chart": "pieChart"
        }

# ------------------ Visual Generator ------------------

def generate_visual(ws: dict, table_name: str, x: int, y: int) -> dict:
    """
    Generate a Power BI visual definition from Tableau worksheet JSON
    """
    visual_map = get_mapping_dictionary()

    tableau_type = (
        ws.get("visualType")
        or ws.get("type")
        or ws.get("chartType")
        or ws.get("vizType")
        or "table"
    ).strip().lower()

    # Lookup mapped type, fallback to table if not found
    visual_type = visual_map.get(tableau_type, "table")

    columns = ws.get("columns", []) or []

    width = 500
    height = 300
    bindings = {}

    # ------------------ Dynamic Bindings Logic ------------------

    # 1. Standard Table (List of values)
    if visual_type == "table":
        bindings = {
            "Values": [
                {"table": col.get("table", table_name), "column": col.get("column")}
                for col in columns
            ]
        }
        height = 350

    # 2. Matrix (Rows and Values)
    elif visual_type == "matrix":
        bindings = {
            "Rows": {
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Row"},
            "Values": {
                "table": columns[1].get("table", table_name), "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    # 3. Standard Charts (Category on Axis, Values on Y)
    elif visual_type in (
        "clusteredBarChart", "stackedBarChart", "100StackedBarChart",
        "clusteredColumnChart", "stackedColumnChart", "100StackedColumnChart",
        "lineChart", "areaChart", "stackedAreaChart", 
        "waterfallChart", "funnel", "treemap"
    ):
        bindings = {
            "Category": {
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Category"},
            "Values": {
                "table": columns[1].get("table", table_name), "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    # 4. Circular Charts (Legend and Values)
    elif visual_type in ("pieChart", "donutChart"):
        bindings = {
            "Legend": {
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Legend"},
            "Values": {
                "table": columns[1].get("table", table_name), "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    # 5. Scatter Charts (Category, X Axis, Y Axis)
    elif visual_type == "scatterChart":
        bindings = {
            "X": {
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "X"},
            "Y": {
                "table": columns[1].get("table", table_name), "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Y"}
        }
        # If there's a 3rd column, use it as the Category/Detail
        if len(columns) > 2:
            bindings["Category"] = {
                "table": columns[2].get("table", table_name), "column": columns[2].get("column")
            }

    # 6. Single Value Visuals (Card, KPI, Gauge)
    elif visual_type in ("card", "kpi", "gauge"):
        bindings = {
            "Values": {
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Value"}
        }
        height = 150
        width = 250

    # 7. Maps (Category/Location and Values)
    elif visual_type in ("map", "filledMap"):
        bindings = {
            "Category": {  
                "table": columns[0].get("table", table_name), "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Location"},
            "Values": {
                "table": columns[1].get("table", table_name), "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    # Fallback Catch-all
    else:
        visual_type = "table"
        bindings = {
            "Values": [
                {"table": col.get("table", table_name), "column": col.get("column")}
                for col in columns
            ]
        }

    # ------------------ Return Visual ------------------

    return {
        "visualType": visual_type,
        "title": ws.get("name", "Auto Visual"),
        "layout": {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        },
        "bindings": bindings
    }

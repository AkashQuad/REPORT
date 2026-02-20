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
- Fetches Tableau -> Power BI visual mapping from public Google Drive Excel
- Caches mapping for performance
- Safe fallbacks & Correct bindings
"""

# Replace this with your actual Google Drive File ID
GOOGLE_DRIVE_FILE_ID = "YOUR_FILE_ID_HERE" 

# Memory cache so we don't download the Excel file on every single API call
_MAPPING_CACHE = {}

def get_mapping_dictionary() -> dict:
    """
    Downloads the Excel file from Google Drive and converts it to a dictionary.
    Caches the result after the first successful download.
    """
    global _MAPPING_CACHE
    
    # Return from cache if we already downloaded it
    if _MAPPING_CACHE:
        return _MAPPING_CACHE

    try:
        # Construct the direct download URL for Google Drive
        download_url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}&export=download"
        
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(BytesIO(response.content))
        
        # Clean column names to ensure no leading/trailing spaces mess up the dictionary
        df.columns = df.columns.str.strip()
        
        # Create a dictionary: {'tableau type': 'power bi type'}
        # We lowercase the Tableau Type to make lookups case-insensitive
        mapping_dict = dict(zip(
            df['Tableau Type'].astype(str).str.strip().str.lower(), 
            df['Power BI Type'].astype(str).str.strip()
        ))
        
        _MAPPING_CACHE = mapping_dict
        print("✅ Visual mapping successfully loaded from Google Drive!")
        return _MAPPING_CACHE
        
    except Exception as e:
        print(f"❌ Failed to load Excel mapping from Drive: {e}")
        # Return a safe fallback dictionary if the download fails
        return {
            "table": "table",
            "text table": "table",
            "bar chart": "barChart",
            "pie chart": "pieChart"
        }

# ------------------ Visual Generator ------------------

def generate_visual(ws: dict, table_name: str, x: int, y: int) -> dict:
    """
    Generate a Power BI visual definition from Tableau worksheet JSON
    """
    # 1. Get the dynamic mapping
    visual_map = get_mapping_dictionary()

    # 2. Normalize incoming visual type
    tableau_type = (
        ws.get("visualType")
        or ws.get("type")
        or ws.get("chartType")
        or ws.get("vizType")
        or "table"
    ).strip().lower()

    # 3. Lookup in our Excel-generated dictionary (fallback to "table")
    visual_type = visual_map.get(tableau_type, "table")

    columns = ws.get("columns", []) or []

    width = 500
    height = 300

    # ------------------ Bindings ------------------

    if visual_type == "table":
        bindings = {
            "Values": [
                {"table": col.get("table", table_name), "column": col.get("column")}
                for col in columns
            ]
        }
        height = 350

    elif visual_type in (
        "barChart",
        "columnChart",
        "stackedBarChart",
        "stackedColumnChart",
        "lineChart",
        "areaChart",
        "stackedAreaChart"
    ):
        bindings = {
            "Category": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Category"},
            
            "Values": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    elif visual_type in ("pieChart", "donutChart"):
        bindings = {
            "Legend": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Legend"},
            
            "Values": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    elif visual_type == "matrix":
        bindings = {
            "Rows": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if len(columns) > 0 else {"table": table_name, "column": "Row"},
            
            "Values": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Value"}
        }

    else:
        # Final safety fallback
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

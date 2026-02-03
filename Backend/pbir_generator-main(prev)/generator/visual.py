# visual_generator.py

"""
Full visual generation module
- Tableau JSON -> Power BI visual mapping
- Safe fallbacks
- Correct bindings per visual
"""

# ------------------ Tableau -> Power BI Visual Mapping ------------------

TABLEAU_TO_POWERBI_VISUALS = {
    # BAR / COLUMN
    "bar chart": "clusteredBarChart",
    "bar": "clusteredBarChart",
    "stacked bar": "stackedBarChart",

    "column chart": "clusteredColumnChart",
    "column": "clusteredColumnChart",
    "stacked column": "stackedColumnChart",

    # LINE / AREA
    "line chart": "lineChart",
    "line": "lineChart",

    "area chart": "areaChart",
    "area": "areaChart",
    "stacked area": "stackedAreaChart",

    # PIE / DONUT
    "pie chart": "pieChart",
    "pie": "pieChart",
    "donut chart": "donutChart",
    "donut": "donutChart",

    # TABLE / MATRIX
    "table": "tableEx",
    "text table": "tableEx",
    "crosstab": "matrix",

    # KPI / CARD
    "kpi": "kpi",
    "card": "card",

    # MAP
    "map": "map",
    "filled map": "filledMap",

    # SCATTER
    "scatter plot": "scatterChart",
    "scatter": "scatterChart",

    # OTHER
    "treemap": "treemap",
    "waterfall": "waterfallChart",
    "funnel": "funnel"
}


# ------------------ Visual Generator ------------------

def generate_visual(ws: dict, table_name: str, x: int, y: int) -> dict:
    """
    Generate a Power BI visual definition from Tableau worksheet JSON
    """

    # Normalize visual type
    tableau_type = (
        ws.get("visualType")
        or ws.get("type")
        or ws.get("chartType")
        or ws.get("vizType")
        or "table"
    ).strip().lower()

    visual_type = TABLEAU_TO_POWERBI_VISUALS.get(tableau_type, "tableEx")

    columns = ws.get("columns", []) or []

    width = 500
    height = 300

    # ------------------ Bindings ------------------

    if visual_type == "tableEx":
        bindings = {
            "Values": [
                {"table": col.get("table", table_name), "column": col.get("column")}
                for col in columns
            ]
        }
        height = 350

    elif visual_type in (
        "clusteredBarChart",
        "clusteredColumnChart",
        "stackedBarChart",
        "stackedColumnChart",
        "lineChart",
        "areaChart",
        "stackedAreaChart"
    ):
        bindings = {
            "Category": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Category"},
            "Values": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if columns else {"table": table_name, "column": "Value"}
        }

    elif visual_type in ("pieChart", "donutChart"):
        bindings = {
            "Legend": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Legend"},
            "Values": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if columns else {"table": table_name, "column": "Value"}
        }

    elif visual_type == "matrix":
        bindings = {
            "Rows": {
                "table": columns[1].get("table", table_name),
                "column": columns[1].get("column")
            } if len(columns) > 1 else {"table": table_name, "column": "Row"},
            "Values": {
                "table": columns[0].get("table", table_name),
                "column": columns[0].get("column")
            } if columns else {"table": table_name, "column": "Value"}
        }

    else:
        # Final safety fallback
        visual_type = "tableEx"
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

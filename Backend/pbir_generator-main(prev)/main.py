# import os
# import json
# from dotenv import load_dotenv

# from blob_reader import load_metadata
# from generator.dataset import generate_dataset_model
# from generator.visual import generate_visual
# from generator.layout import next_position
# from generator.report import generate_definition, generate_item_config

# # --------------------------------------------------
# # ENV & PATHS
# # --------------------------------------------------
# load_dotenv()

# BASE_REPORT_DIR = "output/MyReport.Report"
# VISUAL_DIR = f"{BASE_REPORT_DIR}/static/visuals"
# DATASET_DIR = f"{BASE_REPORT_DIR}/dataset"
# OUTPUT_DIR = "output"

# os.makedirs(VISUAL_DIR, exist_ok=True)
# os.makedirs(DATASET_DIR, exist_ok=True)
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# # --------------------------------------------------
# # 1️⃣ LOAD METADATA FROM BLOB
# # --------------------------------------------------
# metadata = load_metadata()

# print("✅ Metadata keys:", metadata.keys())

# if "worksheets" not in metadata:
#     raise Exception("❌ metadata.json missing 'worksheets' key")

# worksheets = metadata["worksheets"]

# if not worksheets or not isinstance(worksheets, list):
#     raise Exception("❌ metadata.json has empty or invalid worksheets array")

# # --------------------------------------------------
# # 2️⃣ WRITE REPORT ROOT FILES (ONCE)
# # --------------------------------------------------
# with open(f"{BASE_REPORT_DIR}/definition.pbir", "w", encoding="utf-8") as f:
#     json.dump(generate_definition(), f, indent=2)

# report_name = metadata.get("workbookName", "Auto Generated Report")

# with open(f"{BASE_REPORT_DIR}/item.config.json", "w", encoding="utf-8") as f:
#     json.dump(generate_item_config(report_name), f, indent=2)

# print("✅ Report root files written")

# # --------------------------------------------------
# # 3️⃣ GENERATE DATASET MODEL (SCHEMA ONLY)
# # --------------------------------------------------
# dataset_model = generate_dataset_model(metadata)

# with open(f"{DATASET_DIR}/model.json", "w", encoding="utf-8") as f:
#     json.dump(dataset_model, f, indent=2)

# print("✅ Dataset model written")

# # --------------------------------------------------
# # 4️⃣ GENERATE PBIR VISUAL FILES (OPTIONAL)
# # --------------------------------------------------
# for i, ws in enumerate(worksheets):
#     pos = next_position(i)

#     visual_json = generate_visual(ws, pos["x"], pos["y"])

#     with open(f"{VISUAL_DIR}/visual{i+1}.json", "w", encoding="utf-8") as f:
#         json.dump(visual_json, f, indent=2)

# print(f"✅ {len(worksheets)} PBIR visual file(s) generated")

# # --------------------------------------------------
# # 5️⃣ 🔥 GENERATE runtime_visuals.json (CRITICAL)
# # --------------------------------------------------
# runtime_visuals = {
#     "dataset": {
#         "table": "MainTable"
#     },
#     "visuals": []
# }

# x, y = 40, 40

# for ws in worksheets:
#     print("➡️ Processing worksheet:", ws)

#     name = ws.get("name")
#     columns = ws.get("columns")

#     if not name:
#         print("⚠️ Worksheet missing name, skipping")
#         continue

#     if not columns or not isinstance(columns, list):
#         print(f"⚠️ Worksheet '{name}' has no columns, skipping")
#         continue

#     runtime_visuals["visuals"].append({
#         "type": "table",          # default visual
#         "title": name,
#         "x": x,
#         "y": y,
#         "width": 600,
#         "height": 300,
#         "values": columns
#     })

#     y += 340  # stack visuals vertically

# # FINAL VALIDATION
# if not runtime_visuals["visuals"]:
#     raise Exception("❌ No visuals generated — runtime_visuals.json would be empty")

# with open("output/runtime_visuals.json", "w", encoding="utf-8") as f:
#     json.dump(runtime_visuals, f, indent=2)

# print(f"✅ runtime_visuals.json generated with {len(runtime_visuals['visuals'])} visual(s)")

# print("🎉 PBIR generation completed successfully")


# import os
# import json
# from dotenv import load_dotenv
# from blob_reader import load_metadata, extract_worksheets
# from generator.dataset import generate_dataset_model
# from generator.visual import generate_visual
# from generator.layout import next_position
# from generator.report import generate_definition, generate_item_config

# # -------------------- ENV --------------------
# load_dotenv()

# # -------------------- PATHS --------------------
# BASE_REPORT_DIR = "output/MyReport.Report"
# VISUAL_DIR = f"{BASE_REPORT_DIR}/static/visuals"
# DATASET_DIR = f"{BASE_REPORT_DIR}/dataset"
# OUTPUT_DIR = "output"

# os.makedirs(VISUAL_DIR, exist_ok=True)
# os.makedirs(DATASET_DIR, exist_ok=True)
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# # -------------------- 1️⃣ LOAD METADATA --------------------
# metadata = load_metadata()
# worksheets = extract_worksheets(metadata)
# if not worksheets:
#     raise Exception("No worksheets found in metadata!")

# # -------------------- 2️⃣ GENERATE DATASET MODEL --------------------
# dataset_model = generate_dataset_model(metadata)
# table_name = dataset_model["tables"][0]["name"] if dataset_model["tables"] else "MainTable"

# with open(f"{DATASET_DIR}/model.json", "w", encoding="utf-8") as f:
#     json.dump(dataset_model, f, indent=2)

# # -------------------- 3️⃣ GENERATE REPORT ROOT FILES --------------------
# report_definition = generate_definition()
# report_name = metadata.get("workbookName", "Auto Generated Report")
# item_config = generate_item_config(report_name)

# # -------------------- 4️⃣ CREATE PAGES AND VISUALS --------------------
# pages = []
# runtime_visuals = {"dataset": {"table": table_name}, "visuals": []}

# for i, ws in enumerate(worksheets):
#     # Position for visual
#     pos = next_position(i)

#     # Generate visual with correct table binding
#     visual_json = generate_visual(ws, table_name, pos["x"], pos["y"])

#     # Save visual file
#     with open(f"{VISUAL_DIR}/visual{i+1}.json", "w", encoding="utf-8") as f:
#         json.dump(visual_json, f, indent=2)

#     # Append to runtime visuals
#     runtime_visuals["visuals"].append(visual_json)

#     # Each worksheet becomes a page
#     page = {
#         "name": ws.get("name", f"Page {i+1}"),
#         "visuals": [visual_json]
#     }
#     pages.append(page)

# # Assign pages to report definition
# report_definition["pages"] = pages

# # -------------------- 5️⃣ SAVE REPORT ROOT FILES --------------------
# with open(f"{BASE_REPORT_DIR}/definition.pbir", "w", encoding="utf-8") as f:
#     json.dump(report_definition, f, indent=2)

# with open(f"{BASE_REPORT_DIR}/item.config.json", "w", encoding="utf-8") as f:
#     json.dump(item_config, f, indent=2)

# # -------------------- 6️⃣ SAVE RUNTIME VISUALS --------------------
# with open("output/runtime_visuals.json", "w", encoding="utf-8") as f:
#     json.dump(runtime_visuals, f, indent=2)

# print(f"✅ PBIR project generated successfully with {len(worksheets)} page(s) and visuals.")

import os
import json
from dotenv import load_dotenv
from blob_reader import load_metadata, extract_worksheets
from generator.dataset import generate_dataset_model
from generator.visual import generate_visual
from generator.layout import next_position
from generator.report import generate_definition, generate_item_config

# -------------------- ENV --------------------
load_dotenv()

# -------------------- PATHS --------------------
BASE_REPORT_DIR = "output/MyReport.Report"
VISUAL_DIR = f"{BASE_REPORT_DIR}/static/visuals"
DATASET_DIR = f"{BASE_REPORT_DIR}/dataset"
OUTPUT_DIR = "output"

os.makedirs(VISUAL_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- 1️⃣ LOAD METADATA --------------------
metadata = load_metadata()
worksheets = extract_worksheets(metadata)
if not worksheets:
    raise Exception("No worksheets found in metadata!")

# -------------------- 2️⃣ GENERATE DATASET MODEL --------------------
# This now includes the 'relationships' array generated from your metadata
dataset_model = generate_dataset_model(metadata)

# Save the dataset model (model.json)
with open(f"{DATASET_DIR}/model.json", "w", encoding="utf-8") as f:
    json.dump(dataset_model, f, indent=2)

# -------------------- 3️⃣ GENERATE REPORT ROOT FILES --------------------
report_definition = generate_definition()
report_name = metadata.get("workbookName", "Auto Generated Report")
item_config = generate_item_config(report_name)

# -------------------- 4️⃣ CREATE PAGES AND VISUALS --------------------
pages = []
runtime_visuals = {"visuals": []}

for i, ws in enumerate(worksheets):
    # ✅ DYNAMIC TABLE SELECTION:
    # Instead of defaulting to 'MainTable', we extract the specific table
    # name associated with this worksheet from the metadata.
    current_table_name = ws.get("tableName") or ws.get("table")
    
    # Fallback logic: check the first column's table if worksheet table is missing
    if not current_table_name and ws.get("columns"):
        current_table_name = ws["columns"][0].get("table")
    
    # Absolute fallback if metadata is sparse
    if not current_table_name:
        current_table_name = "fact_sales"

    # Position for visual
    pos = next_position(i)

    # ✅ Generate visual with the SPECIFIC table binding
    visual_json = generate_visual(ws, current_table_name, pos["x"], pos["y"])

    # Save individual visual files
    visual_filename = f"visual{i+1}.json"
    with open(f"{VISUAL_DIR}/{visual_filename}", "w", encoding="utf-8") as f:
        json.dump(visual_json, f, indent=2)

    # Append to runtime tracking
    runtime_visuals["visuals"].append({
        "pageName": ws.get("name"),
        "table": current_table_name,
        "file": visual_filename
    })

    # Create the page structure
    page = {
        "name": ws.get("name", f"Page {i+1}"),
        "visuals": [visual_json]
    }
    pages.append(page)

# Assign pages to the report definition
report_definition["pages"] = pages

# -------------------- 5️⃣ SAVE REPORT ROOT FILES --------------------
# .pbir file links the report to the dataset folder
with open(f"{BASE_REPORT_DIR}/definition.pbir", "w", encoding="utf-8") as f:
    json.dump(report_definition, f, indent=2)

with open(f"{BASE_REPORT_DIR}/item.config.json", "w", encoding="utf-8") as f:
    json.dump(item_config, f, indent=2)

# -------------------- 6️⃣ SAVE RUNTIME SUMMARY --------------------
with open("output/runtime_visuals.json", "w", encoding="utf-8") as f:
    json.dump(runtime_visuals, f, indent=2)

print(f"✅ PBIR project generated successfully.")
print(f"✅ Tables mapped: {list(set(v['table'] for v in runtime_visuals['visuals']))}")

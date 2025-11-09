import streamlit as st
import json
import datetime
from copy import deepcopy

st.set_page_config(page_title="🌿 My Garden Log", layout="wide")

# --- Initialization ---
if "garden_data" not in st.session_state:
    st.session_state.garden_data = {
        "inventory": {"vegetables": [], "fruits": []},
        "logs": [],
        "layout": {}
    }

# --- File Upload ---
st.sidebar.header("📁 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload Garden JSON", type="json")

if uploaded_file:
    st.session_state.garden_data = json.load(uploaded_file)
    st.sidebar.success("Garden data loaded successfully!")

# --- Page Selection ---
page = st.sidebar.radio(
    "Navigate",
    ["Inventory", "Daily Logs", "Reports", "Garden Layout"]
)

# =======================================================
# 🥬 INVENTORY PAGE
# =======================================================
if page == "Inventory":
    st.header("🌱 Garden Inventory")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add Vegetable / Fruit")
        item_type = st.selectbox("Type", ["Vegetable", "Fruit"])
        item_name = st.text_input("Name of the plant")
        if st.button("Add to Inventory"):
            if item_name:
                st.session_state.garden_data["inventory"][item_type.lower() + "s"].append(item_name)
                st.success(f"Added {item_name} to {item_type.lower()} inventory")

    with col2:
        st.subheader("Current Inventory")
        st.json(st.session_state.garden_data["inventory"])

# =======================================================
# ✍️ DAILY LOG PAGE
# =======================================================
elif page == "Daily Logs":
    st.header("📝 Daily Log Entry")

    sections = list(st.session_state.garden_data.get("layout", {}).keys()) or [
        "Indoor", "Backyard", "Front Garden", "Raised Beds"
    ]
    plants = st.session_state.garden_data["inventory"]["vegetables"] + st.session_state.garden_data["inventory"]["fruits"]

    with st.form("log_form"):
        date = st.date_input("Date", datetime.date.today())
        section = st.selectbox("Section", sections)
        plant = st.selectbox("Plant", plants)
        action = st.selectbox("Action", ["Sown", "Transplanted", "Watered", "Fertilized", "Measured", "Harvested"])
        default_key = f"{plant}-Set-{date}"
        batch_key = st.text_input("Batch Key", default_key)
        height = st.number_input("Height (cm)", min_value=0.0, step=0.1)
        moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, step=1.0)
        notes = st.text_area("Notes")
        next_visit = st.date_input("Next Visit / Reminder", date + datetime.timedelta(days=3))
        submitted = st.form_submit_button("Add Log Entry")

        if submitted:
            log_entry = {
                "date": str(date),
                "section": section,
                "plant": plant,
                "batch_key": batch_key,
                "action": action,
                "metrics": {"height_cm": height, "moisture_%": moisture},
                "notes": notes,
                "next_visit": str(next_visit)
            }
            st.session_state.garden_data["logs"].append(log_entry)
            st.success("✅ Log entry added!")

    # --- View / Edit Logs ---
    st.subheader("📖 All Logs")

    if st.session_state.garden_data["logs"]:
        for i, log in enumerate(reversed(st.session_state.garden_data["logs"])):
            idx = len(st.session_state.garden_data["logs"]) - 1 - i
            with st.expander(f"{log['date']} | {log['plant']} | {log['batch_key']} | {log['action']}"):
                edited_log = deepcopy(log)

                st.markdown("### ✏️ Edit Log Entry")

                colA, colB = st.columns(2)
                with colA:
                    edited_log["date"] = str(st.date_input("Date", datetime.date.fromisoformat(log["date"]), key=f"date_{i}"))
                    edited_log["section"] = st.text_input("Section", log["section"], key=f"sec_{i}")
                    edited_log["plant"] = st.text_input("Plant", log["plant"], key=f"plant_{i}")
                    edited_log["batch_key"] = st.text_input("Batch Key", log["batch_key"], key=f"key_{i}")
                    edited_log["action"] = st.text_input("Action", log["action"], key=f"act_{i}")
                with colB:
                    edited_log["metrics"]["height_cm"] = st.number_input(
                        "Height (cm)", min_value=0.0, step=0.1, value=log["metrics"].get("height_cm", 0.0), key=f"h_{i}"
                    )
                    edited_log["metrics"]["moisture_%"] = st.number_input(
                        "Moisture (%)", min_value=0.0, max_value=100.0, step=1.0,
                        value=log["metrics"].get("moisture_%", 0.0), key=f"m_{i}"
                    )
                    edited_log["next_visit"] = str(st.date_input(
                        "Next Visit", datetime.date.fromisoformat(log["next_visit"]), key=f"nv_{i}"
                    ))

                edited_log["notes"] = st.text_area("Notes", log["notes"], key=f"notes_{i}")

                colC1, colC2 = st.columns(2)
                with colC1:
                    if st.button("💾 Save Edit", key=f"save_{i}"):
                        st.session_state.garden_data["logs"][idx] = edited_log
                        st.success("✅ Log updated!")

                with colC2:
                    if st.button("🗑️ Delete Log", key=f"del_{i}"):
                        st.session_state.garden_data["logs"].pop(idx)
                        st.warning("🗑️ Log deleted!")
                        st.experimental_rerun()

    else:
        st.info("No logs yet! Add one above.")

# =======================================================
# 📈 REPORT PAGE
# =======================================================
elif page == "Reports":
    st.header("📈 Garden Timeline Report")

    all_keys = sorted(set([log["batch_key"] for log in st.session_state.garden_data["logs"]]))
    if not all_keys:
        st.info("No logs to report yet.")
    else:
        selected_key = st.selectbox("Select Batch Key", all_keys)

        logs = [log for log in st.session_state.garden_data["logs"] if log["batch_key"] == selected_key]
        logs = sorted(logs, key=lambda x: x["date"])

        st.subheader(f"🪴 Timeline for {selected_key}")
        for log in logs:
            st.markdown(f"**📅 {log['date']} — {log['action']}**")
            st.write(f"🗺️ Section: {log['section']}")
            st.write(f"🌿 Plant: {log['plant']}")
            st.write(f"💬 Notes: {log['notes'] or '-'}")
            st.write(f"📏 Height: {log['metrics']['height_cm']} cm | 💧 Moisture: {log['metrics']['moisture_%']}%")
            st.write(f"🔔 Next Visit: {log['next_visit']}")
            st.markdown("---")

# =======================================================
# 🧩 GARDEN LAYOUT PAGE
# =======================================================
elif page == "Garden Layout":
    st.header("🧩 Garden Layout Designer")

    sections = list(st.session_state.garden_data["layout"].keys())
    new_section = st.text_input("Add new section name")

    if st.button("➕ Add Section"):
        if new_section:
            st.session_state.garden_data["layout"][new_section] = {"rows": 3, "cols": 3, "grid": [["" for _ in range(3)] for _ in range(3)]}
            st.success(f"Added new section: {new_section}")

    selected_section = st.selectbox("Select Section", sections if sections else ["No sections yet"])

    if selected_section != "No sections yet":
        section_data = st.session_state.garden_data["layout"][selected_section]
        rows = st.number_input("Rows", min_value=1, max_value=10, value=section_data["rows"])
        cols = st.number_input("Columns", min_value=1, max_value=10, value=section_data["cols"])

        if rows != section_data["rows"] or cols != section_data["cols"]:
            section_data["rows"], section_data["cols"] = rows, cols
            section_data["grid"] = [["" for _ in range(cols)] for _ in range(rows)]

        st.markdown("### 🌿 Click below to assign what’s sown in each tile")

        plants = [""] + st.session_state.garden_data["inventory"]["vegetables"] + st.session_state.garden_data["inventory"]["fruits"]
        for r in range(section_data["rows"]):
            cols_container = st.columns(section_data["cols"])
            for c in range(section_data["cols"]):
                with cols_container[c]:
                    current = section_data["grid"][r][c]
                    section_data["grid"][r][c] = st.selectbox(
                        f"({r+1},{c+1})", plants, index=plants.index(current) if current in plants else 0, key=f"{selected_section}_{r}_{c}"
                    )

        st.success("✅ Layout updated! Don’t forget to download JSON to save it permanently.")

# =======================================================
# 💾 DOWNLOAD
# =======================================================
st.sidebar.download_button(
    label="💾 Download Garden Data",
    data=json.dumps(st.session_state.garden_data, indent=2),
    file_name="garden_log.json",
    mime="application/json"
)

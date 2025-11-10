import streamlit as st
import json
import datetime
import random
import pandas as pd
import plotly.express as px

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🌿 My Garden Log", layout="wide")

# ---------- INIT DATA ----------
if "garden_data" not in st.session_state:
    st.session_state.garden_data = {
        "inventory": {"vegetables": [], "fruits": [], "greens": [], "flowers": []},
        "logs": [],
        "layout": {}
    }
    st.session_state["is_clean"] = True

if "batch_colors" not in st.session_state:
    st.session_state.batch_colors = {}

# ---------- HELPER FUNCTIONS ----------
def get_color_for_key(batch_key):
    if batch_key not in st.session_state.batch_colors:
        hue = random.randint(0, 360)
        color = f"hsl({hue}, 70%, 70%)"
        st.session_state.batch_colors[batch_key] = color
    return st.session_state.batch_colors[batch_key]

# ---------- SIDEBAR ----------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["📊 Reports", "📝 Daily Log", "🧩 Garden Layout", "🌱 Inventory", "🔧 JSON Editor"]
)

st.sidebar.divider()
st.sidebar.header("Data Management")
uploaded_file = st.sidebar.file_uploader("Upload Garden JSON", type="json")
if uploaded_file and st.session_state["is_clean"]:
    uploaded_data = json.load(uploaded_file)
    st.session_state.garden_data = {k:v for k,v in uploaded_data.items() if k != "batch_colors"}
    if "batch_colors" in uploaded_data:
        st.session_state.batch_colors.update(uploaded_data["batch_colors"])
    st.sidebar.success("Garden data loaded!")
    st.session_state["is_clean"] = False

export_data = st.session_state.garden_data.copy()
export_data["batch_colors"] = st.session_state.batch_colors
st.sidebar.download_button(
    "💾 Download Garden Data",
    data=json.dumps(export_data, indent=2),
    file_name="garden_log.json",
    mime="application/json"
)

# ----------------------------------------------------------------
# 📊 PAGE 1: REPORTS
# ----------------------------------------------------------------
if page == "📊 Reports":
    st.header("📊 Batch Report & Timeline")
    logs = st.session_state.garden_data.get("logs", [])
    if not logs:
        st.info("No logs yet. Add some entries first.")
    else:
        batch_keys = sorted(set(log["batch_key"] for log in logs))
        plants = sorted(set(log["plant"] for log in logs))
        sections = sorted(set(log["section"] for log in logs))

        st.subheader("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_batches = st.multiselect("Batch Keys", ["All"] + batch_keys, default=["All"])
        with col2:
            selected_plant = st.multiselect("Plant", ["All"] + plants, default=["All"])
        with col3:
            selected_section = st.multiselect("Section", ["All"] + sections, default=["All"])

        all_dates = sorted([datetime.date.fromisoformat(log["date"]) for log in logs])
        start_date = st.date_input("From Date", all_dates[0] if all_dates else datetime.date.today())
        end_date = st.date_input("To Date", all_dates[-1] if all_dates else datetime.date.today())

        # Filter logs
        filtered_logs = []
        for log in logs:
            log_date = datetime.date.fromisoformat(log["date"])
            if not (start_date <= log_date <= end_date):
                continue
            if "All" not in selected_batches and log["batch_key"] not in selected_batches:
                continue
            if "All" not in selected_plant and log["plant"] not in selected_plant:
                continue
            if "All" not in selected_section and log["section"] not in selected_section:
                continue
            filtered_logs.append(log)

        if not filtered_logs:
            st.warning("No logs match your filters.")
        else:
            filtered_logs = sorted(filtered_logs, key=lambda x: x["date"])
            df = pd.DataFrame(filtered_logs)
            df["Date"] = pd.to_datetime(df["date"])

            # Select batch to highlight in layout
            all_batch_keys = sorted(set(log["batch_key"] for log in filtered_logs))
            selected_batch_for_highlight = st.selectbox(
                "Select a batch to highlight in layout:",
                ["None"] + all_batch_keys,
                index=0
            )
            st.session_state.selected_batch = selected_batch_for_highlight if selected_batch_for_highlight != "None" else None

            # Timeline list view
            st.subheader("📅 Filtered Logs Timeline")
            batch_groups = {}
            for log in filtered_logs:
                batch_groups.setdefault(log["batch_key"], []).append(log)

            for batch_key, logs_list in batch_groups.items():
                color = get_color_for_key(batch_key)
                st.markdown(f"<h4 style='color:{color};'>🌿 {batch_key}</h4>", unsafe_allow_html=True)
                for log in sorted(logs_list, key=lambda x: x["date"]):
                    st.markdown(
                        f"<div style='border-left:5px solid {color}; padding:6px 10px; margin:6px;'>"
                        f"<b>{log['date']}</b> — {log['action']} in <b>{log['section']}</b><br>"
                        f"<i>{log['notes']}</i><br>"
                        f"<small>Height: {log['metrics'].get('height_cm', '—')} cm, "
                        f"Moisture: {log['metrics'].get('moisture_%', '—')}%</small>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Summary metrics
            st.subheader("📈 Summary Metrics")
            avg_height = sum(l["metrics"].get("height_cm", 0) for l in filtered_logs if l["metrics"].get("height_cm")) / max(1, sum(1 for l in filtered_logs if l["metrics"].get("height_cm")))
            avg_moisture = sum(l["metrics"].get("moisture_%", 0) for l in filtered_logs if l["metrics"].get("moisture_%")) / max(1, sum(1 for l in filtered_logs if l["metrics"].get("moisture_%")))
            st.write(f"**Average Height:** {avg_height:.1f} cm")
            st.write(f"**Average Moisture:** {avg_moisture:.1f}%")

            # Gantt Chart
            st.subheader("📊 Gantt-Style Plant Lifecycle")
            gantt_rows = []
            for batch_key, group in df.groupby("batch_key"):
                batch_logs = group.sort_values("Date")
                for i, row in batch_logs.iterrows():
                    start_date = row["Date"]
                    next_logs = batch_logs[batch_logs["Date"] > start_date]
                    end_date = next_logs.iloc[0]["Date"] if not next_logs.empty else start_date + pd.Timedelta(days=1)
                    gantt_rows.append({
                        "Batch Key": batch_key,
                        "Action": row["action"],
                        "Start": start_date,
                        "Finish": end_date,
                        "Section": row["section"],
                        "Notes": row["notes"]
                    })

            gantt_df = pd.DataFrame(gantt_rows)
            color_map = {k: get_color_for_key(k) for k in gantt_df["Batch Key"].unique()}
            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Batch Key",
                color="Batch Key",
                hover_data=["Action", "Section", "Notes"],
                color_discrete_map=color_map
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=500, margin=dict(l=40, r=20, t=30, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------
# 📝 PAGE 2: DAILY LOG
# ----------------------------------------------------------------
elif page == "📝 Daily Log":
    st.header("📝 Daily Log Entry")
    sections = ["Indoor", "Backyard", "Front Garden", "Raised Beds"]
    plants = st.session_state.garden_data["inventory"]["vegetables"] + st.session_state.garden_data["inventory"]["fruits"] +
    + st.session_state.garden_data["inventory"]["flowers"]
    + st.session_state.garden_data["inventory"]["greens"]

    with st.form("log_form"):
        date = st.date_input("Date", datetime.date.today())
        section = st.selectbox("Section", sections)
        plant = st.selectbox("Plant", plants)
        action = st.selectbox("Action", ["Sown", "Transplanted", "Watered", "Fertilized", "Measured", "Harvested"])

        existing_keys = sorted(set([log["batch_key"] for log in st.session_state.garden_data["logs"]]))
        default_key = f"{plant}-Set-{date}"
        use_existing = st.checkbox("Select existing batch key?")
        if use_existing and existing_keys:
            batch_key = st.selectbox("Choose Batch Key", existing_keys)
        else:
            batch_key = st.text_input("Create / Edit Batch Key", default_key)

        height = st.number_input("Height (cm)", min_value=0.0, step=0.1)
        moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, step=1.0)
        notes = st.text_area("Notes")
        next_visit = st.date_input("Next Visit / Reminder", date + datetime.timedelta(days=7))

        submitted = st.form_submit_button("Add Log Entry")
        if submitted:
            log_entry = {
                "date": str(date),
                "section": section,
                "plant": plant,
                "action": action,
                "batch_key": batch_key,
                "metrics": {"height_cm": height},
                "notes": notes,
                "next_visit": str(next_visit)
            }
            st.session_state.garden_data["logs"].append(log_entry)
            get_color_for_key(batch_key)
            st.success("✅ Log entry added!")

    st.subheader("📖 Existing Logs")
    if st.session_state.garden_data["logs"]:
        for i, log in enumerate(reversed(st.session_state.garden_data["logs"])):
            idx = len(st.session_state.garden_data["logs"]) - 1 - i
            with st.expander(f"{log['date']} - {log['plant']} ({log['action']})"):
                edited = st.text_area("Edit Log (JSON)", json.dumps(log, indent=2), key=f"edit_{idx}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Edit", key=f"save_{idx}"):
                        try:
                            st.session_state.garden_data["logs"][idx] = json.loads(edited)
                            st.success("Saved!")
                        except json.JSONDecodeError as e:
                            st.error(f"Invalid JSON: {e}")
                with col2:
                    if st.button("🗑 Delete", key=f"delete_{idx}"):
                        st.session_state.garden_data["logs"].pop(idx)
                        st.warning("Deleted entry.")
                        st.experimental_rerun()
    else:
        st.info("No logs yet! Add one above.")

# ----------------------------------------------------------------
# 🧩 PAGE 3: GARDEN LAYOUT
# ----------------------------------------------------------------
elif page == "🧩 Garden Layout":
    st.header("🧩 Design Your Garden Layout")
    sections = ["Indoor", "Backyard", "Front Garden", "Raised Beds"]
    selected_section = st.selectbox("Select Section", sections)

    if selected_section not in st.session_state.garden_data["layout"]:
        st.session_state.garden_data["layout"][selected_section] = {"rows": 3, "cols": 3, "grid": [[[] for _ in range(3)] for _ in range(3)]}

    section_data = st.session_state.garden_data["layout"][selected_section]
    rows = st.number_input("Rows", 1, 10, section_data["rows"])
    cols = st.number_input("Cols", 1, 10, section_data["cols"])
    if rows != section_data["rows"] or cols != section_data["cols"]:
        section_data["rows"], section_data["cols"] = rows, cols
        section_data["grid"] = [[[] for _ in range(cols)] for _ in range(rows)]

    batch_keys = sorted(set([log["batch_key"] for log in st.session_state.garden_data["logs"]]))

    # Legend
    st.subheader("🗝️ Legend / Key")
    if batch_keys:
        legend_html = ""
        for k in batch_keys:
            color = get_color_for_key(k)
            legend_html += f'<span style="background-color:{color}; padding:4px 8px; margin:2px; border-radius:4px; display:inline-block;">{k}</span>'
        st.markdown(legend_html, unsafe_allow_html=True)
    st.caption("Hover over a tile to see batch metrics. Avg height/moisture shown for multi-batch tiles.")

    # Animation slider
    all_dates = sorted([datetime.date.fromisoformat(log["date"]) for log in st.session_state.garden_data["logs"]])
    if all_dates:
        min_date, max_date = all_dates[0], all_dates[-1]
    else:
        min_date = max_date = datetime.date.today()
    animation_date = st.slider(
        "🕒 Select Date to Animate",
        min_value=min_date,
        max_value=max_date,
        value=max_date,
        format="YYYY-MM-DD"
    )
    st.session_state.animation_date = animation_date

    # Render tiles
    for r in range(section_data["rows"]):
        cols_container = st.columns(section_data["cols"])
        for c in range(section_data["cols"]):
            with cols_container[c]:
                current_values = section_data["grid"][r][c]
                if not isinstance(current_values, list):
                    current_values = [current_values] if current_values else []

                selected_keys = st.multiselect(
                    f"({r+1},{c+1})",
                    options=batch_keys,
                    default=current_values,
                    key=f"{selected_section}_{r}_{c}"
                )
                section_data["grid"][r][c] = selected_keys

                # Aggregated tooltip
                tooltip_html = ""
                heights, moistures = [], []
                for k in selected_keys:
                    batch_logs = [log for log in st.session_state.garden_data["logs"]
                                  if log["batch_key"] == k and datetime.date.fromisoformat(log["date"]) <= animation_date]
                    if batch_logs:
                        last_log = sorted(batch_logs, key=lambda x: x["date"])[-1]
                        heights.append(last_log["metrics"].get("height_cm", 0))
                        moistures.append(last_log["metrics"].get("moisture_%", 0))
                        action = last_log.get("action", "")
                        date = last_log.get("date", "")
                        notes = last_log.get("notes", "")
                        batch_tooltip = f"{k}: {action} on {date}, Height: {last_log['metrics'].get('height_cm','—')} cm, Moisture: {last_log['metrics'].get('moisture_%','—')}%, Notes: {notes}"
                        batch_color = get_color_for_key(k)
                        if k == st.session_state.get("selected_batch"):
                            style = f"background-color:{batch_color}; padding:3px 6px; border-radius:6px; margin:2px; display:inline-block; border:3px solid black;"
                        else:
                            style = f"background-color:{batch_color}; padding:3px 6px; border-radius:4px; margin:2px; display:inline-block;"
                        tooltip_html += f'<span style="{style}" title="{batch_tooltip}">{k}</span>'
                # Aggregated metrics
                if heights or moistures:
                    avg_height = sum(heights)/len(heights) if heights else "—"
                    avg_moisture = sum(moistures)/len(moistures) if moistures else "—"
                    tooltip_html = f'<div title="Avg Height: {avg_height:.1f} cm, Avg Moisture: {avg_moisture:.1f}%">{tooltip_html}</div>'

                if tooltip_html:
                    st.markdown(tooltip_html, unsafe_allow_html=True)

# ----------------------------------------------------------------
# 🌱 PAGE 4: INVENTORY
# ----------------------------------------------------------------
elif page == "🌱 Inventory":
    st.header("🌱 Manage Inventory")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add New Plant")
        item_type = st.selectbox("Type", ["Vegetables", "Greens", "Fruits", "Flowers"])
        item_name = st.text_input("Name of the plant")
        if st.button("Add to Inventory"):
            if item_name:
                st.session_state.garden_data["inventory"][item_type.lower()].append(item_name)
                st.success(f"Added {item_name} to {item_type.lower()} inventory")

    with col2:
        st.subheader("Current Inventory")
        st.json(st.session_state.garden_data["inventory"])

# ----------------------------------------------------------------
# 🔧 PAGE 5: JSON EDITOR
# ----------------------------------------------------------------
elif page == "🔧 JSON Editor":
    st.header("🔧 Advanced JSON Editor")
    live_json = {**st.session_state.garden_data, "batch_colors": st.session_state.batch_colors}
    json_text = st.text_area("Garden Data (editable JSON)", json.dumps(live_json, indent=2), height=500)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save JSON Changes"):
            try:
                new_data = json.loads(json_text)
                if "batch_colors" in new_data:
                    st.session_state.batch_colors = new_data.pop("batch_colors")
                st.session_state.garden_data = new_data
                st.success("✅ JSON updated successfully!")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
    with col2:
        if st.button("🔁 Reset View"):
            st.experimental_rerun()

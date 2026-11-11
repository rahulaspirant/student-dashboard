from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURATION
# Keep dashboard.py and "Sample Data.xlsx" in the same folder.
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "Sample Data.xlsx"
SHEET_NAME = "Sheet1"

st.set_page_config(
    page_title="Student Data Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Student Data Dashboard")
st.caption(f"Source file: {EXCEL_FILE.name}")

# ---------------------------------------------------------
# 2. INFRASTRUCTURE: read the Excel file
# Streamlit caches the data briefly; use the refresh button
# to reload after editing the workbook.
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    data.columns = data.columns.astype(str).str.strip()
    return data


if st.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

if not EXCEL_FILE.exists():
    st.error(
        f"Excel file not found: {EXCEL_FILE}\n\n"
        "Place 'Sample Data.xlsx' in the same folder as dashboard.py."
    )
    st.stop()

try:
    df = load_data(str(EXCEL_FILE), SHEET_NAME)
except Exception as exc:
    st.error(f"Could not read the Excel file or sheet '{SHEET_NAME}'. Details: {exc}")
    st.stop()

required_columns = [
    "Student Name",
    "Gender",
    "Class Level",
    "Home State",
    "Major",
    "Extracurricular Activity",
    "Marks",
    "Joining Date",
]
missing_columns = [column for column in required_columns if column not in df.columns]

if missing_columns:
    st.error("These required columns are missing: " + ", ".join(missing_columns))
    st.stop()

# Clean the fields used by the dashboard.
for column in [
    "Student Name",
    "Gender",
    "Class Level",
    "Home State",
    "Major",
    "Extracurricular Activity",
]:
    df[column] = df[column].astype("string").str.strip()

df["Marks"] = pd.to_numeric(df["Marks"], errors="coerce")
df["Joining Date"] = pd.to_datetime(df["Joining Date"], errors="coerce")

# ---------------------------------------------------------
# 3. FILTERS: all charts and KPIs use the filtered dataset
# ---------------------------------------------------------
st.sidebar.header("Filters")

def options_for(column: str):
    values = df[column].dropna().astype(str).unique().tolist()
    return sorted(values)

gender_options = st.sidebar.multiselect(
    "Gender", options_for("Gender"), default=options_for("Gender")
)
class_options = st.sidebar.multiselect(
    "Class Level", options_for("Class Level"), default=options_for("Class Level")
)
major_options = st.sidebar.multiselect(
    "Major", options_for("Major"), default=options_for("Major")
)
activity_options = st.sidebar.multiselect(
    "Extracurricular Activity",
    options_for("Extracurricular Activity"),
    default=options_for("Extracurricular Activity"),
)
state_options = st.sidebar.multiselect(
    "Home State", options_for("Home State"), default=options_for("Home State")
)

filtered = df[
    df["Gender"].isin(gender_options)
    & df["Class Level"].isin(class_options)
    & df["Major"].isin(major_options)
    & df["Extracurricular Activity"].isin(activity_options)
    & df["Home State"].isin(state_options)
].copy()

# ---------------------------------------------------------
# 4. KPI SUMMARY
# "Student records" counts rows. "Unique names" counts distinct names.
# These can differ if a name occurs more than once.
# ---------------------------------------------------------
total_records = len(filtered)
unique_students = filtered["Student Name"].nunique()
average_marks = filtered["Marks"].mean()
highest_marks = filtered["Marks"].max()
top_major = (
    filtered["Major"].mode().iloc[0]
    if not filtered["Major"].dropna().empty
    else "N/A"
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Student Records", f"{total_records:,}")
k2.metric("Unique Names", f"{unique_students:,}")
k3.metric("Average Marks", "N/A" if pd.isna(average_marks) else f"{average_marks:.1f}")
k4.metric("Highest Marks", "N/A" if pd.isna(highest_marks) else f"{highest_marks:g}")
k5.metric("Most Common Major", top_major)

st.divider()

if filtered.empty:
    st.warning("No records match the selected filters. Change the filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------
# 5. CHARTS
# ---------------------------------------------------------
left, right = st.columns(2)

with left:
    gender_counts = (
        filtered["Gender"].value_counts()
        .rename_axis("Gender")
        .reset_index(name="Students")
    )
    fig_gender = px.pie(
        gender_counts,
        names="Gender",
        values="Students",
        hole=0.45,
        title="Student Records by Gender",
    )
    st.plotly_chart(fig_gender, use_container_width=True)

with right:
    class_counts = (
        filtered["Class Level"].value_counts()
        .rename_axis("Class Level")
        .reset_index(name="Students")
    )
    fig_class = px.bar(
        class_counts,
        x="Class Level",
        y="Students",
        title="Student Records by Class Level",
        text="Students",
    )
    fig_class.update_layout(xaxis_title="", yaxis_title="Number of records")
    st.plotly_chart(fig_class, use_container_width=True)

left, right = st.columns(2)

with left:
    major_marks = (
        filtered.groupby("Major", dropna=False)["Marks"]
        .mean()
        .reset_index(name="Average Marks")
        .sort_values("Average Marks", ascending=False)
    )
    fig_major = px.bar(
        major_marks,
        x="Major",
        y="Average Marks",
        title="Average Marks by Major",
        text_auto=".1f",
    )
    fig_major.update_layout(xaxis_title="Major", yaxis_title="Average marks")
    st.plotly_chart(fig_major, use_container_width=True)

with right:
    activity_counts = (
        filtered["Extracurricular Activity"].value_counts()
        .rename_axis("Extracurricular Activity")
        .reset_index(name="Students")
        .sort_values("Students", ascending=True)
    )
    fig_activity = px.bar(
        activity_counts,
        x="Students",
        y="Extracurricular Activity",
        orientation="h",
        title="Participation by Extracurricular Activity",
        text="Students",
    )
    fig_activity.update_layout(xaxis_title="Number of records", yaxis_title="")
    st.plotly_chart(fig_activity, use_container_width=True)

state_counts = (
    filtered["Home State"].value_counts()
    .rename_axis("Home State")
    .reset_index(name="Students")
    .sort_values("Students", ascending=False)
)
fig_state = px.bar(
    state_counts,
    x="Home State",
    y="Students",
    title="Student Records by Home State",
    text="Students",
)
fig_state.update_layout(xaxis_title="Home State", yaxis_title="Number of records")
st.plotly_chart(fig_state, use_container_width=True)

# ---------------------------------------------------------
# 6. DETAIL TABLE + SEARCH
# ---------------------------------------------------------
st.subheader("Student Details")
search_text = st.text_input("Search student name", placeholder="Type a name...")
display_columns = [
    "Student Name",
    "Gender",
    "Class Level",
    "Home State",
    "Major",
    "Extracurricular Activity",
    "Marks",
    "Joining Date",
]
details = filtered[display_columns].copy()

if search_text.strip():
    details = details[
        details["Student Name"].str.contains(search_text.strip(), case=False, na=False)
    ]

st.dataframe(details, use_container_width=True, hide_index=True)

csv_data = details.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered student data (CSV)",
    data=csv_data,
    file_name="filtered_student_data.csv",
    mime="text/csv",
)

st.caption(
    f"Showing {len(details):,} detail rows from {len(filtered):,} filtered records. "
    "The dashboard reads the workbook from the same folder as this script."
)

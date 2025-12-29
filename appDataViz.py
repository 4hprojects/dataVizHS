import streamlit as st
import pandas as pd
import plotly.express as px

# ---------- CONFIG ----------

st.set_page_config(
    page_title="PH Education Enrollment Dashboard",
    layout="wide"
)

# ---------- DATA LOADING ----------

@st.cache_data
def load_data(uploaded_file=None, default_path=None):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_excel(default_path)

    # Standardise column names
    df.columns = [c.strip() for c in df.columns]
    return df


def compute_shs(df):
    shs = df[(df["Level"] == "Senior High School") &
             df["Total Infrastructure"].notna()].copy()
    shs["Learners per Infra"] = (
        shs["Total Enrollment"] / shs["Total Infrastructure"]
    )
    return shs


def get_year_order(df):
    # Keep original string order as in data, but sorted for consistency
    years = sorted(df["School Year"].unique())
    return years


# ---------- SIDEBAR ----------

st.sidebar.title("Settings")

uploaded = st.sidebar.file_uploader(
    "Upload Education Dataset (.xlsx)",
    type=["xlsx"]
)

default_path = "Education Dataset (1).xlsx"  # update path if needed

try:
    df = load_data(uploaded_file=uploaded, default_path=default_path)
except Exception:
    st.error("Error loading dataset. Check file name/path or upload the file.")
    st.stop()

years = get_year_order(df)
min_year = years[0]
max_year = years[-1]

st.sidebar.markdown("### Year controls")
selected_year_for_ranking = st.sidebar.selectbox(
    "Select year for congestion ranking",
    options=years,
    index=years.index(max_year)
)

st.sidebar.markdown("---")
st.sidebar.write("Columns detected:")
st.sidebar.write(list(df.columns))

# Prepare SHS-only data
shs = compute_shs(df)

# ---------- MAIN TITLE ----------

st.title("A Data-Driven Analysis of Education Enrollment in the Philippines")
st.caption("Dashboard views based on the DepEd regional dataset for basic education")

st.markdown("---")

# ============================================================
# SECTION 1: NATIONAL SHS ENROLLMENT VS INFRASTRUCTURE
# ============================================================

st.subheader("National Senior High School Enrollment and Infrastructure (All Years)")

nat_shs = shs.groupby("School Year").agg(
    total_enrollment=("Total Enrollment", "sum"),
    total_infra=("Total Infrastructure", "sum")
).reset_index()

fig_nat = px.line(
    nat_shs,
    x="School Year",
    y=["total_enrollment", "total_infra"],
    markers=True
)

fig_nat.update_layout(
    title="National Senior High School Enrollment vs Infrastructure",
    xaxis_title="School Year",
    yaxis_title="Count",
    legend_title="Metric"
)

st.plotly_chart(fig_nat, use_container_width=True)

st.write(
    "This view shows how Senior High School enrollment has grown across school years "
    "compared to the slower change in reported infrastructure."
)

st.markdown("---")

# ============================================================
# SECTION 2: CONGESTION TRENDS IN HIGH-GROWTH REGIONS
# ============================================================

st.subheader("Congestion Trends in High-Growth Regions (Learners per Facility)")

focus_regions = {
    "NCR - National Capital Region": "NCR",
    "Region IV-A - CALABARZON": "CALABARZON",
    "Region III - Central Luzon": "Central Luzon",
    "Region XI - Davao Region": "Davao",
    "Region X - Northern Mindanao": "Northern Mindanao",
}

shs_focus = shs[shs["Region"].isin(focus_regions.keys())].copy()
shs_focus["Region Short"] = shs_focus["Region"].map(focus_regions)

region_year_ratio = (
    shs_focus.groupby(["School Year", "Region Short"])["Learners per Infra"]
    .mean()
    .reset_index()
)

fig_cong = px.line(
    region_year_ratio,
    x="School Year",
    y="Learners per Infra",
    color="Region Short",
    markers=True
)

fig_cong.update_layout(
    title="SHS Congestion Trends in Selected Regions",
    xaxis_title="School Year",
    yaxis_title="Learners per Facility",
    legend_title="Region"
)

st.plotly_chart(fig_cong, use_container_width=True)

st.write(
    "These trends highlight how congestion has changed over time in the National Capital Region, "
    "CALABARZON, Central Luzon, Davao Region, and Northern Mindanao."
)

st.markdown("---")

# ============================================================
# SECTION 3: PUBLIC VS PRIVATE SHS ENROLLMENT (TWO YEARS)
# ============================================================

st.subheader("Public and Private Senior High School Enrollment")

col_year1, col_year2 = st.columns(2)

with col_year1:
    year_a = st.selectbox(
        "Select first school year",
        options=years,
        index=0,
        key="year_a"
    )

with col_year2:
    year_b = st.selectbox(
        "Select second school year",
        options=years,
        index=len(years) - 1,
        key="year_b"
    )

compare_years = [year_a, year_b]

shs_sector = shs[
    (shs["Region"].isin(focus_regions.keys())) &
    (shs["School Year"].isin(compare_years)) &
    (shs["Sector"].isin(["PUBLIC", "PRIVATE"]))
].copy()

sector_summary = (
    shs_sector.groupby(["Region", "School Year", "Sector"])["Total Enrollment"]
    .sum()
    .reset_index()
)

sector_summary["Region Short"] = sector_summary["Region"].map(focus_regions)

fig_sector = px.bar(
    sector_summary,
    x="Region Short",
    y="Total Enrollment",
    color="Sector",
    barmode="group",
    facet_col="School Year",
    category_orders={"School Year": compare_years}
)

fig_sector.update_layout(
    title="Public and Private Senior High School Enrollment in Selected Regions",
    xaxis_title="Region",
    yaxis_title="Enrollment"
)

st.plotly_chart(fig_sector, use_container_width=True)

st.write(
    "These grouped bars compare public and private Senior High School enrollment in key regions "
    f"for {year_a} and {year_b}, highlighting shifts in sector reliance over time."
)

st.markdown("---")

# ============================================================
# SECTION 4: SHS CONGESTION RANKING (SELECTED YEAR)
# ============================================================

st.subheader(f"Senior High School Congestion Ranking for {selected_year_for_ranking}")

shs_year = shs[shs["School Year"] == selected_year_for_ranking].copy()

ranking = (
    shs_year.groupby("Region")["Learners per Infra"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

fig_rank = px.bar(
    ranking,
    x="Learners per Infra",
    y="Region",
    orientation="h"
)

fig_rank.update_layout(
    title=f"Regions Ranked by SHS Congestion (Learners per Facility, {selected_year_for_ranking})",
    xaxis_title="Learners per Facility",
    yaxis_title="Region",
    yaxis=dict(autorange="reversed")
)

st.plotly_chart(fig_rank, use_container_width=True)

st.write(
    "Regions at the top of this ranking have the highest number of Senior High School learners per facility. "
    "They can be considered priority candidates for new buildings and specialised SHS rooms."
)

st.markdown("---")

# ============================================================
# SECTION 5: OPTIONAL RAW DATA VIEW
# ============================================================

with st.expander("Show raw Senior High School data"):
    st.dataframe(shs.reset_index(drop=True))

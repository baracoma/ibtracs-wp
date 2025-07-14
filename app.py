import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
import calendar

# Load preprocessed Parquet file
DATA_PATH = "data/ibtracs_wp_tracks.parquet"
df_tracks = pd.read_parquet(DATA_PATH)

# Sidebar Controls
st.sidebar.header("Start Date")

years = sorted(df_tracks['ISO_TIME'].dt.year.unique())
months = list(range(1, 13))

start_year = st.sidebar.selectbox("Start Year", years)
start_month = st.sidebar.selectbox("Start Month", months)
max_start_day = calendar.monthrange(start_year, start_month)[1]
start_day = st.sidebar.selectbox("Start Day", list(range(1, max_start_day + 1)))

# Adjust end year options based on start year
years_end = [y for y in years if y >= start_year]

st.sidebar.header("End Date")
end_year = st.sidebar.selectbox("End Year", years_end, index=len(years_end) - 1)
end_month = st.sidebar.selectbox("End Month", months)
max_end_day = calendar.monthrange(end_year, end_month)[1]
end_day = st.sidebar.selectbox("End Day", list(range(1, max_end_day + 1)))

# Force logical consistency between start and end dates
start_date = datetime(start_year, start_month, start_day)
end_date = datetime(end_year, end_month, end_day)

if end_date < start_date:
    st.error("End date cannot be earlier than start date. Please adjust your selection.")
    st.stop()

# Identify SIDs with at least one point within date range
sids_in_range = df_tracks.loc[
    (df_tracks['ISO_TIME'] >= pd.to_datetime(start_date)) &
    (df_tracks['ISO_TIME'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)),
    "SID"
].unique()

# Filter full tracks for those SIDs
filtered = df_tracks[df_tracks['SID'].isin(sids_in_range)].copy()

sids_in_range_set = set(sids_in_range)
sids_intersects_par = df_tracks.loc[
    df_tracks['SID'].isin(sids_in_range_set) & (df_tracks['intersects_par'] == True),
    'SID'
].unique()
sids_intersects_ph = df_tracks.loc[
    df_tracks['SID'].isin(sids_in_range_set) & (df_tracks['intersects_ph'] == True),
    'SID'
].unique()

st.write(f"Total Tropical Cyclones (TCs) selected: {len(sids_in_range)}")
st.write(f"TCs entering Philippine Area of Responsibility (PAR): {len(sids_intersects_par)}")
st.write(f"TCs making landfall in the Philippines: {len(sids_intersects_ph)}")

par_polygon = {
    'coordinates': [[
        [115, 5],
        [115, 15],
        [120, 21],
        [120, 25],
        [135, 25],
        [135, 5],
        [115, 5]
    ]]
}
par_layer = pdk.Layer(
    "PolygonLayer",
    data=[par_polygon],
    get_polygon="coordinates",
    get_fill_color="[200, 200, 200, 40]",
    get_line_color="[80, 80, 80]",
    line_width_min_pixels=2
)

layers = []
if not filtered.empty:
    path_data = (
        filtered.sort_values(["SID", "ISO_TIME"])
        .groupby("SID", group_keys=False)
        .apply(lambda g: g[["LON", "LAT"]].values.tolist())
        .reset_index()
        .rename(columns={0: "path"})
    )

    path_data["WMO_WIND"] = (
        filtered.groupby("SID")["WMO_WIND"].max().reset_index(drop=True)
    )

    layers.append(pdk.Layer(
        "PathLayer",
        data=path_data,
        get_path="path",
        get_color="[WMO_WIND || 20, 100, 200]",
        width_scale=20,
        width_min_pixels=2,
        pickable=True,
    ))

# Always add PAR layer regardless of filtering result
layers.append(par_layer)




st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(
        latitude=15,
        longitude=125,
        zoom=4,
        pitch=0,
    ),
))


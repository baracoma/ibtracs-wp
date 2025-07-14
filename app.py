import streamlit as st

st.set_page_config(layout="wide")

import pandas as pd
import pydeck as pdk
from datetime import datetime
import calendar

def wind_to_color(wind):
    if pd.isna(wind) or wind <= 0:
        return [255, 255, 255]  # white
    else:
        scale = min(wind / 150, 1.0)
        green_blue = int(255 * (1 - scale))
        return [255, green_blue, green_blue]

# Load preprocessed Parquet file
DATA_PATH = "data/ibtracs_wp_tracks.parquet"
df_tracks = pd.read_parquet(DATA_PATH)
df_tracks["WMO_WIND"] = pd.to_numeric(df_tracks["WMO_WIND"], errors="coerce")
df_tracks["WMO_PRES"] = pd.to_numeric(df_tracks["WMO_PRES"], errors="coerce")

# Sidebar Controls
st.sidebar.header("Start Date")

years = sorted(df_tracks['ISO_TIME'].dt.year.unique())
months = list(range(1, 13))

default_start_year = 2024
default_end_year = 2024

start_year = st.sidebar.selectbox("Start Year", years, index=years.index(default_start_year))
start_month = st.sidebar.selectbox("Start Month", months, index=0)  # January
max_start_day = calendar.monthrange(start_year, start_month)[1]
start_day = st.sidebar.selectbox("Start Day", list(range(1, max_start_day + 1)), index=0)  # Day 1

years_end = [y for y in years if y >= start_year]

st.sidebar.header("End Date")
end_year = st.sidebar.selectbox("End Year", years_end, index=years_end.index(default_end_year))
end_month = st.sidebar.selectbox("End Month", months, index=11)  # December
max_end_day = calendar.monthrange(end_year, end_month)[1]
end_day = st.sidebar.selectbox("End Day", list(range(1, max_end_day + 1)), index=max_end_day - 1)  # Last day of month

start_date = datetime(start_year, start_month, start_day)
end_date = datetime(end_year, end_month, end_day)

if end_date < start_date:
    st.error("End date cannot be earlier than start date. Please adjust your selection.")
    st.stop()

sids_in_range = df_tracks.loc[
    (df_tracks['ISO_TIME'] >= pd.to_datetime(start_date)) &
    (df_tracks['ISO_TIME'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)),
    "SID"
].unique()

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

layers = [par_layer]

if not filtered.empty:
    # segment_rows = []
    # for sid, group in filtered.sort_values(["SID", "ISO_TIME"]).groupby("SID"):
    #     points = group[["LON", "LAT", "WMO_WIND"]].values.tolist()
    #    for i in range(len(points) - 1):
    #        segment_rows.append({
    #            "SID": sid,
    #            "source": points[i][:2],
    #            "target": points[i + 1][:2],
    #            "WMO_WIND": points[i][2] if not pd.isna(points[i][2]) else 0
    #        })

    segment_rows = []
    for sid, group in filtered.sort_values(["SID", "ISO_TIME"]).groupby("SID"):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            segment_rows.append({
                "SID": sid,
                "source": [group.loc[i, "LON"], group.loc[i, "LAT"]],
                "target": [group.loc[i + 1, "LON"], group.loc[i + 1, "LAT"]],
                "WMO_WIND": group.loc[i, "WMO_WIND"] if not pd.isna(group.loc[i, "WMO_WIND"]) else 0,
                "WMO_PRES": group.loc[i, "WMO_PRES"] if not pd.isna(group.loc[i, "WMO_PRES"]) else 0,
                "ISO_TIME": str(group.loc[i, "ISO_TIME"])
            })


    segment_df = pd.DataFrame(segment_rows)
    segment_df["color"] = segment_df["WMO_WIND"].apply(wind_to_color)

    # line_layer = pdk.Layer(
    #     "LineLayer",
    #     data=segment_df,
    #     get_source_position="source",
    #     get_target_position="target",
    #     get_color="color",
    #     width_scale=2,
    #     width_min_pixels=2,
    #     pickable=True,
    # )

    line_layer = pdk.Layer(
        "LineLayer",
        data=segment_df,
        get_source_position="source",
        get_target_position="target",
        get_color="color",
        width_scale=4,
        width_min_pixels=4,
        pickable=True,
    )

    layers.append(line_layer)

#layers.append(par_layer)
canvas_height = st.session_state.get("map_height", 600)

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(
        latitude=15,
        longitude=125,
        zoom=4,
        pitch=0,
    ),
    tooltip={
        "html": "<b>SID:</b> {SID}<br/>"
                "<b>Time:</b> {ISO_TIME}<br/>"
                "<b>Wind:</b> {WMO_WIND}<br/>"
                "<b>Pressure:</b> {WMO_PRES}",
        "style": {"color": "white"}
    }
), use_container_width=True,
   height=canvas_height,)


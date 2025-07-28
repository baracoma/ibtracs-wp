import streamlit as st

#st.set_page_config(layout="wide")

st.set_page_config(page_title="IBTrACS Philippines Dashboard", layout="wide")
st.title("IBTrACS Philippines Dashboard")


import pandas as pd
import pydeck as pdk
from datetime import datetime
import calendar

#from matplotlib import cm
import numpy as np




# def wind_to_color(wind):
#     if pd.isna(wind) or wind <= 0:
#         return [255, 255, 255]  # white
#     else:
#         scale = min(wind / 150, 1.0)
#         green_blue = int(255 * (1 - scale))
#         return [255, green_blue, green_blue]

viridis_colors = [
    [68, 1, 84],
    [71, 39, 119],
    [62, 73, 137],
    [48, 103, 141],
    [37, 130, 142],
    [30, 157, 136],
    [53, 183, 120],
    [109, 206, 88],
    [181, 221, 43],
    [253, 231, 36]
]

magma_colors = [
    [0, 0, 3],
    [23, 15, 60],
    [67, 15, 117],
    [113, 31, 129],
    [158, 46, 126],
    [205, 63, 112],
    [240, 96, 93],
    [253, 149, 103],
    [254, 201, 141],
    [251, 252, 191]
]

reds_colors = [
    [255, 245, 240],
    [254, 226, 213],
    [252, 195, 172],
    [252, 159, 129],
    [251, 124, 92],
    [245, 84, 60],
    [227, 47, 39],
    [193, 21, 27],
    [157, 13, 20],
    [103, 0, 12]
]

def interpolate_from_list(color_list, t):
    n = len(color_list) - 1
    idx = int(t * n)
    frac = (t * n) - idx
    if idx >= n:
        return color_list[-1]
    c0 = color_list[idx]
    c1 = color_list[idx + 1]
    return [
        int(c0[i] + (c1[i] - c0[i]) * frac)
        for i in range(3)
    ]

# def wind_to_color(wind):
#     if pd.isna(wind) or wind <= 0:
#         return [255, 255, 255]

#     scale = min(wind / 150, 1.0)

#     if color_scheme == "Viridis":
#         return interpolate_from_list(viridis_colors, scale)
#     elif color_scheme == "Magma":
#         return interpolate_from_list(magma_colors, scale)
#     else:
#         return interpolate_from_list(reds_colors, scale)


def value_to_color(value, variable):
    if pd.isna(value):
        return [255, 255, 255]

    if variable == "WMO_WIND":
        scale = min(value / 150, 1.0)  # Higher wind → higher color
    elif variable == "WMO_PRES":
        scale = 1.0 - min(max((value - 870) / (1050 - 870), 0.0), 1.0)  # Lower pressure → higher color

    if color_scheme == "Viridis":
        return interpolate_from_list(viridis_colors, scale)
    elif color_scheme == "Magma":
        return interpolate_from_list(magma_colors, scale)
    else:
        return interpolate_from_list(reds_colors, scale)


# Load preprocessed Parquet file
DATA_PATH = "data/ibtracs_wp_tracks.parquet"
df_tracks = pd.read_parquet(DATA_PATH)
df_tracks["WMO_WIND"] = pd.to_numeric(df_tracks["WMO_WIND"], errors="coerce")
df_tracks["WMO_PRES"] = pd.to_numeric(df_tracks["WMO_PRES"], errors="coerce")

# Sidebar Controls
st.sidebar.header("Start Date")

years = sorted(df_tracks['ISO_TIME'].dt.year.unique(), reverse=True)
months = list(range(1, 13))

# Set default years but check first if they exist
#default_start_year = 2024 if 2024 in years else max(years)

#start_year = st.sidebar.selectbox(
    #"Start Year", years, index=years.index(default_start_year), key="start_year_select"
#)

# End year options depend on start year forward
#years_end = [y for y in years if y >= start_year]

#default_end_year = 2024 if 2024 in years_end else years_end[0]

#start_year = st.sidebar.selectbox("Start Year", years, index=years.index(default_start_year))
#start_month = st.sidebar.selectbox("Start Month", months, index=0)  # January
#max_start_day = calendar.monthrange(start_year, start_month)[1]
#start_day = st.sidebar.selectbox("Start Day", list(range(1, max_start_day + 1)), index=0)  # Day 1

#years_end = [y for y in years if y >= start_year]

# Initialize session state defaults
# Set up years and months
years = sorted(df_tracks['ISO_TIME'].dt.year.unique(), reverse=True)
months = list(range(1, 13))

# Initialize session state defaults
if "start_year" not in st.session_state:
    st.session_state.start_year = 2024 if 2024 in years else max(years)
if "end_year" not in st.session_state:
    st.session_state.end_year = st.session_state.start_year

# Select Start Year
st.session_state.start_year = st.sidebar.selectbox(
    "Start Year", years, index=years.index(st.session_state.start_year), key="start_year_select"
)

years_end = [y for y in years if y >= st.session_state.start_year]

# Adjust end_year if invalid
if st.session_state.end_year not in years_end:
    st.session_state.end_year = st.session_state.start_year

# Select End Year

# Select Start Month/Day (not session state)
start_month = st.sidebar.selectbox("Start Month", months, index=0)
max_start_day = calendar.monthrange(st.session_state.start_year, start_month)[1]
start_day = st.sidebar.selectbox("Start Day", list(range(1, max_start_day + 1)), index=0)

st.sidebar.header("End Date")
st.session_state.end_year = st.sidebar.selectbox(
    "End Year", years_end, index=years_end.index(st.session_state.end_year), key="end_year_select"
)


# Select End Month/Day
end_month = st.sidebar.selectbox("End Month", months, index=11)
max_end_day = calendar.monthrange(st.session_state.end_year, end_month)[1]
end_day = st.sidebar.selectbox("End Day", list(range(1, max_end_day + 1)), index=max_end_day - 1)

# Assign final values
start_year = st.session_state.start_year
end_year = st.session_state.end_year
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

# st.write(f"Total Tropical Cyclones (TCs) selected: {len(sids_in_range)}")
# st.write(f"TCs entering Philippine Area of Responsibility (PAR): {len(sids_intersects_par)}")
# st.write(f"TCs making landfall in the Philippines: {len(sids_intersects_ph)}")

#st.markdown(f"**Dates selected:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# stats_df = pd.DataFrame({#
#    "Metric": [
#        "Total TCs",
#        "TCs entering PAR",
#        "TCs making Ph landfall"
#    ],
#    "Count": [
#        len(sids_in_range),
#        len(sids_intersects_par),
#        len(sids_intersects_ph)
#    ]
#})
#stats_df = stats_df.reset_index(drop=True)
#st.dataframe(stats_df, width=300, height=150)
#st.table(stats_df.style.hide(axis="index"))
#st.table(stats_df.set_index("Metric"))

#st.markdown(f"**Dates selected:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
st.markdown(f"**Dates selected:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

st.sidebar.header("Counts for the period")

st.sidebar.markdown("""
<table style='width: 220px'>
  <tr><td>Total TCs</td><td style='text-align: right;'>""" + str(len(sids_in_range)) + """</td></tr>
  <tr><td>TCs entering PAR</td><td style='text-align: right;'>""" + str(len(sids_intersects_par)) + """</td></tr>
  <tr><td>TCs making Ph landfall</td><td style='text-align: right;'>""" + str(len(sids_intersects_ph)) + """</td></tr>
</table>
""", unsafe_allow_html=True)

color_scheme = st.sidebar.selectbox("Color scheme", ["Reds", "Viridis", "Magma"])
line_opacity = st.sidebar.slider("Transparency", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
color_by = st.sidebar.selectbox("Variable", ["WMO_WIND", "WMO_PRES"])


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
                # "WMO_WIND": group.loc[i, "WMO_WIND"] if not pd.isna(group.loc[i, "WMO_WIND"]) else 0,
                # "WMO_PRES": group.loc[i, "WMO_PRES"] if not pd.isna(group.loc[i, "WMO_PRES"]) else 0,
                "WMO_WIND": group.loc[i, "WMO_WIND"],
                "WMO_PRES": group.loc[i, "WMO_PRES"],
                "ISO_TIME": str(group.loc[i, "ISO_TIME"])
            })


    segment_df = pd.DataFrame(segment_rows)
    segment_df["WMO_WIND_DISPLAY"] = segment_df["WMO_WIND"]  # For tooltip display
    segment_df["WMO_WIND_PLOT"] = segment_df["WMO_WIND"].fillna(0)  # For plotting color
    # segment_df["color"] = segment_df["WMO_WIND_PLOT"].apply(wind_to_color)
    segment_df["color"] = segment_df[color_by].apply(lambda val: value_to_color(val, color_by))


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

    #line_layer = pdk.Layer(
        #"LineLayer",
        #data=segment_df,
        #get_source_position="source",
        #get_target_position="target",
        #get_color="color",
        #width_scale=4,
        #width_min_pixels=4,
        #pickable=True,
    #)

    line_layer = pdk.Layer(
        "LineLayer",
        data=segment_df,
        get_source_position="source",
        get_target_position="target",
        get_color="color",
        get_width=4,
        width_min_pixels=4,
        pickable=True,
        opacity=line_opacity
    )


    layers.append(line_layer)

#layers.append(par_layer)
canvas_height = st.session_state.get("map_height", 550)

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(
        latitude=15,
        longitude=125,
        zoom=4,
        pitch=0,
    ),
    # tooltip={
    #     "html": "<b>SID:</b> {SID}<br/>"
    #             "<b>Time:</b> {ISO_TIME}<br/>"
    #             "<b>Wind:</b> {WMO_WIND_DISPLAY} kt<br/>"
    #             "<b>Pressure:</b> {WMO_PRES} mb",
    #     "style": {"color": "white"}
    # }
    tooltip={
        "html": f"<b>SID:</b> {{SID}}<br/>"
                f"<b>Time:</b> {{ISO_TIME}}<br/>"
                f"<b>Wind:</b> {{WMO_WIND}} kt<br/>"
                f"<b>Pressure:</b> {{WMO_PRES}} mb<br/>"
                f"<b>Variable:</b> {color_by}",
        "style": {"color": "white"}
    }

), use_container_width=True,
   height=canvas_height,)

st.markdown("*Note: Tracks shown include the **full paths** of tropical cyclones that intersect the selected dates. Not all points fall within the exact date range.*")

st.markdown("If you find this dashboard helpful, consider supporting future development: [and buy me a ko-fi.](https://ko-fi.com/baracoma)")

st.markdown("""
**About the data:** Data is sourced from [NOAA IBTrACS](https://www.ncdc.noaa.gov/ibtracs/) and filtered for the Western Pacific (WP) basin. WMO_WIND values shown are based on agency-reported best track data. For WP, WMO_WIND primarily reflects **10-minute sustained wind speeds as reported by the Japan Meteorological Agency (JMA)**. Other agencies may use different wind averaging periods; users are advised to consult IBTrACS documentation for detailed metadata.

**Disclaimer:** This dashboard is for educational and research purposes only. The data is provided as is, without warranties of any kind, express or implied, including but not limited to accuracy, completeness, reliability, or fitness for a particular purpose.

There may be differences between IBTrACS tracks and official tracks from the Philippine Atmospheric, Geophysical and Astronomical Services Administration (PAGASA), particularly regarding tropical cyclone names, track paths, intensities, and classification. **The developers do not assume responsibility for reconciling differences between IBTrACS and PAGASA records.**

The developers and data providers do not accept liability for any loss, damage, or consequences resulting from the use of this dashboard. This tool is not intended for operational forecasting, life-and-death decision-making, insurance, legal, or other critical applications.

For complete and official tropical cyclone data and climatology in the Philippines, please consult [PAGASA Climatology and Agrometeorology Division (CAD)](https://www.pagasa.dost.gov.ph/climate/tropical-cyclone-information).
""")



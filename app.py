
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import pydeck as pdk
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(
    page_title="Earthquake Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global Earthquake Dashboard")

st.subheader("Assignment 2")

st.markdown(
    """
    **Prepared by:** G.Jeswanth

    **Assignment:** Capillary Technologies Internship

    **Data Source:** USGS Earthquake API
    """
)

st.divider()

st.write(
    "Explore global earthquake activity using interactive maps, "
    "charts, filters, and downloadable data."
)


# Sidebar filters
st.sidebar.header("Filters")

days = st.sidebar.selectbox(
    "Select time period",
    [7, 14, 30],
    index=0
    format_func=lambda x: f"Last {x} days"
)

min_magnitude = st.sidebar.slider(
    "Minimum magnitude",
    min_value=0.0,
    max_value=7.0,
    value=2.5,
    step=0.5
)

# Fetch data from USGS
@st.cache_data(ttl=300)
def get_earthquake_data(days, min_magnitude):
    from datetime import datetime, timedelta, timezone

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": 20000
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    records = []

    for event in data["features"]:
        properties = event["properties"]
        coordinates = event["geometry"]["coordinates"]

        records.append({
            "Magnitude": properties["mag"],
            "Location": properties["place"],
            "Time": pd.to_datetime(
                properties["time"], unit="ms", utc=True
            ),
            "Longitude": coordinates[0],
            "Latitude": coordinates[1],
            "Depth (km)": coordinates[2],
            "USGS Link": properties["url"]
        })

    return pd.DataFrame(records)

try:
    df = get_earthquake_data(days, min_magnitude)

    if df.empty:
        st.warning("No earthquakes found for these filters.")
        st.stop()

    # Summary cards
    st.subheader("Earthquake Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Earthquakes", len(df))
    col2.metric("Strongest Magnitude", f"{df['Magnitude'].max():.1f}")
    col3.metric("Average Magnitude", f"{df['Magnitude'].mean():.2f}")
    col4.metric("Average Depth", f"{df['Depth (km)'].mean():.1f} km")

    # World map
    st.subheader("🌎 Earthquake Locations")

    map_data = df.dropna(
        subset=["Latitude", "Longitude", "Magnitude"]
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[Longitude, Latitude]",
        get_radius="Magnitude * 15000",
        get_fill_color="[255, 80, 40, 180]",
        pickable=True,
        auto_highlight=True
    )

    view = pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=0.5,
        min_zoom=0.5,
        max_zoom=12
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={
            "html": "<b>{Location}</b><br/>Magnitude: {Magnitude}<br/>Depth: {Depth (km)} km",
            "style": {"color": "white"}
        }
    )

    st.pydeck_chart(deck)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Magnitude Distribution")

        fig1 = px.histogram(
            df,
            x="Magnitude",
            nbins=20,
            title="Earthquakes by Magnitude"
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Earthquake Activity Over Time")

        daily = (
            df.assign(Date=df["Time"].dt.date)
            .groupby("Date")
            .size()
            .reset_index(name="Earthquakes")
        )

        fig2 = px.line(
            daily,
            x="Date",
            y="Earthquakes",
            markers=True,
            title="Daily Earthquake Count"
        )

        st.plotly_chart(fig2, use_container_width=True)

    # Data table
    st.subheader("📋 Earthquake Records")

    st.dataframe(
        df.sort_values("Time", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "USGS Link": st.column_config.LinkColumn("USGS Event")
        }
    )

    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Earthquake Data (CSV)",
        data=csv,
        file_name="earthquake_data.csv",
        mime="text/csv"
    )

    st.caption(
        "Source: USGS Earthquake Hazards Program. "
        "Data is retrieved from the public API and cached for 5 minutes."
    )

except requests.RequestException as error:
    st.error(f"Unable to retrieve USGS data: {error}")

except (ValueError, KeyError, TypeError) as error:
    st.error(f"Unable to process the earthquake data: {error}")

# Project Documentation
st.divider()

st.header("📄 Project Documentation")
st.write(
    "Read the documentation for this Capillary Technologies "
    "internship assignment or download a copy."
)


try:
    with open("earthquake_documentation.pdf", "rb") as file:
        pdf_data = file.read()

    st.download_button(
        label="⬇️ Download Project Documentation",
        data=pdf_data,
        file_name="Earthquake_Dashboard_Documentation.pdf",
        mime="application/pdf"
    )

    with st.expander("📄 View Project Documentation"):
        pdf_viewer(
            input=pdf_data,
            width="100%",
            height=700
        )

except FileNotFoundError:
    st.warning(
        "Documentation PDF not found. "
        "Please place earthquake_documentation.pdf beside app.py."
    )

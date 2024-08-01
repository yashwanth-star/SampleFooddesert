import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from shapely import wkt
import plotly.express as px
import plotly.figure_factory as ff
import base64

# Cache the data loading and processing function
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)
    data['geometry'] = data['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(data, geometry='geometry')
    gdf.set_crs(epsg=4326, inplace=True)  # Set CRS to WGS84
    return gdf

# Load and process the data
lila_data_path = 'LILAZones_geo.csv'
gdf_lila = load_data(lila_data_path)

supermarket_data_path = "supermarkets.csv"
gdf_supermarkets = load_data(supermarket_data_path)

fast_food_data_path = "Fast Food Restaurants.csv"
gdf_fast_food = load_data(fast_food_data_path)

# Function to create a folium map for a given year and optionally filter by rank
def create_map(gdf, year, coverage_ratio_col, rank_col, selected_rank=None, legend_name="Coverage Ratio"):
    # Create a base map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)  # Centered around New York
    
    # Check if columns exist
    if coverage_ratio_col not in gdf.columns or rank_col not in gdf.columns:
        st.error(f"Column '{coverage_ratio_col}' or '{rank_col}' does not exist in the data.")
        return m
    
    # Filter GeoDataFrame if a specific rank is selected
    gdf_filtered = gdf.copy()
    if selected_rank and selected_rank != 'All':
        gdf_filtered = gdf_filtered[gdf_filtered[rank_col] == selected_rank]
    
    folium.Choropleth(
        geo_data=gdf_filtered,
        name='choropleth',
        data=gdf_filtered,
        columns=['TRACTCE', coverage_ratio_col],
        key_on='feature.properties.TRACTCE',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name
    ).add_to(m)
    
    # Add tooltips
    folium.GeoJson(
        gdf_filtered,
        style_function=lambda x: {'fillColor': '#ffffff00', 'color': '#00000000', 'weight': 0},
        tooltip=folium.GeoJsonTooltip(
            fields=['TRACTCE', coverage_ratio_col, rank_col],
            aliases=['Census Tract Area', f'{year} {legend_name}', 'Rank'],
            localize=True
        )
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

# Function to display tooltip info in a styled format
def display_tooltip_info(gdf_filtered, year, coverage_ratio_col):
    if not gdf_filtered.empty:
        for _, row in gdf_filtered.iterrows():
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius: 10px; padding: 10px; margin: 10px 0; background-color: #f9f9f9;">
                    <h4 style="color: #2E7D32;">Census Tract Area: {row['TRACTCE']}</h4>
                    <p><span style="color: #D32F2F;">{year}: </span>{row[coverage_ratio_col]}</p>
                    <p><span style="color: #1976D2;">Rank: </span>{row[f'{year}_rank']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# Main function to create the app
def main():
    st.sidebar.title("Navigation")
    page_icons = {
        "Home": "🏠",
        "Data Analysis": "📊",
        "Data Visualization": "📈",
        "Comments": "💬",
        "Guide": "📖"
    }

    pages = ["Home", "Data Analysis", "Data Visualization", "Comments", "Guide"]
    selection = st.sidebar.radio("Go to", pages, format_func=lambda page: f"{page_icons[page]} {page}")

    st.title(selection)

    if selection == "Home":
        st.write("Welcome to the Food Desert Analysis App")
        st.write("This app helps to analyze food desert regions in Brooklyn.")
    
    elif selection == "Data Analysis":
        # Load the datasets for analysis
        socioeconomics_df = pd.read_csv('dataset_socioeconomics.csv')
        convStores_df = pd.read_csv('dataset_convStores.csv')
        eating_df = pd.read_csv('dataset_eating.csv')
        corrPlot_df = pd.read_csv('dataset_forCorrPlot.csv')

        # Interactive Data Analysis Page
        st.title("Interactive Data Analysis Page")

        # 1. Family Income vs Race (2016-2020)
        st.header("Family Income vs Race (2016-2020)")
        races = socioeconomics_df.columns
        selected_races = st.multiselect('Select races to display', races, default=races)
        filtered_income_df = socioeconomics_df[selected_races]
        fig1 = px.box(filtered_income_df, 
                     labels={'value': 'Family Income', 'variable': 'Race'},
                     title='Family Income vs Race (2016-2020)')
        st.plotly_chart(fig1)
        st.markdown("""
        #### Explanation:
        This boxplot visualizes the distribution of family incomes across different racial groups between 2016 and 2020. Each box represents the interquartile range (IQR), showing the median and spread of the data. The whiskers indicate variability outside the upper and lower quartiles, while points beyond the whiskers are outliers. This visualization helps in identifying income disparities among various racial groups.
        """)

        # 2. Employment in Convenience Stores Over Time
        st.header("Employment in Convenience Stores Over Time")
        years = convStores_df['year'].unique()
        selected_years = st.slider('Select years', min_value=int(years.min()), max_value=int(years.max()), value=(int(years.min()), int(years.max())))
        filtered_convStores_df = convStores_df[(convStores_df['year'] >= selected_years[0]) & (convStores_df['year'] <= selected_years[1])]
        fig2 = px.line(filtered_convStores_df, x='year', y=['count_emp_4453', 'count_emp_453991', 'count_emp_445120'],
                      labels={'value': 'Employment Count', 'year': 'Year'},
                      title='Employment in Convenience Stores Over Time')
        st.plotly_chart(fig2)
        st.markdown("""
        #### Explanation:
        This line chart illustrates the trends in employment across different types of stores, including convenience stores, other general stores, and grocery stores over several years. The x-axis represents the years, while the y-axis represents the count of employees. The lines demonstrate how employment levels have changed over time, helping to identify growth or decline trends in these sectors.
        """)

        # 3. Employment in Eating Establishments Over Time
        st.header("Employment in Eating Establishments Over Time")
        years = eating_df['year'].unique()
        selected_years = st.slider('Select years', min_value=int(years.min()), max_value=int(years.max()), value=(int(years.min()), int(years.max())))
        filtered_eating_df = eating_df[(eating_df['year'] >= selected_years[0]) & (eating_df['year'] <= selected_years[1])]
        fig3 = px.line(filtered_eating_df, x='year', y=['count_emp_722511', 'count_emp_722513', 'count_emp_722515', 'count_emp_722410'],
                      labels={'value': 'Employment Count', 'year': 'Year'},
                      title='Employment in Eating Establishments Over Time')
        st.plotly_chart(fig3)
        st.markdown("""
        #### Explanation:
        This line chart displays employment trends in various eating establishments, such as full-service restaurants, limited-service restaurants, snack and nonalcoholic beverage bars, and caterers over time. The x-axis denotes the years, and the y-axis indicates the count of employees. This plot helps in understanding how employment in different types of eating establishments has evolved, highlighting periods of growth or decline.
        """)

        # 4. Correlation Heatmap
        st.header("Correlation Heatmap")
        columns = corrPlot_df.columns
        selected_columns = st.multiselect('Select columns for correlation', columns, default=columns)
        filtered_corr_df = corrPlot_df[selected_columns]
        corr = filtered_corr_df.corr()
        fig4 = ff.create_annotated_heatmap(
            z=corr.values,
            x=list(corr.columns),
            y=list(corr.index),
            annotation_text=corr.round(2).values,
            colorscale='Viridis'
        )
        st.plotly_chart(fig4)
        st.markdown("""
        #### Explanation:
        This correlation heatmap visualizes the relationships between different variables in the dataset. Each cell in the heatmap shows the correlation coefficient between two variables, with colors representing the strength and direction of the correlation. Positive correlations are shown in one color gradient, while negative correlations are in another. This plot is useful for identifying which variables are strongly related, aiding in data analysis and decision-making.
        """)

    elif selection == "Data Visualization":
        # Map selection using tabs
        tabs = st.tabs(["LILA & Non-LILA Zones", "Supermarket Coverage Ratio", "Fast Food Coverage Ratio"])

        with tabs[0]:
            st.header("LILA & Non-LILA Zones")

            # Initial filter
            nta_options = ["All"] + gdf_lila['NTA Name'].unique().tolist()
            nta_selected = st.selectbox("Search for NTA Name:", nta_options)

            # Filter the GeoDataFrame based on the selected NTA Name
            if nta_selected != "All":
                filtered_gdf = gdf_lila[gdf_lila['NTA Name'] == nta_selected]
            else:
                filtered_gdf = gdf_lila

            # Census Tract Area filter based on the filtered GeoDataFrame
            tract_options = ["All"] + filtered_gdf['Census Tract Area'].unique().tolist()
            tract_selected = st.selectbox("Search for Census Tract Area:", tract_options)

            # Update the filtering logic to highlight the selected Census Tract Area
            if tract_selected != "All":
                filtered_gdf = gdf_lila[gdf_lila['Census Tract Area'] == tract_selected]
                # Ensure NTA dropdown is updated according to selected Census Tract Area
                nta_options = ["All"] + filtered_gdf['NTA Name'].unique().tolist()
                nta_selected = nta_options[1] if nta_selected == "All" else nta_selected
            elif nta_selected != "All":
                filtered_gdf = gdf_lila[gdf_lila['NTA Name'] == nta_selected]
            else:
                filtered_gdf = gdf_lila

            m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
            folium.GeoJson(
                filtered_gdf,
                style_function=lambda feature: {
                    'fillColor': 'red',
                    'color': 'red',
                    'weight': 1,
                    'fillOpacity': 0.6,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['Census Tract Area', 'NTA Name', 'Food Index', ' Median Family Income ', 'Education below high school diploma (Poverty Rate)', 'SNAP Benefits %'],
                    aliases=['Census Tract Area:', 'NTA Name:', 'Food Index:', 'Median Family Income:', 'Poverty Rate:', 'SNAP Benefits:'],
                    localize=True
                )
            ).add_to(m)
            folium_static(m, width=800, height=600)

            def display_info(details):
                for i, row in details.iterrows():
                    st.markdown(f"""
                        <div style="border: 2px solid #ddd; border-radius: 10px; padding: 20px; margin: 20px 0; background-color: #f9f9f9;">
                            <h4 style="color: #2E8B57;">{row['NTA Name']} - Census Tract Area: {row['Census Tract Area']}</h4>
                            <p><strong style="color: #FF6347;">Food Index:</strong> {row['Food Index']}</p>
                            <p><strong style="color: #4682B4;">Median Family Income:</strong> {row[' Median Family Income ']}</p>
                            <p><strong style="color: #8A2BE2;">Poverty Rate:</strong> {row['Education below high school diploma (Poverty Rate)']}</p>
                            <p><strong style="color: #DAA520;">SNAP Benefits:</strong> {row['SNAP Benefits %']}</p>
                        </div>
                    """, unsafe_allow_html=True)

            if nta_selected != "All":
                if tract_selected == "All":
                    details = filtered_gdf[['NTA Name', 'Census Tract Area', 'Food Index', ' Median Family Income ', 'Education below high school diploma (Poverty Rate)', 'SNAP Benefits %']]
                    st.subheader(f"Details for {nta_selected}")
                    display_info(details)
                else:
                    details = filtered_gdf[['NTA Name', 'Census Tract Area', 'Food Index', ' Median Family Income ', 'Education below high school diploma (Poverty Rate)', 'SNAP Benefits %']]
                    display_info(details)

        with tabs[1]:
            st.header("Supermarket Coverage Ratio")
            
            # Add a select slider for the years
            years = list(range(2003, 2018))  # Adjust this range based on your data
            year = st.select_slider(
                "Select Year",
                options=years,
                value=min(years),
                format_func=lambda x: f"{x}",
                key="supermarket_year_slider"
            )

            # Add a select box for Rank search
            rank_options = ['All'] + sorted([rank for rank in gdf_supermarkets[f'{year}_rank'].dropna().unique() if rank.isdigit()], key=int)
            selected_rank = st.selectbox(f"Select a Rank for the year {year} or 'All':", rank_options, key="supermarket_rank_select")

            # Create and display the map
            m = create_map(gdf_supermarkets, year, f'{year}_supermarket coverage ratio', f'{year}_rank', selected_rank, "Supermarket Coverage Ratio")
            folium_static(m)

            # Display the tooltip information below the map if a specific rank is selected
            if selected_rank != 'All':
                filtered_gdf = gdf_supermarkets[gdf_supermarkets[f'{year}_rank'] == selected_rank]
                display_tooltip_info(filtered_gdf, year, f'{year}_supermarket coverage ratio')

        with tabs[2]:
            st.header("Fast Food Coverage Ratio")
            
            # Add a select slider for the years
            years = list(range(2003, 2018))  # Adjust this range based on your data
            year = st.select_slider(
                "Select Year",
                options=years,
                value=min(years),
                format_func=lambda x: f"{x}",
                key="fast_food_year_slider"
            )

            # Add a select box for Rank search
            rank_options = ['All'] + sorted([rank for rank in gdf_fast_food[f'{year}_rank'].dropna().unique() if rank.isdigit()], key=int)
            selected_rank = st.selectbox(f"Select a Rank for the year {year} or 'All':", rank_options, key="fast_food_rank_select")

            # Create and display the map
            m = create_map(gdf_fast_food, year, f'{year}_Fast Food Coverage Ratio', f'{year}_rank', selected_rank, "Fast Food Coverage Ratio")
            folium_static(m)

            # Display the tooltip information below the map if a specific rank is selected
            if selected_rank != 'All':
                filtered_gdf = gdf_fast_food[gdf_fast_food[f'{year}_rank'] == selected_rank]
                display_tooltip_info(filtered_gdf, year, f'{year}_Fast Food Coverage Ratio')

        # Share App button with Gmail link
        share_text = "Check out this Food Desert Analysis App!"
        app_link = "https://samplefooddesert01.streamlit.app/"
        mailto_link = f"mailto:?subject=Food Desert Analysis App&body={share_text}%0A{app_link}"
        st.sidebar.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color:green;color:white;border:none;padding:10px 20px;text-align:center;text-decoration:none;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer;">Share App via Email</button></a>', unsafe_allow_html=True)

        # Download CSV button
        csv = gdf_lila.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="LILAZones_geo.csv"><button style="background-color:blue;color:white;border:none;padding:10px 20px;text-align:center;text-decoration:none;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer;">Download CSV</button></a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)

    elif selection == "Comments":
        st.write("Leave your comments here:")
        st.text_area("Comments:")

    elif selection == "Guide":
        st.write("How to use the app content goes here.")

if __name__ == "__main__":
    main()

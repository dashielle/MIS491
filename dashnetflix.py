%%writefile streamlit_app.py
import streamlit as st

# Maximize the whole screen
st.set_page_config(layout="wide")


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import textwrap
import pycountry
import plotly.express as px

# Add the title at the beginning of your script
st.title("Netflix Content Analysis") 


# Load and preprocess data
df = pd.read_csv('netflix_titles.csv')
df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce') # or errors='coerce' if you prefer to handle error by dropping
df['year_added'] = df['date_added'].dt.year
df['month_added'] = df['date_added'].dt.month

# Genre extractor function
def extract_genres(genre_series):
    genres = genre_series.dropna().str.split(', ')
    return Counter([genre for sublist in genres for genre in sublist])

# Function to get alpha-3 country code
def get_alpha3_code(country_name):
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        return country.alpha_3
    except LookupError:
        return None

# Setup for plots
sns.set(style='whitegrid')

# Sidebar filter
st.sidebar.header("Filter by Year")
all_years = sorted(df['year_added'].dropna().astype(int).unique(), reverse=True) # Fix here
selected_year = st.sidebar.selectbox("Select Year", ["All"] + list(all_years)) # Fix here


# Filter data based on selected year
if selected_year != "All":
    df_filtered = df[df['year_added'] == selected_year]
else:
    df_filtered = df

# Filter movies and TV shows
movies_filtered = df_filtered[df_filtered['type'] == 'Movie']
tv_shows_filtered = df_filtered[df_filtered['type'] == 'TV Show']

# --- Main Layout with Columns ---
col1, col2, col3 = st.columns([1, 2, 1])

# Column 1: Content Breakdown and Genre
with col1:
    st.header("Content Breakdown & Genre")
    st.subheader("Type Breakdown")
    fig_type, ax_type = plt.subplots(figsize=(6, 6))
    df_filtered['type'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#ff6f61', '#6b5b95' ], startangle=90, ax=ax_type)
    ax_type.set_title('Movies vs TV Shows')
    ax_type.set_ylabel('')
    st.pyplot(fig_type)

    st.subheader("Top Movie Genres")
    movie_genres = extract_genres(movies_filtered['listed_in']).most_common(10)
    fig_movie_genres, ax_movie_genres = plt.subplots(figsize=(8, 5))
    sns.barplot(x=[genre for genre, _ in movie_genres],
                y=[count for _, count in movie_genres],
                color="#ff6f61", ax=ax_movie_genres)
    ax_movie_genres.set_title('Top 10 Movie Genres')
    labels = [textwrap.fill(genre, 15) for genre, _ in movie_genres]
    ax_movie_genres.set_xticklabels(labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(fig_movie_genres)

    st.subheader("Top TV Show Genres")
    tv_genres = extract_genres(tv_shows_filtered['listed_in']).most_common(10)
    fig_tv_genres, ax_tv_genres = plt.subplots(figsize=(8, 5))
    sns.barplot(x=[genre for genre, _ in tv_genres],
                y=[count for _, count in tv_genres],
                color= "#6b5b95", ax=ax_tv_genres)
    ax_tv_genres.set_title('Top 10 TV Show Genres')
    labels = [textwrap.fill(genre, 15) for genre, _ in tv_genres]
    ax_tv_genres.set_xticklabels(labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(fig_tv_genres)

# Column 2: Geographical Analysis
with col2:
    st.header("Geographical Analysis")
    st.subheader("Content Contribution by Country")
    # Count country appearances
    all_countries = Counter(
        country.strip()
        for countries in df_filtered['country'].dropna().str.split(', ')
        for country in countries
    )

    # Convert to DataFrame
    country_counts_df = pd.DataFrame(all_countries.items(), columns=['country', 'count'])

    # Get alpha-3 codes for mapping
    country_counts_df['alpha_3'] = country_counts_df['country'].apply(get_alpha3_code)
    country_counts_df = country_counts_df.dropna(subset=['alpha_3'])

    fig_map = px.choropleth(country_counts_df,
                            locations='alpha_3',
                            color='count',
                            hover_name='country',
                            color_continuous_scale=px.colors.sequential.Plasma,
                            title='Content Contribution by Country',
                            labels={'count': 'Number of Titles'},
                            projection='natural earth')
    st.plotly_chart(fig_map)

    st.subheader("Top Genres in the United States")
    us_data = df_filtered[df_filtered['country'].str.contains('United States', na=False)]
    if not us_data.empty:
        us_genres = extract_genres(us_data['listed_in']).most_common(10)
        fig_us_genres, ax_us_genres = plt.subplots(figsize=(8, 5))
        sns.barplot(x=[genre for genre, _ in us_genres], y=[count for _, count in us_genres], color="lightblue", ax=ax_us_genres)
        ax_us_genres.set_title('Top 10 Genres in the US')
        labels = [textwrap.fill(genre, 15) for genre, _ in us_genres]
        ax_us_genres.set_xticklabels(labels, rotation=90, ha='center')
        plt.tight_layout()
        st.pyplot(fig_us_genres)
    else:
        st.info("No data available for the United States in the selected year.")

# Column 3: Analysis and Ratings
with col3:
    st.header("Analysis & Ratings")
    st.subheader("Titles Added Per Year")
    fig_year_added, ax_year_added = plt.subplots(figsize=(10, 5))
    df_filtered['year_added'].value_counts().sort_index().plot(kind='line',  marker='o', markerfacecolor='blue', markeredgecolor='skyblue', ax=ax_year_added)
    ax_year_added.set_title('Titles Added Per Year')
    ax_year_added.set_xlabel('Year')
    ax_year_added.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig_year_added)

    # Extract duration in minutes, handling NaNs
    movies_filtered['duration_minutes'] = pd.to_numeric(movies_filtered['duration'].str.extract(r'(\d+)', expand=False), errors='coerce').astype('Int64')

    # Group by genre and calculate average duration
    genre_duration = movies_filtered.groupby('listed_in')['duration_minutes'].mean().reset_index()

    # Sort by average duration and select top 5 for better visibility in a column
    genre_duration = genre_duration.sort_values(by='duration_minutes', ascending=False).head(5)

    st.subheader("Avg Movie Duration by Genre (Top 5)")
    fig_duration, ax_duration = plt.subplots(figsize=(8, 5))

    # Use plot for line graph instead of sns.barplot
    ax_duration.plot(genre_duration['listed_in'], genre_duration['duration_minutes'], marker='o', linestyle='-', color='orange') 

    ax_duration.set_title('Avg Movie Duration by Genre (Top 5)')
    ax_duration.set_xlabel('Genre')
    ax_duration.set_ylabel('Average Duration (minutes)')
    labels = [textwrap.fill(genre, 10) for genre in genre_duration['listed_in']]
    ax_duration.set_xticklabels(labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(fig_duration)

    st.subheader("Top Content Ratings")
    fig_ratings, ax_ratings = plt.subplots(figsize=(8, 5))
    df_filtered['rating'].value_counts().head(10).plot(kind='bar', color='#88b04b', ax=ax_ratings)
    ax_ratings.set_title('Top 10 Ratings')
    ax_ratings.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig_ratings)



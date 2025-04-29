import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import streamlit as st
import textwrap
import pycountry
import plotly.express as px

# Maximize the whole screen
st.set_page_config(layout="wide")

# Load and preprocess
df = pd.read_csv('netflix_titles.csv')
df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
df['year_added'] = df['date_added'].dt.year
df['month_added'] = df['date_added'].dt.month

movies = df[df['type'] == 'Movie'].copy()
tv_shows = df[df['type'] == 'TV Show'].copy()

# Genre extractor
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

# Sidebar for year selection
st.sidebar.header("Filter by Year")
years = sorted(df['year_added'].dropna().unique().astype(int), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", ["All"] + list(years))

# Filter DataFrame based on selected year
if selected_year != "All":
    df_filtered = df[df['year_added'] == selected_year]
    movies_filtered = movies[movies['year_added'] == selected_year]
    tv_shows_filtered = tv_shows[tv_shows['year_added'] == selected_year]
else:
    df_filtered = df
    movies_filtered = movies
    tv_shows_filtered = tv_shows

# --- Main Layout with Columns ---
col1, col2, col3 = st.columns([1, 1, 1])

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
    ax_movie_genres.set_xticklabels(labels, rotation=45, ha='right')
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
    ax_tv_genres.set_xticklabels(labels, rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig_tv_genres)

# Column 2: Geographical Analysis
# --- Main Layout with Columns ---
st.header("Geographical Analysis")
col_map, col_genres = st.columns([2, 3])

with col_map:
    st.subheader("Content Contribution by Country")
    # Count country appearances
    country_counts = Counter(
        country.strip()
        for countries in df_filtered['country'].dropna().str.split(', ')
        for country in countries
    )

    country_df = pd.DataFrame(country_counts.items(), columns=['country', 'count'])
    country_df['alpha_3'] = country_df['country'].apply(get_alpha3_code)
    country_df = country_df.dropna(subset=['alpha_3'])

    fig_map = px.choropleth(country_df,
                            locations='alpha_3',
                            color='count',
                            hover_name='country',
                            color_continuous_scale=px.colors.sequential.Plasma,
                            title='Content Contribution by Country',
                            labels={'count': 'Number of Titles'}, # Add legend label
                            projection='natural earth') # Improved projection
    st.plotly_chart(fig_map)

    def handle_country_click(event):
        if event['points']:
            clicked_country = event['points'][0]['hovertext']
            st.session_state['selected_country'] = clicked_country

    fig_map.data[0].on_click(handle_country_click)

with col_genres:
    st.subheader("Top Genres by Country")
    selected_country = st.session_state.get('selected_country')

    if selected_country:
        country_data = df_filtered[df_filtered['country'].str.contains(selected_country, na=False)]
        if not country_data.empty:
            col_tv, col_movie = st.columns(2)

            with col_tv:
                st.subheader(f"Top TV Show Genres in {selected_country}")
                country_tv_shows = country_data[country_data['type'] == 'TV Show']
                if not country_tv_shows.empty:
                    tv_genres_country = extract_genres(country_tv_shows['listed_in']).most_common(10)
                    if tv_genres_country:
                        fig_tv_country, ax_tv_country = plt.subplots(figsize=(8, 5))
                        sns.barplot(x=[genre for genre, _ in tv_genres_country], y=[count for _, count in tv_genres_country], color="lightcoral", ax=ax_tv_country)
                        ax_tv_country.set_title(f'Top 10 TV Show Genres in {selected_country}')
                        labels_tv = [textwrap.fill(genre, 15) for genre, _ in tv_genres_country]
                        ax_tv_country.set_xticklabels(labels_tv, rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig_tv_country)
                    else:
                        st.info(f"No TV show genre data available for {selected_country}.")
                else:
                    st.info(f"No TV shows available in {selected_country}.")

            with col_movie:
                st.subheader(f"Top Movie Genres in {selected_country}")
                country_movies = country_data[country_data['type'] == 'Movie']
                if not country_movies.empty:
                    movie_genres_country = extract_genres(country_movies['listed_in']).most_common(10)
                    if movie_genres_country:
                        fig_movie_country, ax_movie_country = plt.subplots(figsize=(8, 5))
                        sns.barplot(x=[genre for genre, _ in movie_genres_country], y=[count for _, count in movie_genres_country], color="lightskyblue", ax=ax_movie_country)
                        ax_movie_country.set_title(f'Top 10 Movie Genres in {selected_country}')
                        labels_movie = [textwrap.fill(genre, 15) for genre, _ in movie_genres_country]
                        ax_movie_country.set_xticklabels(labels_movie, rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig_movie_country)
                    else:
                        st.info(f"No movie genre data available for {selected_country}.")
                else:
                    st.info(f"No movies available in {selected_country}.")

        else:
            st.info(f"No data available for {selected_country} in the selected year.")
    else:
        st.info("Click on a country on the map to see its top TV show and movie genres.")

# --- Remaining Columns ---
col_temp, col_ratings = st.columns(2)

with col_temp:
    st.header("Temporal Analysis")
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
    sns.barplot(x='listed_in', y='duration_minutes', data=genre_duration, color='orange', ax=ax_duration)
    ax_duration.set_title('Avg Movie Duration by Genre (Top 5)')
    ax_duration.set_xlabel('Genre')
    ax_duration.set_ylabel('Average Duration (minutes)')
    labels = [textwrap.fill(genre, 10) for genre in genre_duration['listed_in']]
    ax_duration.set_xticklabels(labels, rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig_duration)

with col_ratings:
    st.header("Ratings Analysis")
    st.subheader("Top Content Ratings")
    fig_ratings, ax_ratings = plt.subplots(figsize=(8, 5))
    df_filtered['rating'].value_counts().head(10).plot(kind='bar', color='#88b04b', ax=ax_ratings)
    ax_ratings.set_title('Top 10 Ratings')
    ax_ratings.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig_ratings)
# Column 3: Temporal Analysis and Ratings
with col3:
    st.header("Temporal Analysis & Ratings")
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
    sns.barplot(x='listed_in', y='duration_minutes', data=genre_duration, color='orange', ax=ax_duration)
    ax_duration.set_title('Avg Movie Duration by Genre (Top 5)')
    ax_duration.set_xlabel('Genre')
    ax_duration.set_ylabel('Average Duration (minutes)')
    labels = [textwrap.fill(genre, 10) for genre in genre_duration['listed_in']]
    ax_duration.set_xticklabels(labels, rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig_duration)

    st.subheader("Top Content Ratings")
    fig_ratings, ax_ratings = plt.subplots(figsize=(8, 5))
    df_filtered['rating'].value_counts().head(10).plot(kind='bar', color='#88b04b', ax=ax_ratings)
    ax_ratings.set_title('Top 10 Ratings')
    ax_ratings.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig_ratings)

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

    # Top N countries + combine others
    top_n = 10
    top_countries = country_counts_df.sort_values(by='count', ascending=False).head(top_n)
    other_count = country_counts_df['count'].sum() - top_countries['count'].sum()

    # Add 'Other' slice
    top_countries = pd.concat([
        top_countries,
        pd.DataFrame([{'country': 'Other', 'count': other_count}])
    ])

    # Plot pie chart
    fig_country_pie, ax_country_pie = plt.subplots(figsize=(8, 8))
    ax_country_pie.pie(top_countries['count'], labels=top_countries['country'], autopct='%1.1f%%',
                        startangle=75, colors=sns.color_palette('pastel'))
    ax_country_pie.set_title('Content Contribution by Country (Top {})'.format(top_n))
    plt.tight_layout()
    st.pyplot(fig_country_pie)


    def get_alpha3_code(country_name):
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        return country.alpha_3
    except LookupError:
        return None

st.subheader("Content Contribution by Country")
# Count country appearances
all_countries = Counter(
    country.strip()
    for countries in df_filtered['country'].dropna().str.split(', ')
    for country in countries
)

# Convert to DataFrame
country_counts_df = pd.DataFrame(all_countries.items(), columns=['country', 'count'])
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
        ax_us_genres.set_xticklabels(labels, rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig_us_genres)
    else:
        st.info("No data available for the United States in the selected year.")

# Column 3: Temporal Analysis and Ratings
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

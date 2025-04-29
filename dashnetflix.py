import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import streamlit as st
import textwrap

# Maximize the screen layout
st.set_page_config(page_title="Netflix Dashboard", layout="wide")

# Title and subtitle
st.title("🎬 Netflix Content Dashboard")
st.markdown("Analyze Netflix content by type, geography, genre, and more.")

# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv('netflix_titles.csv')
    df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
    df['year_added'] = df['date_added'].dt.year
    df['month_added'] = df['date_added'].dt.month
    return df

df = load_data()

movies = df[df['type'] == 'Movie'].copy()
tv_shows = df[df['type'] == 'TV Show'].copy()

# Sidebar Year Filter
st.sidebar.header("📅 Filter by Year of Addition")
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

# Genre extraction helper
def extract_genres(genre_series):
    genres = genre_series.dropna().str.split(', ')
    return Counter([genre for sublist in genres for genre in sublist])

# Seaborn theme
sns.set(style='whitegrid')

# --- Layout with 2 Custom Columns ---
col1, col2 = st.columns([1, 2])  # 1/3 and 2/3 screen ratio

# Column 1: Type Breakdown, Yearly Trends, Ratings
with col1:
    st.header("📊 Breakdown & Ratings")

    st.subheader("Type Breakdown")
    fig_type, ax_type = plt.subplots(figsize=(6, 6))
    df_filtered['type'].value_counts().plot(kind='pie', autopct='%1.1f%%',
                                            colors=['#ff6f61', '#6b5b95'],
                                            startangle=90, ax=ax_type)
    ax_type.set_title('Movies vs TV Shows')
    ax_type.set_ylabel('')
    st.pyplot(fig_type)

    st.subheader("Titles Added Per Year")
    fig_year, ax_year = plt.subplots(figsize=(6, 4))
    df_filtered['year_added'].value_counts().sort_index().plot(kind='line',
        marker='o', ax=ax_year, color='darkred')
    ax_year.set_title("Titles Added Over Time")
    ax_year.set_xlabel("Year")
    ax_year.set_ylabel("Count")
    st.pyplot(fig_year)

    st.subheader("Top Content Ratings")
    fig_ratings, ax_ratings = plt.subplots(figsize=(6, 4))
    df_filtered['rating'].value_counts().head(10).plot(kind='bar',
        color='#88b04b', ax=ax_ratings)
    ax_ratings.set_title("Top 10 Ratings")
    ax_ratings.set_ylabel("Count")
    st.pyplot(fig_ratings)

    st.subheader("Avg Movie Duration by Genre (Top 5)")
    movies_filtered['duration_minutes'] = pd.to_numeric(
        movies_filtered['duration'].str.extract(r'(\d+)', expand=False),
        errors='coerce'
    ).astype('Int64')

    genre_duration = movies_filtered.groupby('listed_in')['duration_minutes'].mean().reset_index()
    genre_duration = genre_duration.sort_values(by='duration_minutes', ascending=False).head(5)

    fig_duration, ax_duration = plt.subplots(figsize=(6, 4))
    sns.barplot(x='listed_in', y='duration_minutes', data=genre_duration,
                color='orange', ax=ax_duration)
    ax_duration.set_title("Avg Duration by Genre (Top 5)")
    ax_duration.set_xlabel("Genre")
    ax_duration.set_ylabel("Avg Duration (min)")
    labels = [textwrap.fill(genre, 12) for genre in genre_duration['listed_in']]
    ax_duration.set_xticklabels(labels, rotation=45, ha='right')
    st.pyplot(fig_duration)

# Column 2: Geographical & Genre Analysis
with col2:
    st.header("🌍 Geographical & Genre Insights")

    st.subheader("Content Contribution by Country")
    all_countries = Counter(
        country.strip()
        for countries in df_filtered['country'].dropna().str.split(', ')
        for country in countries
    )

    country_df = pd.DataFrame(all_countries.items(), columns=['country', 'count'])
    top_n = 10
    top_countries = country_df.sort_values(by='count', ascending=False).head(top_n)
    other_count = country_df['count'].sum() - top_countries['count'].sum()
    top_countries = pd.concat([
        top_countries,
        pd.DataFrame([{'country': 'Other', 'count': other_count}])
    ])

    fig_country, ax_country = plt.subplots(figsize=(8, 6))
    ax_country.pie(top_countries['count'], labels=top_countries['country'],
                   autopct='%1.1f%%', startangle=75,
                   colors=sns.color_palette('pastel'))
    ax_country.set_title("Top Countries Producing Content")
    st.pyplot(fig_country)

    st.subheader("Top Genres in the United States")
    us_data = df_filtered[df_filtered['country'].str.contains('United States', na=False)]
    if not us_data.empty:
        us_genres = extract_genres(us_data['listed_in']).most_common(10)
        fig_us, ax_us = plt.subplots(figsize=(8, 4))
        sns.barplot(x=[genre for genre, _ in us_genres],
                    y=[count for _, count in us_genres],
                    color="lightblue", ax=ax_us)
        ax_us.set_title("Top 10 Genres in the US")
        labels = [textwrap.fill(genre, 15) for genre, _ in us_genres]
        ax_us.set_xticklabels(labels, rotation=45, ha='right')
        st.pyplot(fig_us)
    else:
        st.info("No data for the United States in the selected year.")

    st.subheader("Top Movie Genres")
    movie_genres = extract_genres(movies_filtered['listed_in']).most_common(10)
    fig_mg, ax_mg = plt.subplots(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in movie_genres],
                y=[count for _, count in movie_genres],
                color="#ff6f61", ax=ax_mg)
    ax_mg.set_title("Top 10 Movie Genres")
    labels = [textwrap.fill(genre, 15) for genre, _ in movie_genres]
    ax_mg.set_xticklabels(labels, rotation=45, ha='right')
    st.pyplot(fig_mg)

    st.subheader("Top TV Show Genres")
    tv_genres = extract_genres(tv_shows_filtered['listed_in']).most_common(10)
    fig_tv, ax_tv = plt.subplots(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in tv_genres],
                y=[count for _, count in tv_genres],
                color="#6b5b95", ax=ax_tv)
    ax_tv.set_title("Top 10 TV Show Genres")
    labels = [textwrap.fill(genre, 15) for genre, _ in tv_genres]
    ax_tv.set_xticklabels(labels, rotation=45, ha='right')
    st.pyplot(fig_tv)

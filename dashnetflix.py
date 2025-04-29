import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from collections import Counter
import textwrap

# Maximize layout
st.set_page_config(layout="wide")
sns.set(style='whitegrid')

# Load and preprocess
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

# Genre extractor
def extract_genres(series):
    genres = series.dropna().str.split(', ')
    return Counter([genre for sublist in genres for genre in sublist])

# Sidebar
st.sidebar.header("📅 Filter by Year")
years = sorted(df['year_added'].dropna().unique().astype(int), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", ["All"] + list(years))

if selected_year != "All":
    df_filtered = df[df['year_added'] == selected_year]
    movies_filtered = movies[movies['year_added'] == selected_year]
    tv_shows_filtered = tv_shows[tv_shows['year_added'] == selected_year]
else:
    df_filtered = df
    movies_filtered = movies
    tv_shows_filtered = tv_shows

# Layout: Left = 1/3, Right = 2/3
left_col, right_col = st.columns([1, 2])

# --- LEFT COLUMN: Type Breakdown, Ratings ---
with left_col:
    st.header("🎬 Content Breakdown & Ratings")

    # Type Breakdown Pie
    st.subheader("Type Breakdown")
    fig_type, ax_type = plt.subplots(figsize=(6, 6))
    df_filtered['type'].value_counts().plot(
        kind='pie',
        autopct='%1.1f%%',
        colors=['#ff6f61', '#6b5b95'],
        startangle=90,
        ax=ax_type
    )
    ax_type.set_ylabel('')
    st.pyplot(fig_type)

    # Ratings Bar
    st.subheader("Top Content Ratings")
    fig_ratings, ax_ratings = plt.subplots(figsize=(6, 4))
    df_filtered['rating'].value_counts().head(10).plot(kind='bar', color='#88b04b', ax=ax_ratings)
    ax_ratings.set_ylabel('Count')
    st.pyplot(fig_ratings)

    # Yearly Additions Line Chart
    st.subheader("Titles Added Per Year")
    fig_year, ax_year = plt.subplots(figsize=(6, 4))
    df_filtered['year_added'].value_counts().sort_index().plot(marker='o', ax=ax_year)
    ax_year.set_xlabel('Year')
    ax_year.set_ylabel('Titles Added')
    st.pyplot(fig_year)

# --- RIGHT COLUMN: Geographic & Genre ---
with right_col:
    st.header("🌍 Geographic & Genre Analysis")

    # Country Pie
    st.subheader("Content by Country")
    country_counts = Counter(
        country.strip()
        for countries in df_filtered['country'].dropna().str.split(', ')
        for country in countries
    )
    country_df = pd.DataFrame(country_counts.items(), columns=['country', 'count'])
    top_countries = country_df.sort_values(by='count', ascending=False).head(10)
    other_sum = country_df['count'].sum() - top_countries['count'].sum()
    top_countries = pd.concat([
        top_countries,
        pd.DataFrame([{'country': 'Other', 'count': other_sum}])
    ])
    fig_country, ax_country = plt.subplots(figsize=(7, 6))
    ax_country.pie(top_countries['count'], labels=top_countries['country'],
                   autopct='%1.1f%%', startangle=75,
                   colors=sns.color_palette('pastel'))
    ax_country.set_title('Top 10 Countries by Content')
    st.pyplot(fig_country)

    # Top Genres US
    st.subheader("Top Genres in US")
    us_data = df_filtered[df_filtered['country'].str.contains('United States', na=False)]
    if not us_data.empty:
        us_genres = extract_genres(us_data['listed_in']).most_common(10)
        fig_us, ax_us = plt.subplots(figsize=(7, 4))
        sns.barplot(x=[g for g, _ in us_genres], y=[c for _, c in us_genres], ax=ax_us, color="lightblue")
        ax_us.set_xticklabels([textwrap.fill(g, 15) for g, _ in us_genres], rotation=45, ha='right')
        st.pyplot(fig_us)
    else:
        st.info("No US data available for this year.")

    # Top Movie Genres
    st.subheader("Top 10 Movie Genres")
    movie_genres = extract_genres(movies_filtered['listed_in']).most_common(10)
    fig_mg, ax_mg = plt.subplots(figsize=(7, 4))
    sns.barplot(x=[g for g, _ in movie_genres], y=[c for _, c in movie_genres], color="#ff6f61", ax=ax_mg)
    ax_mg.set_xticklabels([textwrap.fill(g, 15) for g, _ in movie_genres], rotation=45, ha='right')
    st.pyplot(fig_mg)

    # Top TV Show Genres
    st.subheader("Top 10 TV Show Genres")
    tv_genres = extract_genres(tv_shows_filtered['listed_in']).most_common(10)
    fig_tg, ax_tg = plt.subplots(figsize=(7, 4))
    sns.barplot(x=[g for g, _ in tv_genres], y=[c for _, c in tv_genres], color="#6b5b95", ax=ax_tg)
    ax_tg.set_xticklabels([textwrap.fill(g, 15) for g, _ in tv_genres], rotation=45, ha='right')
    st.pyplot(fig_tg)

    # Avg Movie Duration
    st.subheader("Avg Duration by Genre (Top 5)")
    movies_filtered['duration_minutes'] = pd.to_numeric(
        movies_filtered['duration'].str.extract(r'(\d+)', expand=False),
        errors='coerce'
    )
    duration_stats = movies_filtered.groupby('listed_in')['duration_minutes'].mean().reset_index()
    top_duration = duration_stats.sort_values(by='duration_minutes', ascending=False).head(5)
    fig_dur, ax_dur = plt.subplots(figsize=(7, 4))
    sns.barplot(data=top_duration, x='listed_in', y='duration_minutes', color='orange', ax=ax_dur)
    ax_dur.set_xticklabels([textwrap.fill(g, 15) for g in top_duration['listed_in']], rotation=45, ha='right')
    ax_dur.set_ylabel('Avg Duration (min)')
    st.pyplot(fig_dur)

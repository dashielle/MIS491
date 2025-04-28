import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import textwrap
import streamlit as st
import pydeck as pdk

# Load and preprocess
df = pd.read_csv('netflix_titles.csv')
df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
df['year_added'] = df['date_added'].dt.year
df['month_added'] = df['date_added'].dt.month

# Split by type
movies = df[df['type'] == 'Movie'].copy()
tv_shows = df[df['type'] == 'TV Show'].copy()

# Helper to extract genres
def extract_genres(genre_series):
    genres = genre_series.dropna().str.split(', ')
    return Counter([genre for sublist in genres for genre in sublist])

# --- SIDEBAR ---
st.sidebar.title("Filters")

# Year filter
years = df['year_added'].dropna().astype(int).sort_values().unique()
selected_year = st.sidebar.selectbox('Select Year', options=[None] + list(years))

# Content type filter
content_types = ['All', 'Movie', 'TV Show']
selected_type = st.sidebar.radio('Select Content Type', options=content_types)

# Apply filters
filtered_df = df.copy()
if selected_year:
    filtered_df = filtered_df[filtered_df['year_added'] == selected_year]
if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['type'] == selected_type]

# --- PAGE TITLE ---
st.title('🎬 Netflix Content Analysis Dashboard')

# --- 1. Content Overview Section ---
st.header('Content Breakdown')

# Pie Chart: Movies vs TV Shows
st.subheader('Movies vs TV Shows Distribution')
type_counts = filtered_df['type'].value_counts()
fig1, ax1 = plt.subplots(figsize=(6, 6))
ax1.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=90, colors=['#ff6f61', '#6b5b95'])
ax1.set_title('Movies vs TV Shows')
st.pyplot(fig1)

# Top Genres
st.subheader('Top Genres')

movie_genres = extract_genres(filtered_df[filtered_df['type'] == 'Movie']['listed_in']).most_common(10)
tv_genres = extract_genres(filtered_df[filtered_df['type'] == 'TV Show']['listed_in']).most_common(10)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top 10 Movie Genres**")
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in movie_genres], y=[count for _, count in movie_genres], color="#ff6f61", ax=ax2)
    ax2.set_xticklabels([textwrap.fill(genre, 15) for genre, _ in movie_genres], rotation=90)
    st.pyplot(fig2)

with col2:
    st.markdown("**Top 10 TV Show Genres**")
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in tv_genres], y=[count for _, count in tv_genres], color="#6b5b95", ax=ax3)
    ax3.set_xticklabels([textwrap.fill(genre, 15) for genre, _ in tv_genres], rotation=90)
    st.pyplot(fig3)

# Top Ratings
st.subheader('Top Content Ratings')
fig4, ax4 = plt.subplots(figsize=(10, 4))
filtered_df['rating'].value_counts().head(10).plot(kind='bar', color='#88b04b', ax=ax4)
ax4.set_ylabel('Count')
ax4.set_title('Top 10 Ratings')
st.pyplot(fig4)

# --- 2. Temporal Analysis Section ---
st.header('Temporal Trends')

st.subheader('Titles Added Over the Years')
fig5, ax5 = plt.subplots(figsize=(12, 4))
filtered_df['year_added'].value_counts().sort_index().plot(kind='line', marker='o', ax=ax5)
ax5.set_xlabel('Year')
ax5.set_ylabel('Number of Titles')
ax5.set_title('Titles Added Per Year')
st.pyplot(fig5)

# Average Movie Duration by Genre
if selected_type in ['All', 'Movie']:
    st.subheader('Average Movie Duration by Genre (Top 10)')
    movies_filtered = filtered_df[filtered_df['type'] == 'Movie']
    movies_filtered['duration_minutes'] = pd.to_numeric(movies_filtered['duration'].str.extract(r'(\d+)'), errors='coerce')

    genre_duration = movies_filtered.groupby('listed_in')['duration_minutes'].mean().reset_index()
    genre_duration = genre_duration.sort_values(by='duration_minutes', ascending=False).head(10)

    fig6, ax6 = plt.subplots(figsize=(10, 6))
    sns.lineplot(x='listed_in', y='duration_minutes', data=genre_duration, marker='o', ax=ax6)
    ax6.set_xticklabels([textwrap.fill(label, 15) for label in genre_duration['listed_in']], rotation=90)
    ax6.set_title('Average Duration by Genre')
    st.pyplot(fig6)

# --- 3. Geographic Analysis Section ---
st.header('Geographic Analysis')

st.subheader('Content Contribution by Country')

# Country counts
country_counts = Counter(
    country.strip()
    for countries in filtered_df['country'].dropna().str.split(', ')
    for country in countries
)

country_counts_df = pd.DataFrame(country_counts.items(), columns=['country', 'count'])

top_countries = country_counts_df.sort_values(by='count', ascending=False).head(20)

fig7, ax7 = plt.subplots(figsize=(8, 8))
ax7.pie(top_countries['count'], labels=top_countries['country'], autopct='%1.1f%%', startangle=75, colors=sns.color_palette('pastel'))
ax7.set_title('Top 20 Countries by Content')
st.pyplot(fig7)

# Top Genres in the US
st.subheader('Top Genres in the United States')
us_genres = extract_genres(filtered_df[filtered_df['country'].str.contains('United States', na=False)]['listed_in']).most_common(10)

fig8, ax8 = plt.subplots(figsize=(8, 4))
sns.barplot(x=[genre for genre, _ in us_genres], y=[count for _, count in us_genres], color="lightblue", ax=ax8)
ax8.set_xticklabels([textwrap.fill(label, 15) for label, _ in us_genres], rotation=90)
ax8.set_title('Top 10 Genres in the US')
st.pyplot(fig8)

# Top 5 Countries Genre Breakdown
st.subheader('Top Genres by Top 5 Countries')

top5_countries = country_counts_df.sort_values(by='count', ascending=False).head(5)['country']
filtered_top5 = filtered_df[filtered_df['country'].apply(lambda x: any(c in x for c in top5_countries if isinstance(x, str)))]

genre_by_country = {}
for country in top5_countries:
    genre_by_country[country] = extract_genres(filtered_top5[filtered_top5['country'].str.contains(country)]['listed_in'])

genre_by_country_df = pd.DataFrame(genre_by_country).fillna(0).T
top_10_genres = genre_by_country_df.sum().sort_values(ascending=False).head(10).index
genre_by_country_df = genre_by_country_df[top_10_genres]

fig9, ax9 = plt.subplots(figsize=(12, 6))
genre_by_country_df.plot(kind='bar', stacked=True, ax=ax9, colormap='tab20')
ax9.set_title('Top 10 Genres by Top 5 Countries')
ax9.set_ylabel('Number of Titles')
ax9.legend(title='Genre', bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig9)

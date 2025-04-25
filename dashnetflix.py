import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import streamlit as st
import textwrap

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
years = sorted(df['year_added'].dropna().unique(), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", ["All"] + [int(year) for year in years])

# Filter data based on selected year
if selected_year != "All":
    df_filtered = df[df['year_added'] == selected_year].copy()
    movies_filtered = movies[movies['year_added'] == selected_year].copy()
    tv_shows_filtered = tv_shows[tv_shows['year_added'] == selected_year].copy()
else:
    df_filtered = df.copy()
    movies_filtered = movies.copy()
    tv_shows_filtered = tv_shows.copy()

# Create columns
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Content Breakdown")
    # Type count plot
    plt.figure(figsize=(6, 8))
    df_filtered['type'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#ff6f61', '#6b5b95' ], startangle=90)
    plt.title('Movies vs TV Shows')
    plt.ylabel('')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    st.subheader("Top Genres")
    # Genre plots
    movie_genres = extract_genres(movies_filtered['listed_in']).most_common(5)
    tv_genres = extract_genres(tv_shows_filtered['listed_in']).most_common(5)

    # Movie genres
    plt.figure(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in movie_genres],
                y=[count for _, count in movie_genres],
                color="#ff6f61")
    plt.title('Top 5 Movie Genres')
    labels = [textwrap.fill(genre, 15) for genre, _ in movie_genres]
    plt.xticks(range(len(labels)), labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # TV show genres
    plt.figure(figsize=(8, 4))
    sns.barplot(x=[genre for genre, _ in tv_genres],
                y=[count for _, count in tv_genres],
                color= "#6b5b95")
    plt.title('Top 5 TV Show Genres')
    labels = [textwrap.fill(genre, 15) for genre, _ in tv_genres]
    plt.xticks(range(len(labels)), labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    st.subheader("Top Ratings")
    # Ratings
    plt.figure(figsize=(8, 4))
    df_filtered['rating'].value_counts().head(5).plot(kind='bar', color='#88b04b')
    plt.title('Top 5 Ratings')
    plt.ylabel('Count')
    plt.tight_layout()
    st.pyplot(plt.gcf())

with col2:
    st.subheader("Temporal Analysis")
    # Titles per year
    plt.figure(figsize=(10, 4))
    if selected_year == "All":
        df['year_added'].value_counts().sort_index().plot(kind='line',  marker='o', markerfacecolor='blue', markeredgecolor='skyblue')
    else:
        df_filtered['month_added'].value_counts().sort_index().plot(kind='line', marker='o', markerfacecolor='blue', markeredgecolor='skyblue')
        plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        plt.xlabel('Month Added')

    plt.title(f"Titles Added Per {'Month' if selected_year != 'All' else 'Year'}")
    plt.ylabel('Count')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # Extract duration in minutes, handling NaNs
    movies_filtered['duration_minutes'] = pd.to_numeric(movies_filtered['duration'].str.extract(r'(\d+)', expand=False), errors='coerce').astype('Int64')

    # Group by genre and calculate average duration
    genre_duration = movies_filtered.groupby('listed_in')['duration_minutes'].mean().reset_index()

    # Sort by average duration and select top 5
    genre_duration = genre_duration.sort_values(by='duration_minutes', ascending=False).head(5)

    # Create the plot (Line graph)
    plt.figure(figsize=(10, 6))
    sns.lineplot(x='listed_in', y='duration_minutes', data=genre_duration, marker='o', markerfacecolor='blue', markeredgecolor='skyblue')
    plt.title('Average Movie Duration by Genre (Top 5)')
    plt.xlabel('Genre')
    plt.ylabel('Average Duration (minutes)')
    labels = [textwrap.fill(genre, 15) for genre in genre_duration['listed_in']]
    plt.xticks(range(len(labels)), labels, rotation=90, ha='center')
    plt.tight_layout()
    st.pyplot(plt.gcf())

with col3:
    st.subheader("Geographical Analysis")
    # Count country appearances
    all_countries = Counter(
        country.strip()
        for countries in df_filtered['country'].dropna().str.split(', ')
        for country in countries
    )

    # Convert to DataFrame
    country_counts_df = pd.DataFrame(all_countries.items(), columns=['country', 'count'])

    # Top N countries + combine others
    top_n = 5
    top_countries = country_counts_df.sort_values(by='count', ascending=False).head(top_n)
    other_count = country_counts_df['count'].sum() - top_countries['count'].sum()

    # Add 'Other' slice
    top_countries = pd.concat([
        top_countries,
        pd.DataFrame([{'country': 'Other', 'count': other_count}])
    ])

    # Plot pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(top_countries['count'], labels=top_countries['country'], autopct='%1.1f%%',
            startangle=75, colors=sns.color_palette('pastel'))
    plt.title('Content Contribution by Country')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # Top genres in the most contributing country
    if not top_countries.empty and top_countries.iloc[0]['country'] != 'Other':
        most_common_country = top_countries.iloc[0]['country']
        country_genres = extract_genres(df_filtered[df_filtered['country'].str.contains(most_common_country, na=False)]['listed_in']).most_common(5)
        plt.figure(figsize=(8, 4))
        sns.barplot(x=[genre for genre, _ in country_genres], y=[count for _, count in country_genres], color="lightcoral")
        plt.title(f'Top 5 Genres in {most_common_country}')
        labels = [textwrap.fill(genre, 15) for genre, _ in country_genres]
        plt.xticks(range(len(labels)), labels, rotation=90, ha='center')
        plt.tight_layout()
        st.pyplot(plt.gcf())

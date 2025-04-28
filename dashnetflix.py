import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('/mnt/data/netflix_titles.csv')
    df['date_added'] = pd.to_datetime(df['date_added'])
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filter Netflix Titles")
type_filter = st.sidebar.multiselect("Select Type", df['type'].unique(), default=df['type'].unique())
country_filter = st.sidebar.multiselect("Select Country", df['country'].dropna().unique(), default=df['country'].dropna().unique())
year_filter = st.sidebar.slider("Select Release Year", int(df['release_year'].min()), int(df['release_year'].max()), (2010, 2020))

# Apply filters
filtered_df = df[
    (df['type'].isin(type_filter)) &
    (df['country'].isin(country_filter)) &
    (df['release_year'].between(year_filter[0], year_filter[1]))
]

# Main dashboard
st.title("🎬 Netflix Titles Dashboard")

# Top KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Titles", filtered_df.shape[0])
col2.metric("Movies", filtered_df[filtered_df['type'] == 'Movie'].shape[0])
col3.metric("TV Shows", filtered_df[filtered_df['type'] == 'TV Show'].shape[0])

st.markdown("---")

# Releases over time
st.subheader("Releases Over Time")
releases_per_year = filtered_df['release_year'].value_counts().sort_index()
fig_year = px.line(x=releases_per_year.index, y=releases_per_year.values, labels={'x':'Year', 'y':'Number of Titles'}, markers=True)
st.plotly_chart(fig_year, use_container_width=True)

# Content Ratings Pie Chart
st.subheader("Content Rating Distribution")
rating_counts = filtered_df['rating'].value_counts()
fig_rating = px.pie(values=rating_counts.values, names=rating_counts.index, title="Content Ratings")
st.plotly_chart(fig_rating, use_container_width=True)

# Genre distribution
st.subheader("Top Genres")
all_genres = filtered_df['listed_in'].dropna().str.split(', ')
all_genres = all_genres.explode()
top_genres = all_genres.value_counts().head(10)
fig_genres = px.bar(x=top_genres.index, y=top_genres.values, labels={'x':'Genre', 'y':'Number of Titles'})
st.plotly_chart(fig_genres, use_container_width=True)

# Show Data
with st.expander("Show Dataset"):
    st.dataframe(filtered_df)

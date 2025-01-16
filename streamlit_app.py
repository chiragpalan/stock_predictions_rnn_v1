import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Set page configuration for a better layout
st.set_page_config(layout="wide")

# Function to fetch table names from the database
def fetch_table_names(db_path):
    conn = sqlite3.connect(db_path)
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    conn.close()
    return tables

# Fetch available tables from both actual and predicted databases
actual_db_path = 'nifty50_data_v1.db'
pred_db_path = 'predictions/predictions.db'
actual_tables = fetch_table_names(actual_db_path)
pred_tables = fetch_table_names(pred_db_path)

# Combine actual and predicted table names for selection
table_options = list(set(actual_tables) & set([t.replace('_predictions', '') for t in pred_tables]))

# Create the dropdown menu for table selection
selected_table = st.selectbox("Select Table", table_options)

# Function to load the selected table's data and plot the box plot
def load_and_plot_data(selected_table):
    # Connect to the databases
    actual_conn = sqlite3.connect(actual_db_path)
    pred_conn = sqlite3.connect(pred_db_path)

    # Load the actual and predicted data based on selected table
    actual_df = pd.read_sql(f"SELECT * FROM {selected_table} ORDER BY Datetime DESC;", actual_conn)
    pred_df = pd.read_sql(f"SELECT * FROM {selected_table}_predictions ORDER BY Datetime DESC;", pred_conn)

    actual_conn.close()
    pred_conn.close()

    # Convert datetime columns to datetime format
    actual_df['Datetime'] = pd.to_datetime(actual_df['Datetime'], errors='coerce').dt.tz_localize(None)
    pred_df['Datetime'] = pd.to_datetime(pred_df['Datetime'], errors='coerce').dt.tz_localize(None)

    # Drop duplicate entries in the 'Datetime' column by keeping the last entry
    actual_df = actual_df.drop_duplicates(subset=['Datetime'], keep='last')
    pred_df = pred_df.drop_duplicates(subset=['Datetime'], keep='last')

    # Filter data to only include stock market open hours
    market_open = actual_df['Datetime'].dt.time >= pd.to_datetime('09:15').time()
    market_close = actual_df['Datetime'].dt.time <= pd.to_datetime('15:30').time()
    actual_df = actual_df[market_open & market_close]

    pred_open = pred_df['Datetime'].dt.time >= pd.to_datetime('09:15').time()
    pred_close = pred_df['Datetime'].dt.time <= pd.to_datetime('15:30').time()
    pred_df = pred_df[pred_open & pred_close]

    # Streamlit slider for date range selection
    min_date = pred_df['Datetime'].min().date()
    max_date = pred_df['Datetime'].max().date()
    date_range = st.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

    # Filter data based on the selected date range from the slider
    filtered_actual_df = actual_df[(actual_df['Datetime'].dt.date >= date_range[0]) & (actual_df['Datetime'].dt.date <= date_range[1])]
    filtered_pred_df = pred_df[(pred_df['Datetime'].dt.date >= date_range[0]) & (pred_df['Datetime'].dt.date <= date_range[1])]

    # Plot the box plot using Plotly
    fig = go.Figure()

    # Add actual data to the chart
    fig.add_trace(go.Box(
        x=filtered_actual_df['Datetime'],
        y=filtered_actual_df['Close'],
        name='Actual Data',
        marker_color='green'
    ))

    # Add predicted data to the chart
    fig.add_trace(go.Box(
        x=filtered_pred_df['Datetime'],
        y=filtered_pred_df['Predicted_Close'],
        name='Predicted Data',
        marker_color='blue'
    ))

    # Update layout for better visuals
    fig.update_layout(
        title=f"Box Plot for {selected_table}",
        xaxis_title="Datetime",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        xaxis=dict(
            tickformat='%Y-%m-%d %H:%M',
            tickmode='auto',
            showgrid=True,
            type='date'
        ),
        yaxis=dict(
            showgrid=True
        ),
        width=1200,  # Set width to fit 12 inches on your screen
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)  # Use container width to ensure the chart uses full width

# Load and display the data when a table is selected
if selected_table:
    load_and_plot_data(selected_table)

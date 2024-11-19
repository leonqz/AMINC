import streamlit as st
import bcrypt
import pandas as pd
import re
from datetime import datetime

# Example credentials
USERS = {
    "user1": bcrypt.hashpw("password1".encode(), bcrypt.gensalt()).decode(),
    "user2": bcrypt.hashpw("password2".encode(), bcrypt.gensalt()).decode(),
}

def authenticate(username, password):
    """Authenticate the user by checking the username and hashed password."""
    if username in USERS:
        hashed_password = USERS[username].encode()
        return bcrypt.checkpw(password.encode(), hashed_password)
    return False

def main():
    st.title("Streamlit Login Demo")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if authenticate(username, password):
                    st.success("Login successful!")
                    st.session_state.authenticated = True
                else:
                    st.error("Invalid username or password.")

    if st.session_state.authenticated:
        st.success("You are logged in!")
        # Protected content here
        st.write("Welcome to the protected page!")

        if st.button("Logout"):
            st.session_state.authenticated = False

        st.title("Sales Data Dashboard")
    st.write("Upload your sales data files containing 'Date', 'Description', 'Unit Price', and 'Units Sold' columns.")

    # File uploader
    uploaded_files = st.file_uploader("Upload files", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        # Process uploaded files
        combined_data = process_uploaded_files(uploaded_files)

        if not combined_data.empty:
            st.success("Data successfully combined!")
            st.write("Combined Data Preview:")
            st.write(combined_data.head())

            # Visualize the data
            visualize_sales_data(combined_data)

def process_uploaded_files(uploaded_files):
    """Read and combine multiple uploaded files."""
    combined_data = []
    for file in uploaded_files:
        try:
            # Read the file into a DataFrame
            data = pd.read_csv(file)

            # Ensure the 'Date' column is in datetime format
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

            # Drop rows with invalid dates
            data = data.dropna(subset=['Date'])

            combined_data.append(data)
        except Exception as e:
            st.error(f"Error processing file {file.name}: {e}")
    
    if combined_data:
        return pd.concat(combined_data, ignore_index=True)
    return pd.DataFrame()


def visualize_sales_data(combined_data):
    """Visualize sales data."""
    if combined_data.empty:
        st.warning("No valid data to display.")
        return

    # Group data by Date and Description for aggregation
    aggregated_data = combined_data.groupby(['Date', 'Description']).sum().reset_index()
    # Dropdown for selecting an item
    unique_items = aggregated_data['Description'].unique()
    selected_item = st.selectbox("Select an item to visualize:", unique_items)

    # Filter data for the selected item
    filtered_data = aggregated_data[aggregated_data['Description'] == selected_item]

    st.write(f"Data for {selected_item}:")
    st.write(filtered_data)

    # Line chart: Units Sold by Date
    st.subheader(f"Units Sold Over Time for {selected_item}")
    st.line_chart(filtered_data.set_index('Date')['Units Sold'])

    # Line chart: Unit Price by Date
    st.subheader(f"Unit Price Over Time for {selected_item}")
    st.line_chart(filtered_data.set_index('Date')['Unit Price'])


if __name__ == "__main__":
    main()





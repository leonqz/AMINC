import streamlit as st
import bcrypt
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt

# Example credentials
USERS = {
    "aforestier@amincpr.com": bcrypt.hashpw("aaf123@!".encode(), bcrypt.gensalt()).decode(),
    "epabon@amincpr.com": bcrypt.hashpw("ebb124@".encode(), bcrypt.gensalt()).decode(),
}

def authenticate(username, password):
    """Authenticate the user by checking the username and hashed password."""
    if username in USERS:
        hashed_password = USERS[username].encode()
        return bcrypt.checkpw(password.encode(), hashed_password)
    return False

def main():
    st.title("Welcome to BetterBasket, AM Inc")

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
        FILE_NAMES = [
        "Items BetterBasket 9.18.2024.csv",
        "Items BetterBasket 9.25.2024.csv",
        "Items BetterBasket 10.2.2024.csv",
        "Items BetterBasket 10.9.2024.csv",
        "Items BetterBasket 10.16.2024.csv",
        "Items BetterBasket 10.23.2024.csv",
        "Items BetterBasket 10.30.2024.csv",
        "Items BetterBasket 11.6.2024.csv",
        "Items BetterBasket 11.13.2024.csv",

        ]


        data = read_and_combine_files(FILE_NAMES)

        if not data.empty:
            st.success("Data successfully loaded!")
            st.write("Data Preview:")
            st.write(data.head())

            # Dropdown for selecting an item
            unique_items = data['Description'].unique()
            selected_item = st.selectbox("Select an item to visualize:", unique_items)

            # Filter data for the selected item
            filtered_data = data[data['Description'] == selected_item]
            filtered_data = calculate_rolling_metrics(filtered_data)

            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["Sales Trends", "Rolling 7 Day", "Elasticity"])

            with tab1:
                st.subheader(f"Rolling 7-Day Average Sales and Price Change for {selected_item}")
                fig = plot_dual_axis_chart(filtered_data, selected_item)
                st.pyplot(fig)

            with tab2:
                st.subheader(f"Units Sold Over Time for {selected_item}")
                st.line_chart(filtered_data.set_index('Date')['Units Sold'])

                st.subheader(f"Unit Price Over Time for {selected_item}")
                st.line_chart(filtered_data.set_index('Date')['Unit Price'])

            with tab3: 
                st.subheader(f"Price Elasticity for {selected_item}")
                elasticity_results = calculate_elasticity(filtered_data)

                if not elasticity_results.empty:
                    # Filter by date of price change
                    change_dates = elasticity_results['Change Date'].dt.date.unique()
                    selected_dates = st.multiselect("Select price change dates to filter:", change_dates, default=change_dates)

                    # Apply date filter
                    filtered_results = elasticity_results[elasticity_results['Change Date'].dt.date.isin(selected_dates)]

                    st.write(filtered_results)
                    plot_elasticity_chart(filtered_results)

        else:
            st.warning("No valid data to display. Ensure files are correctly formatted.")

def calculate_elasticity(data):
    """Calculate elasticity for items with price changes."""
    # Ensure indices are sequential
    data = data.sort_values('Date').reset_index(drop=True)
    price_changes = data[data['Unit Price'].diff() != 0]

    results = []
    for row_index, row in price_changes.iterrows():
        change_date = row['Date']
        new_price = row['Unit Price']

        # Get the previous price using iloc for positional indexing
        if row_index > 0:
            old_price = data.iloc[row_index - 1]['Unit Price']
        else:
            old_price = None

        if old_price is None or old_price == new_price:
            continue

        # Filter data one month before and after the price change
        before = data[(data['Date'] < change_date) & (data['Date'] >= change_date - pd.Timedelta(days=30))]
        after = data[(data['Date'] > change_date) & (data['Date'] <= change_date + pd.Timedelta(days=30))]

        if before.empty or after.empty:
            continue

        before_sales = before['Units Sold'].sum()
        after_sales = after['Units Sold'].sum()

        quantity_change = (after_sales - before_sales) / before_sales
        price_change = (new_price - old_price) / old_price
        elasticity = quantity_change / price_change if price_change != 0 else None

        results.append({
            'Change Date': change_date,
            'Old Price': old_price,
            'New Price': new_price,
            'Before Sales': before_sales,
            'After Sales': after_sales,
            'Price Change (%)': price_change * 100,
            'Quantity Change (%)': quantity_change * 100,
            'Elasticity': elasticity
        })
    return pd.DataFrame(results)

# Plot elasticity results
def plot_elasticity_chart(results):
    """Visualize sales before and after price changes."""
    for _, row in results.iterrows():
        fig, ax = plt.subplots(figsize=(8, 6))

        ax.bar(['Before', 'After'], [row['Before Sales'], row['After Sales']], color=['blue', 'orange'])
        ax.set_title(f"Price Change on {row['Change Date'].date()}")
        ax.set_xlabel("Period")
        ax.set_ylabel("Units Sold")
        st.pyplot(fig)

        st.write(f"**Elasticity**: {row['Elasticity']:.2f}")
        st.write(f"**Price Change**: {row['Price Change (%)']:.2f}%")
        st.write(f"**Quantity Change**: {row['Quantity Change (%)']:.2f}%")
        st.markdown("---")


def plot_dual_axis_chart(data, item):
    """Plot a dual-axis chart for rolling sales average and unit price."""
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot rolling sales average on the primary y-axis
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Rolling Sales Average", color="blue")
    ax1.plot(data['Date'], data['Rolling_Sales_Avg'], color="blue", label="Rolling Sales Avg")
    ax1.tick_params(axis='y', labelcolor="blue")
    ax1.legend(loc="upper left")

    # Plot unit price on the secondary y-axis
    ax2 = ax1.twinx()
    ax2.set_ylabel("Unit Price", color="red")
    ax2.plot(data['Date'], data['Unit Price'], color="red", linestyle="--", label="Unit Price")
    ax2.tick_params(axis='y', labelcolor="red")
    ax2.legend(loc="upper right")

    plt.title(f"Rolling Sales Avg and Unit Price for {item}")
    plt.tight_layout()
    return fig

def read_and_combine_files(file_names):
    """Read multiple CSV files and combine them into a single DataFrame."""
    combined_data = []
    for file_name in file_names:
        try:
            data = pd.read_csv(file_name)

            # Ensure the 'Date' column is in datetime format
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            data['Units Sold'] = pd.to_numeric(data['Units Sold'], errors='coerce').fillna(0)
            if 'Unit Price' in data.columns:
                data = clean_unit_price_column(data)            
                combined_data.append(data)
        except Exception as e:
            st.error(f"Error reading file {file_name}: {e}")
    
    if combined_data:
        return pd.concat(combined_data, ignore_index=True)
    return pd.DataFrame()

def calculate_rolling_metrics(data):
    """Calculate rolling 7-day averages and price changes."""
    # Sort data by Date
    data = data.sort_values(by='Date')

    # Calculate rolling 7-day average of Units Sold
    data['Rolling_Sales_Avg'] = data['Units Sold'].rolling(window=7).mean()

    # Calculate daily price change
    data['Price_Change'] = data['Unit Price'].diff()

    return data

def clean_unit_price_column(data):
    """Clean and convert 'Unit Price' to numeric."""
    # Remove the dollar sign and convert to numeric
    data['Unit Price'] = data['Unit Price'].str.replace(r'[^0-9.]', '', regex=True)
    data['Unit Price'] = pd.to_numeric(data['Unit Price'], errors='coerce')

    # Fill missing values with 0 (optional) or handle otherwise
    data['Unit Price'] = data['Unit Price'].fillna(0)
    return data

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





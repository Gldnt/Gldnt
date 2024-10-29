import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from functionsappa import (
    get_etf_data, calculate_metrics, plot_performance,
    plot_comparative_performance, get_sector_allocation,
    plot_sector_allocation, plot_correlation_heatmap, plot_monetary_returns_pie
)
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

# Title and Introduction
st.markdown("""
    <style>
    .reportview-container {
        background-color: #f4f4f4;
    }
    </style>
    <div style="background-image: url('https://images.unsplash.com/photo-1523202732194-ecc5a7d5b8ac'); background-size: cover;">
    <h1 style="color: black; text-align: center;">Welcome to the ETF Performance Tracker</h1>
    <p style="color: black; text-align: center;">This dashboard is designed for Allianz Patrimonial to track and analyze the performance of selected ETFs.</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar for user inputs
st.sidebar.header("Configure Analysis")
selected_tickers = st.sidebar.multiselect("Choose ETF(s)", [
    "FXI", "EWT", "IWM", "EWZ", "EWU", "XLF", "BKF", "EWY", "AGG", "EEM",
    "EZU", "GLD", "QQQ", "AAXJ", "SHY", "ACWI", "SLV", "EWH", "SPY", "EWJ",
    "IBGL", "DIA", "EWQ", "XOP", "VWO", "EWA", "XLF", "EWC", "ILF", "XLV",
    "EWG", "ITB"
], default=["FXI", "SPY"])

period = st.sidebar.selectbox("Select time period", ["1y", "3y", "5y", "10y", "YTD", "Custom Range"])

# Custom date range option
start_date, end_date = None, None
if period == "Custom Range":
    start_date = st.sidebar.date_input("Start Date", datetime.now().replace(year=datetime.now().year - 5))
    end_date = st.sidebar.date_input("End Date", datetime.now())

# Investment allocation inputs
investment_amount = st.sidebar.number_input("Total Investment Amount ($)", min_value=0.0, max_value=100000.0, step=100.0, value=10000.0)
allocation = {}
total_allocation = 0

if selected_tickers:
    st.sidebar.subheader("Investment Allocation")
    
    for ticker in selected_tickers:
        remaining_allocation = 100 - total_allocation
        allocation[ticker] = st.sidebar.slider(
            f"Allocation for {ticker} (%)", 
            min_value=0, 
            max_value=remaining_allocation, 
            value=0
        )
        
        total_allocation += allocation[ticker]

    st.sidebar.write(f"Total Allocation: {total_allocation}%")
    if total_allocation > 100:
        st.sidebar.warning("Total allocation cannot exceed 100%!")

# Fetch and display data
if selected_tickers:
    st.write(f"### Analysis for: {', '.join(selected_tickers)}")
    
    # Data retrieval with caching
    data = get_etf_data(selected_tickers, period=period, start_date=start_date, end_date=end_date)
    
    summary_data = []  # For summary table
    total_invested_capital = 0
    total_current_worth = 0

    for ticker in selected_tickers:
        st.write(f"#### {ticker} Performance Overview")
        etf_data = data.get(ticker)
        if etf_data is not None:
            # Calculate financial metrics
            metrics = calculate_metrics(etf_data)
            
            # Check for None values in metrics
            if None in metrics.values():
                st.error(f"Failed to calculate metrics for {ticker}. Please check the data.")
                continue  # Skip to the next ticker if metrics are not valid
            
            # Calculate investment worth today based on cumulative return
            allocation_percentage = allocation[ticker]
            if allocation_percentage > 0:
                cumulative_return = metrics["Cumulative Return"]
                invested_amount = investment_amount * (allocation_percentage / 100)
                investment_worth_today = invested_amount * (1 + cumulative_return)

                # Update totals
                total_invested_capital += invested_amount
                total_current_worth += investment_worth_today
            else:
                investment_worth_today = 0

            # Append metrics to summary data
            summary_data.append({
                "ETF": ticker,
                "Average Return": f"{metrics['Average Return']:.2%}",
                "Volatility": f"{metrics['Volatility']:.2%}" if metrics['Volatility'] is not None else "N/A",
                "Cumulative Return": f"{metrics['Cumulative Return']:.2%}",
                "Investment Worth Today": investment_worth_today,
                "Initial Investment": invested_amount
            })

            # Display metrics in a table
            st.write("**Key Metrics**")
            metrics_df = pd.DataFrame([metrics])
            st.dataframe(metrics_df)

            # Plot performance
            fig = plot_performance(etf_data, title=f"{ticker} Price History")
            st.pyplot(fig)

            # Display sector allocation
            sector_allocation = get_sector_allocation(ticker)
            if sector_allocation is not None:
                st.write("**Sector Allocation**")
                st.dataframe(sector_allocation)
                st.pyplot(plot_sector_allocation(sector_allocation))

# Summary table for all returns and presented information
st.write("### Summary of Returns and Information")
summary_df = pd.DataFrame(summary_data)
summary_df["Investment Worth Today"] = summary_df["Investment Worth Today"].apply(lambda x: f"${x:,.2f}")
summary_df["Initial Investment"] = summary_df["Initial Investment"].apply(lambda x: f"${x:,.2f}")
st.table(summary_df)

# Total summary
total_earned = total_current_worth - total_invested_capital
st.write(f"**Total Invested Capital:** ${total_invested_capital:,.2f}")
st.write(f"**Total Worth Today:** ${total_current_worth:,.2f}")
st.write(f"**Total Earned:** ${total_earned:,.2f}")

# Bar chart for initial vs current worth
if summary_data:
    bar_df = pd.DataFrame(summary_data)
    
    # Ensure numeric values are used for plotting
    initial_investment_values = bar_df["Initial Investment"].astype(float)
    investment_worth_values = bar_df["Investment Worth Today"].astype(float)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=bar_df["ETF"], y=initial_investment_values, name="Initial Investment", marker_color="blue"))
    fig.add_trace(go.Bar(x=bar_df["ETF"], y=investment_worth_values, name="Investment Worth Today", marker_color="green"))
    fig.update_layout(
        title="Investment Worth Comparison",
        xaxis_title="ETF",
        yaxis_title="Amount ($)",
        barmode="group"
    )
    st.plotly_chart(fig)


# Display comparative performance if multiple ETFs selected
if len(selected_tickers) > 1:
    st.write("#### Comparative Performance")
    fig = plot_comparative_performance(data, selected_tickers)
    st.pyplot(fig)

# Plot correlation heatmap only if there are multiple selected tickers
if len(selected_tickers) > 1:
    st.write("### Correlation Heatmap of Selected ETFs")
    heatmap_fig = plot_correlation_heatmap(data, selected_tickers)
    if heatmap_fig is not None:
        st.pyplot(heatmap_fig)

# Export data option
st.write("### Download Data")
if st.button("Download CSV"):
    combined_data = pd.concat([data[ticker]['Close'] for ticker in selected_tickers], axis=1)
    combined_data.columns = selected_tickers
    st.download_button("Download ETF Data", combined_data.to_csv().encode("utf-8"), "etf_data.csv", "text/csv")

st.subheader("User Feedback")
user_rating = st.radio("Rate your experience (5 is the best):", options=[1, 2, 3, 4, 5], index=0)
feedback = st.text_area("Enter your feedback or comments here:")
if st.button("Submit Feedback"):
    st.write("Thank you for your feedback!")

# Footer
st.markdown("""
    ---
    &copy; 2024 Allianz Patrimonial. All Rights Reserved.  
    For inquiries, contact us at: [email@allianz.com](mailto:email@allianz.com)  
    *Disclaimer: This tool is for informational purposes only and does not constitute financial advice.*
""")
st.markdown("Connect with us: [Twitter](#) | [LinkedIn](#) | [Website](#)")

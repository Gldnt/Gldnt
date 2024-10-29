import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt



def plot_monetary_returns_pie(labels, values, total_investment):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Normalize values to percentages of total investment
    normalized_values = [value / total_investment * 100 for value in values]
    
    wedges, texts, autotexts = ax.pie(normalized_values, labels=labels, autopct='%1.1f%%', startangle=90)
    
    # Add text annotations with investment worth
    for i, text in enumerate(texts):
        text.set_text(f"\n\n${normalized_values[i]:.2f}\n(${values[i]:.2f})")
    
    # Set title and adjust layout
    plt.title('Monetary Returns Distribution', fontsize=16)
    plt.axis('equal')  # Equal aspect ratio ensures pie chart is circular
    
    # Add legend explaining the format
    plt.figtext(0.95, 0.05, 'Values shown are in USD. Parentheses indicate initial investment amount.', 
               verticalalignment='bottom', horizontalalignment='right',
               fontsize=8, bbox=dict(boxstyle='round,pad=0.5', alpha=0.9, facecolor='yellow'))
    
    return fig



# Fetch ETF data
@st.cache_data
def get_etf_data(tickers, period="5y", start_date=None, end_date=None):
    """Fetches historical data for the given tickers from Yahoo Finance."""
    data = {}
    for ticker in tickers:
        try:
            etf = yf.Ticker(ticker)
            data[ticker] = etf.history(period=period, start=start_date, end=end_date)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            data[ticker] = pd.DataFrame(columns=['Close'])  # Create empty DataFrame if fetch fails
    return data

# Calculate performance metrics
def calculate_metrics(df):
    returns = df['Close'].pct_change().dropna()
    avg_return = np.mean(returns) if not returns.empty else None
    volatility = np.std(returns) if not returns.empty else None
    cumulative_return = (df['Close'][-1] / df['Close'][0]) - 1 if not df.empty else None
    return {
        'Average Return': avg_return,
        'Volatility': volatility,
        'Cumulative Return': cumulative_return,
    }

# Plot ETF performance
def plot_performance(df, title="ETF Performance"):
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['Close'], label='Closing Price', color='blue')
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid()
    return plt

# Plot comparative performance
def plot_comparative_performance(data, tickers):
    plt.figure(figsize=(12, 6))
    for ticker in tickers:
        plt.plot(data[ticker].index, data[ticker]['Close'], label=ticker)
    plt.title("Comparative Performance of Selected ETFs")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid()
    return plt

# Get sector allocation for an ETF
def get_sector_allocation(ticker):
    try:
        etf = yf.Ticker(ticker)
        sector_weights = etf.sector_weights
        sectors = list(sector_weights.keys())
        allocations = [sector_weights[sector] * 100 for sector in sectors]
        sector_allocation = pd.DataFrame({'Sector': sectors, 'Allocation (%)': allocations})
        return sector_allocation
    except Exception as e:
        print(f"Error retrieving sector allocation for {ticker}: {e}")
        return None

# Plot sector allocation
def plot_sector_allocation(sector_allocation):
    plt.figure(figsize=(8, 6))
    plt.bar(sector_allocation['Sector'], sector_allocation['Allocation (%)'], color='skyblue')
    plt.title("Sector Allocation")
    plt.ylabel("Allocation (%)")
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    return plt

# Plot correlation heatmap
def plot_correlation_heatmap(data, tickers):
    combined_data = pd.concat([data[ticker]['Close'] for ticker in tickers], axis=1)
    combined_data.columns = tickers
    correlation = combined_data.pct_change().corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt='.2f', square=True, cbar_kws={"shrink":.8})
    plt.title("Correlation Heatmap")
    return plt

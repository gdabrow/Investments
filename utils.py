"""
Definitions of needed functions and objects
"""

import yfinance as yf
import pandas as pd
import cloudscraper
from urllib.request import urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import csv
import random
import json
import time

scraper = cloudscraper.create_scraper(delay=10)
fin_apikey = 'c21576dc0c20c5ea9792a384f102c6db'


def read_csv_as_flat_list(filename: str) -> list[str]:
    """
    Reads a CSV file and returns a flat list containing all values.

    Arguments:
    filename (str): The path to the CSV file to be read.

    Returns:
    list: A flat list containing all values from the CSV file, where each list item
    represents a single value from the file.

    Example usage:
    >>> data = read_csv_as_flat_list('your_file_name.csv')
    >>> print(data)
    """

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        flat_list = [item for row in reader for item in row]
    return flat_list



def go_to_url(tickers: list[str], urls: list[str]) -> list[dict]:
    """
    This function generates a list of dictionaries, each containing the stock symbol and corresponding URLs modified to include the ticker symbol.

    Args:
    tickers (list of str): A list of ticker symbols (e.g., ['AAPL', 'GOOG']).
    urls (list of str): A list of URL templates (e.g., ['https://www.zacks.com/stock/quote/', 'https://www.tipranks.com/stocks/']).

    Returns:
    list of dicts: A list where each dictionary represents a ticker symbol and its associated URLs.
                   Each key in the dictionary is the domain of the URL, and its value is the URL concatenated with the ticker symbol.
    """

    www = []

    for tic in tickers:
        dic={'symbol': tic}

        for url in urls:
            netloc = urlparse(url).netloc
            dic[netloc]= url + tic

        www.append(dic)

    www = pd.DataFrame(www)
    www.set_index('symbol', inplace=True)

    return www


def conversion_to_number(dataframe: pd.DataFrame, columns: list) -> None:
    """
    Convert specified columns in a pandas DataFrame from percentage strings to float.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing the columns to convert.
        columns (list): A list of column names (strings) to be converted.

    Note:
        This function modifies the original DataFrame in place.

    Example:
        conversion_to_number(df, ['column1', 'column2'])
    """
    # Check if the input is of correct types
    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError("dataframe must be a pandas DataFrame")
    if not isinstance(columns, list):
        raise ValueError("columns must be a list of column names")

    # Iterate through the specified columns and convert each from percentage string to float
    for col in columns:
        # Check if the column exists in the DataFrame
        if col not in dataframe.columns:
            raise ValueError(f"Column {col} does not exist in the DataFrame")
        # Replace '%' with nothing and convert the type
        dataframe[col] = dataframe[col].str.replace("%", "").astype(float)


def conversion_to_percent(dataframe: pd.DataFrame, columns: list) -> None:
    """
    Convert selected columns of a DataFrame to percentages by multiplying them by 100.

    Args:
    dataframe (pd.DataFrame): The DataFrame containing the columns to be converted.
    columns (list): A list of column names (strings) to be converted to percentages.

    Returns:
    None: The function modifies the DataFrame in place and does not return anything.

    Raises:
    KeyError: If any of the specified columns do not exist in the DataFrame.
    TypeError: If the data in the columns is not numeric and cannot be converted to percentages.
    """
    # Check if all columns exist in the DataFrame
    missing_cols = [col for col in columns if col not in dataframe.columns]
    if missing_cols:
        raise KeyError(f"The following columns are missing from the DataFrame: {missing_cols}")

    # Check if all specified columns are numeric
    non_numeric_cols = [col for col in columns if not pd.api.types.is_numeric_dtype(dataframe[col])]
    if non_numeric_cols:
        raise TypeError(f"The following columns are not numeric and cannot be converted to percentages: {non_numeric_cols}")

    # Convert columns to percentages
    for col in columns:
        dataframe[col] = dataframe[col] * 100
        # Ensure the operation does not introduce unexpected types
        dataframe[col] = dataframe[col].astype(float)

# Note: The function call and any tests should be uncommented and run outside this code block to verify its functionality.



def get_data_from_yf(tickers: list[str]) -> pd.DataFrame:
    """
    Fetches and processes financial data for a list of tickers from Yahoo Finance.

    Args:
        tickers (list of str): A list of stock ticker symbols.

    Returns:
        pandas.DataFrame: A DataFrame containing processed Yahoo Finance data for the given tickers.
    """

    yahoo_data = []  # Initialize an empty list to store data for each ticker

    # Iterate over each ticker to fetch and process its data
    for tic in tickers:
        try:
            data = yf.Ticker(tic).info  # Fetch data for the ticker
        except Exception as e:
            print(f"Failed to fetch Yahoo Finance data for {tic}: {e}")
            continue  # Skip to the next ticker if an error occurs

        # Convert selected fields to percentages based on the regular market previous close price
        try:
            price = float(data['regularMarketPreviousClose'])  # Get the previous close price
            # Map original field names to new percentage field names
            percentage_fields = {
                'targetLowPrice': 'Target low price [%]',
                'targetMeanPrice': 'Target mean price [%]',
                'targetMedianPrice': 'Target median price [%]',
                'targetHighPrice': 'Target high price [%]'
            }
            for original, new in percentage_fields.items():
                if original in data:
                    # Convert the original price to a percentage change
                    data[new] = round(100 * (float(data[original]) / price - 1), 2)
                else:
                    data[new] = None  # Set to None if the original field is missing
        except Exception as e:
            print(f"Failed to process percentage fields for {tic}: {e}")
            continue  # Skip to the next ticker if an error occurs

        yahoo_data.append(data)  # Add the processed data to the list


    yahoo_data = pd.DataFrame(yahoo_data)  # Convert the list of data to a DataFrame
    yahoo_data.set_index('symbol', inplace=True)

    return yahoo_data  # Return the processed DataFrame


def get_data_from_zacks(tickers: list[str]) -> pd.DataFrame:
    """
    Fetches Zacks Investment Research rankings for a given list of stock symbols.

    Args:
        tickers (List[str]): List of stock symbols to fetch the ranking for.

    Returns:
        pd.DataFrame: DataFrame containing the Zacks ranking for each stock symbol.
                      If the ranking is not available, returns 0 for that symbol.
    """

    zacks = []
    for tic in tickers:
        url = f'https://www.zacks.com/stock/quote/{tic}'
        try:
            page = scraper.get(url)
            page_html = BeautifulSoup(page.content, 'html.parser')
            rank = page_html.find_all('span', class_=lambda x: x and x.startswith('rank_chip rankrect_'))
            for r in rank:
                if r.text.isdigit():
                    zacks.append({'symbol' : tic, 'zacks' : int(r.text)})
                    time.sleep(random.uniform(1, 3))  # Randomized delay to mimic human behavior

        except:
            zacks.append({'symbol' : tic, 'zacks' : 0})
            time.sleep(random.uniform(1, 3))  # Randomized delay to mimic human behavior
            continue

    zacks = pd.DataFrame(zacks)
    zacks.set_index('symbol', inplace=True)

    return zacks


def get_data_from_financialmodeling(tickers: list, fin_apikey: str) -> pd.DataFrame:

    """
    Fetches and combines discounted cash flow and rating information for a list of tickers from the FinancialModelingPrep API.

    Args:
        tickers (list): A list of stock tickers (symbols) for which data is to be fetched.
        fin_apikey (str): The API key required to authenticate requests to the FinancialModelingPrep API.

    Returns:
        pd.DataFrame: A DataFrame containing the combined data for all tickers, set with 'symbol' as the index.
    """

    financialmodelin = []
    for tic in tickers:

        cdf_url = f'https://financialmodelingprep.com/api/v3/discounted-cash-flow/{tic}?apikey={fin_apikey}'
        rating_url = f'https://financialmodelingprep.com/api/v3/rating/{tic}?apikey={fin_apikey}'


        try:
            cdf_response = urlopen(cdf_url)
        except Exception as e:
            print(f"No data for {tic}: {e}")
            continue
        cdf_data = json.loads(cdf_response.read().decode("utf-8"))

        if len(cdf_data) == 0:
            cdf_data = [{'symbol': tic,
                        'date': 'no data',
                        'dcf': 0,
                        'Stock Price': 0}]

        try:
            rating_response = urlopen(rating_url)
        except Exception as e:
            print(f"No data for {tic}: {e}")
            continue

        rating_data = json.loads(rating_response.read().decode("utf-8"))

        if len(rating_data) == 0:
            rating_data = [{'symbol': tic,
                            'date': 'no data',
                            'rating': 'no data',
                            'ratingScore': 0 ,
                            'ratingRecommendation': 'no data',
                            'ratingDetailsDCFScore': 0,
                            'ratingDetailsDCFRecommendation': 'no data',
                            'ratingDetailsROEScore': 0,
                            'ratingDetailsROERecommendation': 'no data',
                            'ratingDetailsROAScore': 0,
                            'ratingDetailsROARecommendation': 'no data',
                            'ratingDetailsDEScore': 0,
                            'ratingDetailsDERecommendation': 'no data',
                            'ratingDetailsPEScore': 0,
                            'ratingDetailsPERecommendation': 'no data',
                            'ratingDetailsPBScore': 0,
                            'ratingDetailsPBRecommendation': 'no data'}]

        financialmodelin.append({**cdf_data[0], **rating_data[0]})

    financialmodelin = pd.DataFrame(financialmodelin)
    financialmodelin.set_index('symbol', inplace=True)

    return financialmodelin


def get_data_from_finviz(tickers: list[str]) -> pd.DataFrame:
    """
    Fetches and returns financial data for a list of tickers from Finviz.

    Args:
        tickers (List[str]): A list of stock ticker symbols.

    Returns:
        pd.DataFrame: A DataFrame containing the financial data for each ticker,
                      with each row representing a different ticker and columns for different financial metrics.
                      The index of the DataFrame is set to the ticker symbols.
    """
    # Initialize the list to hold data for all tickers
    finviz_data = []

    # List of user agents to rotate through for requests, to prevent request blocking by the server
    USER_AGENTS_LIST = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.92 Mobile Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0"
    ]

    # Loop through each ticker to scrape its data
    for tic in tickers:
        url = f'https://finviz.com/quote.ashx?t={tic}'
        # Random choice of user-agent to prevent blocking
        page = scraper.get(url, headers={'User-Agent': random.choice(USER_AGENTS_LIST)})
        page_html = BeautifulSoup(page.content, 'html.parser')
        table = page_html.find_all('tr', class_='table-dark-row')
        # Delay to prevent being blocked by the server
        time.sleep(random.uniform(1, 3))  # Randomized delay to mimic human behavior

        # Skip tickers for which no data is available
        if not table:
            print(f'No data for {tic}')
            continue

        # Initialize lists for the names and values of data points
        names, values = [], []

        # Extract data from each row of the table
        for row in table:
            cells = row.find_all('td', class_='snapshot-td2')
            for i, cell in enumerate(cells):
                text = cell.text.strip() if cell.text.strip() != '-' else '0'  # Strip whitespace and convert '-' to '0'
                if i % 2 == 0:  # Even index elements are names
                    names.append(text)
                else:  # Odd index elements are values
                    values.append(text)

        # Create a dictionary for the ticker's data and add it to the list
        data = dict(zip(names, values))
        data['Symbol'] = tic
        finviz_data.append(data)

    # Convert the list of data into a pandas DataFrame and set the index to the symbols
    finviz_data = pd.DataFrame(finviz_data)
    finviz_data.set_index('Symbol', inplace=True)

    return finviz_data


def get_selected_tickers_from_finviz(urls: list[str]) -> pd.DataFrame:
    """
    Scrapes given Finviz URLs for stock tickers.

    Args:
        urls (List[str]): A list of URLs to scrape for tickers.

    Returns:
        pd.DataFrame: A dataframe containing all found tickers.
    """
    # Initialize an empty list to store tickers
    tickers = []

    # Loop through each URL
    for url in urls:
        # Scrape the page content
        page = scraper.get(url)  # Assuming 'scraper' is a predefined variable, need to handle its definition.
        page_html = BeautifulSoup(page.content, 'html.parser')

        # Find all 'a' elements with class 'tab-link' and containing 'quote.ashx?t' in 'href'
        for a in page_html.find_all('a', class_="tab-link", href=True):
            if 'quote.ashx?t' in a['href']:
                # Add the ticker text to the list
                tickers.append(a.text)

    # Convert the list of tickers to a DataFrame
    tickers = pd.DataFrame(tickers, columns=['ticker'])

    # Return the DataFrame
    return tickers


def norm(series: pd.Series, max_value: float, reverse: bool = False) -> pd.Series:
    """
    Normalizes a Pandas Series by dividing all its values by a specified maximum value.
    Optionally, reverses the series values by subtracting from the max_value and adds one before normalization.

    Args:
        series (Series): Pandas Series to be normalized.
        max_value (float): The value used to normalize the series values.
        reverse (bool, optional): Flag to determine if the series values should be reversed. Defaults to False.

    Returns:
        Series: The normalized (and possibly reversed) Pandas Series.

    Raises:
        ValueError: If max_value is zero, to avoid division by zero.
    """

    # Check if max_value is zero to prevent division by zero
    if max_value == 0:
        raise ValueError("max_value cannot be zero.")

    # If reverse is True, modify the series accordingly
    if reverse:
        series = -series + max_value + 1

    # Normalize the series
    normalized_series = series / max_value

    # Ensure no values exceed 1.5 after normalization
    normalized_series = normalized_series.clip(upper=1.5)

    return normalized_series

# name of the fields that will be retrieved from finance.yahoo
COLUMNS_YF = ['exchange', 'country', 'industry', 'sector', 'currentPrice',
              'trailingPE', 'forwardPE', 'pegRatio', 'trailingPegRatio', 'trailingEps', 'forwardEps',
              'recommendationMean', 'recommendationKey', 'numberOfAnalystOpinions',
              'targetHighPrice', 'targetLowPrice', 'targetMeanPrice', 'targetMedianPrice',
              'Target low price [%]', 'Target mean price [%]', 'Target median price [%]', 'Target high price [%]',
              'profitMargins', 'revenueGrowth', 'grossMargins', 'ebitdaMargins', 'quickRatio', 'currentRatio', 'earningsGrowth']

# fields that will be renamed from from finance.yahoo for clarity
COLUMNS_YF_TO_CHANGE = {'currentPrice':'Price', 'trailingPE':'Trailing PE', 'forwardPE':'Forward PE',
                        'pegRatio':'PEG ratio', 'trailingPegRatio':'Trailing PEG ratio', 'trailingEps':'Trailing EPS',
                        'forwardEps':'Forward Eps', 'recommendationMean':'Recommendation mean', 'recommendationKey':'Recommendation key',
                        'numberOfAnalystOpinions':'Number of analyst', 'targetHighPrice':'Target high price', 'targetLowPrice':'Target low price',
                        'targetMeanPrice':'Target mean price', 'targetMedianPrice':'Target median price', 'profitMargins':'Profit margins',
                        'revenueGrowth':'Revenue growth', 'grossMargins':'Gross margins', 'ebitdaMargins':'Ebitda margins', 'quickRatio':'Quick ratio',
                        'currentRatio':'Current rtio', 'earningsGrowth':'Earnings growth'}

# fields that will be renamed from from financialmodelingprep.com for clarity
COLUMNS_FINMOD_TO_CHANGE = {'rating':'Rating', 'ratingScore':'Rating score', 'ratingRecommendation':'Rating recommendation',
                            'ratingDetailsDCFScore':'Rating DCF score', 'ratingDetailsDCFRecommendation':'Rrating DCF recommendation',
                            'ratingDetailsROEScore':'Rating ROE score', 'ratingDetailsROERecommendation':'Rating ROE recommendation',
                            'ratingDetailsROAScore':'Rating ROA score', 'ratingDetailsROARecommendation':'Rating ROA recommendation',
                            'ratingDetailsDEScore':'Rating D/E score', 'ratingDetailsDERecommendation':'Rating DE recommendation',
                            'ratingDetailsPEScore':'Rating P/E score', 'ratingDetailsPERecommendation':'Rating PE recommendation',
                            'ratingDetailsPBScore':'Rating P/B score', 'ratingDetailsPBRecommendation':'Rating PB recommendation'}

# name of the fields that will be retrieved from finviz.com
COLUMNS_FIN = ['EPS this Y', 'EPS next Q','EPS next Y', 'EPS next 5Y', 'EPS past 5Y', 'PEG', 'ROA', 'ROE', 'ROI']

# field names to convert to percentages
COLUMNS_TO_PERCENT = ['Profit margins', 'Revenue growth', 'Gross margins','Earnings growth']

# field names which will be shown in the report
COLUMNS_TO_SHOW = ['exchange', 'country', 'industry', 'sector', 'Ranking', 'Price', 'Trailing PE', 'Number of analyst','Recommendation mean',
                      'Recommendation key','Target low price [%]', 'Target mean price [%]', 'Target median price [%]',
                      'Target high price [%]', 'zacks', 'tipranks', 'Quick ratio', 'Current rtio', 'EPS this Y', 'EPS next Y',
                      'PEG', 'ROA', 'ROE', 'ROI', 'www.zacks.com',	'www.tipranks.com']

# names of fields for ranking with their parameters
PARAMETERS_FOR_RANKING = [
    {'series': 'Recommendation mean', 'max': 5, 'reverse': True, 'weight': 1.0},
    {'series': 'Target mean price [%]', 'max': 25, 'reverse': False, 'weight': 1.2},
    {'series': 'Target median price [%]', 'max': 25, 'reverse': False, 'weight': 1.2},
    {'series': 'Target high price [%]', 'max': 50, 'reverse': False, 'weight': 1.0},
    {'series': 'zacks', 'max': 5, 'reverse': True, 'weight': 1.2},
    {'series': 'tipranks', 'max': 10, 'reverse': False, 'weight': 1.1},
    {'series': 'EPS next Y', 'max': 25, 'reverse': False, 'weight': 1.2},
    {'series': 'ROA', 'max': 10, 'reverse': False, 'weight': 1.0},
    {'series': 'ROE', 'max': 15, 'reverse': False, 'weight': 0.8},
    {'series': 'ROI', 'max': 20, 'reverse': False, 'weight': 1.1}]

# fragments of urls that will be used to build redirections to appropriate websites
URLS =['https://www.zacks.com/stock/quote/', 'https://www.tipranks.com/stocks/']

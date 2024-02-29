# Investments

This script is designed to collect information about stock market companies from various online services using APIs or through web scraping, and then present this information in tabular form in an *xlsx* file. Additionally, the script creates a ranking of these companies based on rules established by the script's author. Detailed parameters for the ranking can be found in the **PARAMETERS_FOR_RANKING** dictionary in the *utilities.py* or *StockAnalysis.ipynb* file.
### Information is sourced from the following services:
* [seekingalpha.com](seekingalpha.com)
* [zacks.com](https://www.zacks.com/)
* [finance.yahoo.com](https://finance.yahoo.com)
* [financialmodelingprep.com](https://site.financialmodelingprep.com)
* [alphavantage.co](https://www.alphavantage.co)
* [tipranks.com](https://www.tipranks.com)
  
The necessary input file for the analysis is an xlsx file that contains two columns: symbol and tipranks, where they respectively contain the tickers of the companies and the ratings of the companies obtained from tipranks.com. Unfortunately, data in the tipranks column must be manually filled in, as there is no possibility of automating this process."

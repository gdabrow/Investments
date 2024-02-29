# Investments

This script is designed to collect information about stock market companies from various online services using APIs or through web scraping, and then present this information in tabular form in an *xlsx* file. Additionally, the script creates a ranking of these companies based on rules established by the script's author. Detailed parameters for the ranking can be found in the **PARAMETERS_FOR_RANKING** dictionary in the **utilities.py** or **StockAnalysis.ipynb** file.
### Information is sourced from the following services:
* [zacks.com](https://www.zacks.com/)
* [finance.yahoo.com](https://finance.yahoo.com/)
* [financialmodelingprep.com](https://site.financialmodelingprep.com/)
* [alphavantage.co](https://www.alphavantage.co/)
* [tipranks.com](https://www.tipranks.com/)

### How it's working
The necessary input file for the analysis is an *.xlsx* file (the sample file in this repository is **candidates.xlsx**) that contains two columns: **symbol** and **tipranks**, where they respectively contain the tickers of the companies and the ratings of the companies obtained from tipranks.com. Unfortunately, data in the **tipranks** column must be manually filled in, as there is no possibility of automating this process. Then the script downloads the symbols of the listed companies we are interested in from **candidates.xlsx** and collects information from the websites listed above. The next step is to combine all the information and build a ranking based on it. The parameters that take part in building the ranking and their weights are placed in a dictionary called **PARAMETERS_FOR_RANKING**. Finally, the script prepares an *.xlsx* file with the collected data and ranking for individual companies (the sample file in this repository is **ranking.xlsx**).

"""
Ticker to company name mapping for common stocks
"""

TICKER_TO_NAME = {
    # Tech
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "GOOG": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.",
    "CRM": "Salesforce Inc.",
    "INTC": "Intel Corporation",
    "AMD": "Advanced Micro Devices",
    "QCOM": "Qualcomm Inc.",
    "CSCO": "Cisco Systems Inc.",
    "ORCL": "Oracle Corporation",
    "IBM": "IBM Corporation",
    "AVGO": "Broadcom Inc.",
    "MU": "Micron Technology Inc.",
    "MCHP": "Microchip Technology Inc.",
    
    # Finance
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corp.",
    "WFC": "Wells Fargo & Company",
    "GS": "Goldman Sachs Group Inc.",
    "MS": "Morgan Stanley",
    "BLK": "BlackRock Inc.",
    "SCHW": "Charles Schwab Corp.",
    "AXP": "American Express Company",
    "V": "Visa Inc.",
    "MA": "Mastercard Inc.",
    "DFS": "Discover Financial Services",
    "COF": "Capital One Financial",
    
    # Healthcare
    "JNJ": "Johnson & Johnson",
    "UNH": "UnitedHealth Group Inc.",
    "PFE": "Pfizer Inc.",
    "ABBV": "AbbVie Inc.",
    "MRK": "Merck & Co. Inc.",
    "LLY": "Eli Lilly and Company",
    "AZN": "AstraZeneca PLC",
    "AMGN": "Amgen Inc.",
    "GILD": "Gilead Sciences Inc.",
    "BIIB": "Biogen Inc.",
    "VRTX": "Vertex Pharmaceuticals",
    "REGN": "Regeneron Pharmaceuticals",
    
    # Consumer
    "WMT": "Walmart Inc.",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo Inc.",
    "MCD": "McDonald's Corporation",
    "NKE": "Nike Inc.",
    "LULU": "Lululemon Athletica",
    "TJX": "The TJX Companies Inc.",
    "HD": "The Home Depot Inc.",
    "LOW": "Lowe's Companies Inc.",
    "DRI": "Dine Global Holdings Corp.",
    "SBUX": "Starbucks Corporation",
    "CMG": "Chipotle Mexican Grill",
    
    # Industrial
    "BA": "The Boeing Company",
    "CAT": "Caterpillar Inc.",
    "GE": "General Electric Company",
    "HON": "Honeywell International",
    "MMM": "3M Company",
    "RTX": "Raytheon Technologies",
    "LMT": "Lockheed Martin Corporation",
    "NOC": "Northrop Grumman Corp.",
    "GD": "General Dynamics Corp.",
    "TT": "Trane Technologies PLC",
    
    # Energy
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "COP": "ConocoPhillips",
    "SLB": "Schlumberger Limited",
    "EOG": "EOG Resources Inc.",
    "MPC": "Marathon Petroleum Corp.",
    "PSX": "Phillips 66",
    "VLO": "Valero Energy Corp.",
    
    # Utilities
    "NEE": "NextEra Energy Inc.",
    "DUK": "Duke Energy Corporation",
    "SO": "Southern Company",
    "EXC": "Exelon Corporation",
    "AEP": "American Electric Power",
    "XEL": "Xcel Energy Inc.",
    "PEG": "Public Service Enterprise",
    "AWK": "American Water Works",
    
    # Real Estate
    "PLD": "Prologis Inc.",
    "AMT": "American Tower Corp.",
    "CCI": "Crown Castle Inc.",
    "EQIX": "Equinix Inc.",
    "SPG": "Simon Property Group",
    "AVB": "AvalonBay Communities",
    "EQR": "Equity Residential",
    "MAA": "Mid-America Apartment",
    
    # Materials
    "NEM": "Newmont Corporation",
    "FCX": "Freeport-McMoran Inc.",
    "SCCO": "Southern Copper Corp.",
    "ALB": "Albemarle Corporation",
    "LIN": "Linde PLC",
    "APD": "Air Products & Chemicals",
    "DD": "DuPont de Nemours Inc.",
    "ECL": "Ecolab Inc.",
    
    # Communication
    "VZ": "Verizon Communications",
    "T": "AT&T Inc.",
    "CMCSA": "Comcast Corporation",
    "CHTR": "Charter Communications",
    "TMUS": "T-Mobile US Inc.",
    
    # ETFs & Indices
    "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ Trust",
    "IWM": "iShares Russell 2000 ETF",
    "EEM": "iShares MSCI Emerging Markets",
    "GLD": "SPDR Gold Shares",
    "TLT": "iShares 20+ Year Treasury",
    "AGG": "iShares Core U.S. Aggregate Bond",
}


def get_company_name(ticker: str) -> str:
    """Get company name for a ticker, fallback to ticker if not found"""
    return TICKER_TO_NAME.get(ticker.upper(), ticker.upper())

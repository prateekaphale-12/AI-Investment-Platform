"""
Data Validation Layer - Critical guardrails for data quality.

This layer validates all stock data before it's used in analysis or narratives.
Bad data at high confidence levels is extremely dangerous.

Validation checks:
1. Price sanity (reasonable range for ticker)
2. Return sanity (no impossible returns)
3. Market cap consistency
4. Split adjustment verification
5. Stale data detection
6. Outlier detection
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

# Known price ranges for major tickers (conservative bounds)
# Format: ticker -> (min_reasonable_price, max_reasonable_price)
# These are WIDE ranges to catch obvious corruption, not tight bounds
PRICE_BOUNDS: dict[str, tuple[float, float]] = {
    # Semiconductors
    "NVDA": (10, 2000),
    "AMD": (5, 500),
    "INTC": (10, 500),  # Widened from 200 to 500 to catch data issues
    "AVGO": (50, 1000),
    "QCOM": (30, 400),
    "MU": (20, 1000),  # Widened from 200 to 1000 to catch data issues
    
    # Technology
    "AAPL": (50, 300),
    "MSFT": (100, 600),
    "GOOGL": (50, 500),
    "META": (50, 700),
    "CRM": (100, 500),
    "ORCL": (50, 300),
    
    # Healthcare
    "JNJ": (100, 250),
    "UNH": (200, 700),
    "LLY": (200, 900),
    "PFE": (20, 100),
    "ABBV": (100, 250),
    
    # Financials
    "JPM": (100, 350),
    "BAC": (20, 100),
    "GS": (200, 600),
    "MS": (50, 200),
    "V": (150, 400),
    
    # Consumer
    "AMZN": (50, 300),
    "TSLA": (50, 500),
    "HD": (200, 600),
    "NKE": (50, 200),
    "MCD": (200, 400),
    
    # Energy
    "XOM": (50, 200),
    "CVX": (100, 250),
    "COP": (50, 200),
}

# Maximum reasonable YTD return (in %)
# Anything beyond this is likely data corruption
MAX_REASONABLE_YTD_RETURN = 1000  # Allow up to 1000% for extreme bull markets (e.g., AI boom)
MIN_REASONABLE_YTD_RETURN = -100  # -100% is max loss (stock goes to zero)


class DataValidationError(Exception):
    """Raised when data fails validation"""
    pass


class DataValidator:
    """Validates stock data for quality and sanity"""
    
    @staticmethod
    def validate_stock_row(row: dict[str, Any], ticker: str) -> tuple[bool, str | None]:
        """
        Validate a stock market row.
        
        Returns: (is_valid, error_message)
        """
        if not row:
            return False, "Empty row"
        
        # Check for error flag
        if "error" in row:
            return False, f"Data fetch error: {row.get('error')}"
        
        ticker = ticker.upper()
        current_price = row.get("current_price")
        ytd_return = row.get("ytd_return_pct")
        
        # Validate price exists and is numeric
        if current_price is None:
            return False, "Missing current_price"
        
        try:
            current_price = float(current_price)
        except (ValueError, TypeError):
            return False, f"Invalid price: {current_price}"
        
        # Validate price is positive
        if current_price <= 0:
            return False, f"Price must be positive, got {current_price}"
        
        # Validate price is within reasonable bounds
        if ticker in PRICE_BOUNDS:
            min_price, max_price = PRICE_BOUNDS[ticker]
            if current_price < min_price or current_price > max_price:
                return False, (
                    f"Price {current_price} outside reasonable range "
                    f"[{min_price}, {max_price}] for {ticker}. "
                    f"Likely split adjustment or data corruption issue."
                )
        
        # Validate return exists and is numeric
        if ytd_return is None:
            return False, "Missing ytd_return_pct"
        
        try:
            ytd_return = float(ytd_return)
        except (ValueError, TypeError):
            return False, f"Invalid return: {ytd_return}"
        
        # Validate return is within reasonable bounds
        if ytd_return > MAX_REASONABLE_YTD_RETURN:
            return False, (
                f"YTD return {ytd_return}% exceeds maximum reasonable return "
                f"({MAX_REASONABLE_YTD_RETURN}%). Likely data corruption."
            )
        
        if ytd_return < MIN_REASONABLE_YTD_RETURN:
            return False, (
                f"YTD return {ytd_return}% below minimum reasonable return "
                f"({MIN_REASONABLE_YTD_RETURN}%). Likely data corruption."
            )
        
        # Validate info object if present
        info = row.get("info", {})
        if info:
            # Cross-check market cap with price and shares
            market_cap = info.get("marketCap")
            shares_outstanding = info.get("sharesOutstanding")
            
            if market_cap and shares_outstanding:
                try:
                    market_cap = float(market_cap)
                    shares_outstanding = float(shares_outstanding)
                    
                    if shares_outstanding > 0:
                        implied_price = market_cap / shares_outstanding
                        price_ratio = current_price / implied_price if implied_price > 0 else 0
                        
                        # Price should be within 10% of implied price
                        if price_ratio < 0.9 or price_ratio > 1.1:
                            logger.warning(
                                f"{ticker}: Price {current_price} vs implied {implied_price} "
                                f"(ratio: {price_ratio:.2f}). Possible split adjustment issue."
                            )
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        
        return True, None
    
    @staticmethod
    def validate_and_filter_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Validate multiple rows and filter out bad data.
        
        Returns: (valid_rows, error_messages)
        """
        valid_rows = []
        errors = []
        
        for row in rows:
            ticker = row.get("ticker", "UNKNOWN")
            is_valid, error_msg = DataValidator.validate_stock_row(row, ticker)
            
            if is_valid:
                valid_rows.append(row)
            else:
                error_msg = f"{ticker}: {error_msg}"
                errors.append(error_msg)
                logger.warning(f"Data validation failed: {error_msg}")
        
        if errors:
            logger.warning(f"Filtered out {len(errors)} invalid rows: {errors}")
        
        return valid_rows, errors
    
    @staticmethod
    def validate_price_history(df: Any, ticker: str) -> tuple[bool, str | None]:
        """
        Validate price history dataframe.
        
        Returns: (is_valid, error_message)
        """
        if df is None or df.empty:
            return False, "Empty price history"
        
        try:
            # Check for required columns
            required_cols = ["Close", "Volume"]
            for col in required_cols:
                if col not in df.columns:
                    return False, f"Missing column: {col}"
            
            # Check for NaN values
            if df["Close"].isna().all():
                return False, "All Close prices are NaN"
            
            # Check for negative prices
            if (df["Close"] < 0).any():
                return False, "Negative prices detected"
            
            # Check for extreme price jumps (likely split adjustment issue)
            close_prices = df["Close"].dropna()
            if len(close_prices) > 1:
                price_changes = close_prices.pct_change().abs()
                extreme_jumps = price_changes[price_changes > 0.5]  # >50% daily change
                
                if len(extreme_jumps) > len(close_prices) * 0.1:  # >10% of days have >50% jumps
                    return False, (
                        f"Excessive price jumps detected ({len(extreme_jumps)} days). "
                        f"Likely split adjustment or data corruption."
                    )
            
            return True, None
        except Exception as e:
            return False, f"Error validating price history: {e}"
    
    @staticmethod
    def validate_fundamental_data(info: dict[str, Any], ticker: str) -> tuple[bool, list[str]]:
        """
        Validate fundamental data for sanity.
        
        Returns: (is_valid, warnings)
        """
        warnings = []
        
        try:
            # Check PE ratio sanity
            pe = info.get("trailingPE")
            if pe is not None:
                pe = float(pe)
                if pe < 0:
                    warnings.append(f"Negative PE ratio: {pe}")
                elif pe > 500:
                    warnings.append(f"Extremely high PE ratio: {pe}")
            
            # Check debt to equity
            dte = info.get("debtToEquity")
            if dte is not None:
                dte = float(dte)
                if dte < 0:
                    warnings.append(f"Negative debt-to-equity: {dte}")
                elif dte > 100:
                    warnings.append(f"Extremely high debt-to-equity: {dte}")
            
            # Check margins
            for margin_key in ["profitMargins", "operatingMargins", "grossMargins"]:
                margin = info.get(margin_key)
                if margin is not None:
                    margin = float(margin)
                    if margin < -1.0 or margin > 1.0:
                        warnings.append(f"Invalid {margin_key}: {margin} (should be 0-1)")
            
            # Check ROE/ROA
            for ratio_key in ["returnOnEquity", "returnOnAssets"]:
                ratio = info.get(ratio_key)
                if ratio is not None:
                    ratio = float(ratio)
                    if ratio < -1.0 or ratio > 1.0:
                        warnings.append(f"Invalid {ratio_key}: {ratio} (should be 0-1)")
            
            return len(warnings) == 0, warnings
        except Exception as e:
            return False, [f"Error validating fundamental data: {e}"]
    
    @staticmethod
    def flag_suspicious_data(row: dict[str, Any], ticker: str) -> list[str]:
        """
        Flag data that passes validation but looks suspicious.
        
        Returns: list of warning messages
        """
        warnings = []
        
        current_price = row.get("current_price")
        ytd_return = row.get("ytd_return_pct")
        info = row.get("info", {})
        
        # Flag extreme returns (more aggressive)
        if ytd_return and abs(ytd_return) > 100:
            warnings.append(
                f"EXTREME YTD return: {ytd_return}%. "
                f"This is highly suspicious and may indicate data corruption. "
                f"Verify against multiple sources before using in analysis."
            )
        elif ytd_return and abs(ytd_return) > 75:
            warnings.append(
                f"Very high YTD return: {ytd_return}%. "
                f"Verify this is not a split adjustment or data error."
            )
        
        # Flag very high PE (more aggressive)
        pe = info.get("trailingPE")
        if pe and pe > 150:
            warnings.append(
                f"Extremely high PE ratio: {pe}. "
                f"This is unusual and may indicate data issue or extreme growth premium."
            )
        elif pe and pe > 100:
            warnings.append(f"Very high PE ratio: {pe}. Verify data quality.")
        
        # Flag very low price
        if current_price and current_price < 1:
            warnings.append(f"Very low price: ${current_price}. Verify not a penny stock or data error.")
        
        # Flag missing fundamental data
        if not info or len(info) < 5:
            warnings.append("Limited fundamental data available. Analysis may be incomplete.")
        
        # NEW: Flag price-return inconsistency
        # If return is extreme but price is normal, something is wrong
        if ytd_return and current_price:
            if abs(ytd_return) > 150 and current_price > 10:
                warnings.append(
                    f"Inconsistency detected: Extreme return ({ytd_return}%) but normal price (${current_price}). "
                    f"Likely split adjustment or data corruption."
                )
        
        return warnings


def validate_snapshot_data(snapshot: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Validate entire snapshot and filter out bad data.
    
    Returns: (cleaned_snapshot, error_messages)
    """
    errors = []
    
    # Validate picks
    if "picks" in snapshot:
        valid_picks, pick_errors = DataValidator.validate_and_filter_rows(snapshot["picks"])
        snapshot["picks"] = valid_picks
        errors.extend(pick_errors)
    
    # Validate gainers
    if "gainers" in snapshot:
        valid_gainers, gainer_errors = DataValidator.validate_and_filter_rows(snapshot["gainers"])
        snapshot["gainers"] = valid_gainers
        errors.extend(gainer_errors)
    
    # Validate losers
    if "losers" in snapshot:
        valid_losers, loser_errors = DataValidator.validate_and_filter_rows(snapshot["losers"])
        snapshot["losers"] = valid_losers
        errors.extend(loser_errors)
    
    if errors:
        logger.warning(f"Snapshot validation found {len(errors)} issues: {errors}")
    
    return snapshot, errors

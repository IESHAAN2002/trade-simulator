"""
Maker-Taker Model for Crypto Trading Simulator

This module implements a model to predict the maker/taker proportion
for cryptocurrency trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional
from sklearn.linear_model import LogisticRegression
import logging

logger = logging.getLogger("maker_taker_model")


class FeeModel:
    """Rule-based model for calculating trading fees based on exchange tiers."""

    # OKX fee tiers (https://www.okx.com/help-center/gettingStarted/spot-trading-fee-rates)
    FEE_TIERS = {
        "Tier 1 (0.1%)": {"maker": 0.0008, "taker": 0.001},   # VIP 0
        "Tier 2 (0.08%)": {"maker": 0.0006, "taker": 0.0008}, # VIP 1
        "Tier 3 (0.05%)": {"maker": 0.0004, "taker": 0.0005}, # VIP 2
        "Custom": {"maker": 0.0002, "taker": 0.0003},         # Customizable
    }

    def __init__(self, fee_tier: str = "Tier 1 (0.1%)"):
        """
        Initialize the fee model.
        
        Args:
            fee_tier: The fee tier to use for calculations
        """
        self.set_fee_tier(fee_tier)
    
    def set_fee_tier(self, fee_tier: str) -> None:
        """
        Set the current fee tier.
        
        Args:
            fee_tier: The fee tier to use
        """
        if fee_tier in self.FEE_TIERS:
            self.fee_tier = fee_tier
            self.maker_fee = self.FEE_TIERS[fee_tier]["maker"]
            self.taker_fee = self.FEE_TIERS[fee_tier]["taker"]
        else:
            logger.warning(f"Unknown fee tier: {fee_tier}. Using Tier 1 as default.")
            self.fee_tier = "Tier 1 (0.1%)"
            self.maker_fee = self.FEE_TIERS["Tier 1 (0.1%)"]["maker"]
            self.taker_fee = self.FEE_TIERS["Tier 1 (0.1%)"]["taker"]
    
    def calculate_fees(self, trade_size: float, maker_ratio: float = 0.0) -> Dict[str, float]:
        """
        Calculate trading fees for a given trade size.
        
        Args:
            trade_size: The total size of the trade in USD
            maker_ratio: Proportion of the trade executed as maker (0.0 to 1.0)
            
        Returns:
            Dictionary with fee details
        """
        taker_size = trade_size * (1 - maker_ratio)
        maker_size = trade_size * maker_ratio
        
        taker_fee_amount = taker_size * self.taker_fee
        maker_fee_amount = maker_size * self.maker_fee
        total_fee = taker_fee_amount + maker_fee_amount
        
        return {
            "maker_fee_rate": self.maker_fee,
            "taker_fee_rate": self.taker_fee,
            "maker_fee_amount": maker_fee_amount,
            "taker_fee_amount": taker_fee_amount,
            "total_fee": total_fee,
            "fee_percentage": (total_fee / trade_size) * 100 if trade_size > 0 else 0,
        }


class MakerTakerModel:
    """Model for predicting maker/taker proportion for a trade."""
    
    def __init__(self):
        """Initialize the maker/taker prediction model."""
        self.model = LogisticRegression()
        self.is_trained = False
    
    def predict_maker_ratio(self, orderbook: Dict[str, pd.DataFrame], quantity: float, order_type: str = "Market") -> float:
        """
        Predict the maker/taker ratio for a given trade.
        
        Args:
            orderbook: Dictionary with 'asks' and 'bids' DataFrames
            quantity: Trade quantity
            order_type: Type of order (Market, Limit, etc.)
            
        Returns:
            Predicted maker ratio (0.0 to 1.0)
        """
        # For non-market orders, we use different default maker ratios
        if order_type.lower() != "market":
            if order_type.lower() == "limit":
                return 0.8  # Limit orders are predominantly maker
            elif order_type.lower() in ["stop-limit", "take-profit"]:
                return 0.5  # Conditional orders can be either
            return 0.0
            
        # Extract features from orderbook
        asks_df = orderbook['asks']
        bids_df = orderbook['bids']
        
        if asks_df.empty or bids_df.empty:
            return 0.0  # Default to all taker if orderbook is empty
        
        # Calculate spread
        best_ask = asks_df.iloc[0]['price']
        best_bid = bids_df.iloc[0]['price']
        spread = best_ask - best_bid
        spread_pct = spread / best_bid if best_bid > 0 else 0
        
        # Calculate top volume
        ask_vol = asks_df.iloc[0]['size']
        bid_vol = bids_df.iloc[0]['size']
        
        # Simple heuristic: larger trades are more likely to be taker
        # Tight spreads with high volume increase chance of maker orders
        
        # For market orders, we default to mostly taker
        maker_ratio = 0.0
        
        # If the quantity is small compared to available volume, 
        # some portion might be filled as maker
        vol_ratio = min(quantity / ask_vol, 1.0) if ask_vol > 0 else 1.0
        
        # Tight spread increases maker probability
        spread_factor = min(0.0001 / (spread_pct if spread_pct > 0 else 0.0001), 0.2)
        
        # Simple heuristic model
        maker_ratio = max(0.0, 0.05 + spread_factor - vol_ratio * 0.1)
        
        # Cap at 0.2 for market orders (realistic upper bound)
        maker_ratio = min(maker_ratio, 0.2)
        
        return maker_ratio
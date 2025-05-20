"""
Slippage Model for Crypto Trading Simulator

This module implements predictive models for estimating slippage in cryptocurrency trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from sklearn.linear_model import LinearRegression, QuantileRegressor
import logging

logger = logging.getLogger("slippage_model")


class SlippageModel:
    """Predictive model for estimating slippage in crypto trades."""
    
    def __init__(self, model_type: str = "linear"):
        """
        Initialize the slippage prediction model.
        
        Args:
            model_type: Type of regression model to use ("linear" or "quantile")
        """
        self.model_type = model_type.lower()
        
        if self.model_type == "linear":
            self.model = LinearRegression()
        elif self.model_type == "quantile":
            # Use 75th percentile for conservative slippage estimation
            self.model = QuantileRegressor(quantile=0.75, alpha=0.5)
        else:
            logger.warning(f"Unknown model type: {model_type}. Using linear regression.")
            self.model_type = "linear"
            self.model = LinearRegression()
        
        self.is_trained = False
        
    def _extract_features(
        self, 
        orderbook: Dict[str, pd.DataFrame], 
        quantity: float,
        side: str = "buy"
    ) -> np.ndarray:
        """
        Extract features from orderbook for slippage prediction.
        
        Args:
            orderbook: Dictionary with 'asks' and 'bids' DataFrames
            quantity: Trade quantity in base currency
            side: Trade side ("buy" or "sell")
            
        Returns:
            Feature array for prediction
        """
        features = []
        
        # Use asks for buy orders, bids for sell orders
        book_side = orderbook['asks'] if side.lower() == "buy" else orderbook['bids']
        
        if book_side.empty:
            return np.array([0.0, 0.0, 0.0, 0.0, 0.0]).reshape(1, -1)
        
        # Calculate basic orderbook metrics
        best_price = book_side.iloc[0]['price']
        depth_1pct = self._calculate_depth(book_side, best_price, 0.01)
        depth_2pct = self._calculate_depth(book_side, best_price, 0.02)
        
        # Calculate size-to-depth ratio (higher value means higher potential slippage)
        size_depth_ratio = quantity / depth_1pct if depth_1pct > 0 else 10.0
        
        # Calculate book imbalance
        ask_depth = self._calculate_depth(orderbook['asks'], 
                                        orderbook['asks'].iloc[0]['price'] if not orderbook['asks'].empty else 0, 
                                        0.01)
        bid_depth = self._calculate_depth(orderbook['bids'], 
                                        orderbook['bids'].iloc[0]['price'] if not orderbook['bids'].empty else 0, 
                                        0.01)
        book_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
        
        # Features: [quantity, size_depth_ratio, depth_1pct, depth_2pct, book_imbalance]
        features = [quantity, size_depth_ratio, depth_1pct, depth_2pct, book_imbalance]
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_depth(self, book_side: pd.DataFrame, reference_price: float, price_range: float) -> float:
        """
        Calculate the available liquidity within a price range.
        
        Args:
            book_side: DataFrame containing one side of the orderbook
            reference_price: Price to calculate depth around
            price_range: Price range as a fraction of reference price
            
        Returns:
            Total available liquidity (size) within the price range
        """
        if book_side.empty or reference_price <= 0:
            return 0.0
        
        price_limit = reference_price * (1 + price_range)
        
        # For asks, we want price <= price_limit
        # For bids, we want price >= price_limit
        if 'price' in book_side.columns and book_side.iloc[0]['price'] > book_side.iloc[-1]['price']:
            # This is a bid book (descending prices)
            depth_df = book_side[book_side['price'] >= reference_price * (1 - price_range)]
        else:
            # This is an ask book (ascending prices)
            depth_df = book_side[book_side['price'] <= price_limit]
        
        return depth_df['size'].sum() if not depth_df.empty else 0.0
    
    def predict_slippage(
        self, 
        orderbook: Dict[str, pd.DataFrame], 
        quantity: float,
        side: str = "buy",
        slippage_tolerance: float = 0.5
    ) -> Dict[str, float]:
        """
        Predict slippage for a given trade.
        
        Args:
            orderbook: Dictionary with 'asks' and 'bids' DataFrames
            quantity: Trade quantity in base currency
            side: Trade side ("buy" or "sell")
            slippage_tolerance: Maximum acceptable slippage percentage
            
        Returns:
            Dictionary with slippage details
        """
        # For simplicity, we'll use a model based purely on the orderbook
        # without historical training data
        
        # Extract relevant orderbook data
        book_side = orderbook['asks'] if side.lower() == "buy" else orderbook['bids']
        
        if book_side.empty:
            logger.warning("Empty orderbook side, cannot estimate slippage accurately")
            return {
                "estimated_slippage_pct": slippage_tolerance,
                "estimated_slippage_price": 0.0,
                "max_acceptable_slippage_pct": slippage_tolerance
            }
        
        # Calculate estimated execution price
        execution_price, slippage_pct = self._calculate_execution_price(book_side, quantity, side)
        
        # If slippage exceeds tolerance, cap it at the tolerance level
        capped_slippage = min(slippage_pct, slippage_tolerance)
        
        # Record model features for potential future training
        features = self._extract_features(orderbook, quantity, side)
        
        return {
            "estimated_slippage_pct": slippage_pct,
            "estimated_slippage_price": execution_price,
            "max_acceptable_slippage_pct": slippage_tolerance
        }
    
    def _calculate_execution_price(
        self, 
        book_side: pd.DataFrame, 
        quantity: float,
        side: str = "buy"
    ) -> Tuple[float, float]:
        """
        Calculate estimated execution price by walking the book.
        
        Args:
            book_side: DataFrame for the relevant side of the orderbook
            quantity: Trade quantity to execute
            side: Trade side ("buy" or "sell")
            
        Returns:
            Tuple of (execution_price, slippage_percentage)
        """
        if book_side.empty:
            return 0.0, 0.0
        
        remaining_qty = quantity
        notional_total = 0.0
        
        # Reference price (best available price)
        reference_price = book_side.iloc[0]['price']
        
        # Walk the book to calculate execution price
        for _, level in book_side.iterrows():
            level_price = level['price']
            level_size = level['size']
            
            if remaining_qty <= level_size:
                # This level can fill the remaining quantity
                notional_total += remaining_qty * level_price
                remaining_qty = 0
                break
            else:
                # Take all available at this level and continue
                notional_total += level_size * level_price
                remaining_qty -= level_size
        
        # If we couldn't fill the entire order from the book
        if remaining_qty > 0:
            # Use the last available price for the remaining quantity
            if not book_side.empty:
                last_price = book_side.iloc[-1]['price']
                notional_total += remaining_qty * last_price
            else:
                # This should not happen, but just in case
                return reference_price, 0.0
        
        # Calculate average execution price
        executed_qty = quantity - remaining_qty
        if executed_qty > 0:
            avg_execution_price = notional_total / quantity
            
            # Calculate slippage percentage
            if side.lower() == "buy":
                slippage_pct = (avg_execution_price - reference_price) / reference_price * 100
            else:
                slippage_pct = (reference_price - avg_execution_price) / reference_price * 100
                
            return avg_execution_price, slippage_pct
        
        return reference_price, 0.0
"""
Market Impact Model for Crypto Trading Simulator

This module implements the Almgren-Chriss model for estimating market impact
of cryptocurrency trades.

Reference: https://www.linkedin.com/pulse/understanding-almgren-chriss-model-optimal-portfolio-execution-pal-pmeqc/
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import logging
import math

logger = logging.getLogger("market_impact_model")


class AlmgrenChrissModel:
    """Implementation of the Almgren-Chriss market impact model."""
    
    def __init__(
        self, 
        permanent_impact_factor: float = 2.5e-6,
        temporary_impact_factor: float = 1.5e-5,
        volatility_scaling: bool = True
    ):
        """
        Initialize the Almgren-Chriss market impact model.
        
        Args:
            permanent_impact_factor: Factor for permanent market impact
            temporary_impact_factor: Factor for temporary market impact
            volatility_scaling: Whether to scale impact by volatility
        """
        self.permanent_impact_factor = permanent_impact_factor
        self.temporary_impact_factor = temporary_impact_factor
        self.volatility_scaling = volatility_scaling
        
    def estimate_market_impact(
        self, 
        orderbook: Dict[str, pd.DataFrame],
        quantity: float,
        side: str = "buy",
        market_volatility: float = 0.05,
        execution_timeframe: float = 1.0  # in seconds
    ) -> Dict[str, float]:
        """
        Estimate market impact for a given trade based on Almgren-Chriss model.
        
        Args:
            orderbook: Dictionary with 'asks' and 'bids' DataFrames
            quantity: Trade quantity in base currency
            side: Trade side ("buy" or "sell")
            market_volatility: Asset price volatility (daily)
            execution_timeframe: Time to execute the order in seconds
            
        Returns:
            Dictionary with market impact details
        """
        # Extract orderbook data
        asks_df = orderbook['asks']
        bids_df = orderbook['bids']
        
        if asks_df.empty or bids_df.empty:
            logger.warning("Empty orderbook, cannot estimate market impact accurately")
            return {
                "temporary_impact": 0.0,
                "permanent_impact": 0.0,
                "total_impact": 0.0,
                "impact_bps": 0.0
            }
        
        # Get best prices from the orderbook
        best_ask = asks_df.iloc[0]['price']
        best_bid = bids_df.iloc[0]['price']
        mid_price = (best_ask + best_bid) / 2
        
        # Calculate order size in notional value
        notional_value = quantity * mid_price
        
        # Calculate market depth metrics
        market_depth = self._calculate_market_depth(orderbook)
        
        # Scale impact factors by market depth and volatility
        adjusted_permanent_factor = self.permanent_impact_factor
        adjusted_temporary_factor = self.temporary_impact_factor
        
        if self.volatility_scaling:
            # Convert daily volatility to the execution timeframe
            timeframe_volatility = market_volatility * math.sqrt(execution_timeframe / (24 * 3600))
            
            # Scale impact factors by volatility
            volatility_scale = max(0.5, min(2.0, timeframe_volatility / 0.01))
            adjusted_permanent_factor *= volatility_scale
            adjusted_temporary_factor *= volatility_scale
        
        # Scale by market depth (thinner books should have higher impact)
        depth_scale = max(0.5, min(3.0, 1.0 / (market_depth / notional_value)))
        adjusted_permanent_factor *= depth_scale
        adjusted_temporary_factor *= depth_scale
        
        # Calculate market impact components
        # 1. Permanent impact: Effect on market price (remains after trade)
        permanent_impact = adjusted_permanent_factor * notional_value
        
        # 2. Temporary impact: Immediate price movement (reverts over time)
        temporary_impact = adjusted_temporary_factor * notional_value * math.sqrt(1.0 / execution_timeframe)
        
        # Total market impact
        total_impact = permanent_impact + temporary_impact
        
        # Convert to basis points
        impact_bps = (total_impact / mid_price) * 10000
        
        return {
            "temporary_impact": temporary_impact,
            "permanent_impact": permanent_impact,
            "total_impact": total_impact,
            "impact_bps": impact_bps
        }
    
    def _calculate_market_depth(self, orderbook: Dict[str, pd.DataFrame]) -> float:
        """
        Calculate market depth as available liquidity within 1% of mid price.
        
        Args:
            orderbook: Dictionary with 'asks' and 'bids' DataFrames
            
        Returns:
            Market depth as notional value
        """
        asks_df = orderbook['asks']
        bids_df = orderbook['bids']
        
        if asks_df.empty or bids_df.empty:
            return 1000.0  # Default value if orderbook is empty
        
        # Calculate mid price
        mid_price = (asks_df.iloc[0]['price'] + bids_df.iloc[0]['price']) / 2
        
        # Define price range (1% from mid price)
        upper_bound = mid_price * 1.01
        lower_bound = mid_price * 0.99
        
        # Filter orders within range
        asks_in_range = asks_df[asks_df['price'] <= upper_bound]
        bids_in_range = bids_df[bids_df['price'] >= lower_bound]
        
        # Calculate total notional value
        ask_notional = (asks_in_range['price'] * asks_in_range['size']).sum()
        bid_notional = (bids_in_range['price'] * bids_in_range['size']).sum()
        
        return ask_notional + bid_notional
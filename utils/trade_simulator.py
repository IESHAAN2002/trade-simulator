
"""
Trade Simulator core module for Crypto Trading Simulator.

This module integrates various models to simulate trades and estimate costs.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor

# Import project modules
from models.maker_taker_model import FeeModel, MakerTakerModel
from models.slippage_model import SlippageModel
from models.market_impact import AlmgrenChrissModel
from utils.latency_tracker import LatencyTracker
from websocket.okx_client import OkxOrderbookClient

logger = logging.getLogger("trade_simulator")


class TradeSimulator:
    """Core class that integrates models to simulate cryptocurrency trades."""
    
    def __init__(self):
        """Initialize the trade simulator with required models."""
        # Initialize models
        self.fee_model = FeeModel()
        self.maker_taker_model = MakerTakerModel()
        self.slippage_model = SlippageModel()
        self.market_impact_model = AlmgrenChrissModel()
        
        # Initialize orderbook client (placeholder, will be set later)
        self.orderbook_client = None
        
        # Initialize performance tracker
        self.latency_tracker = LatencyTracker()
        
        # Flag to track if simulator is running
        self.is_running = False
        
        # Cache for simulation results
        self.last_simulation_results = {}
        
        # Thread pool for non-blocking operations
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
    
    async def initialize(self, ws_url: str = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP") -> None:
        """
        Initialize the simulator and establish WebSocket connection.
        
        Args:
            ws_url: WebSocket URL for orderbook data
        """
        logger.info("Initializing Trade Simulator...")
        
        # Initialize orderbook client
        self.orderbook_client = OkxOrderbookClient(ws_url=ws_url)
        
        # Connect to WebSocket
        try:
            await self.orderbook_client.connect()
            client_task = asyncio.create_task(self.orderbook_client.start())
            self.is_running = True
            logger.info("Trade Simulator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Trade Simulator: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Properly shutdown the simulator and close connections."""
        logger.info("Shutting down Trade Simulator...")
        self.is_running = False
        
        if self.orderbook_client:
            await self.orderbook_client.stop()
        
        self.thread_pool.shutdown(wait=True)
        logger.info("Trade Simulator shutdown complete")
    
    def get_orderbook_snapshot(self) -> Dict[str, pd.DataFrame]:
        """
        Get the current orderbook snapshot.
        
        Returns:
            Dictionary with orderbook data
        """
        if not self.orderbook_client:
            logger.warning("Orderbook client not initialized")
            return {'asks': pd.DataFrame(), 'bids': pd.DataFrame()}
        
        return self.orderbook_client.get_orderbook_snapshot()
    
    def simulate_trade(
        self,
        exchange: str,
        asset: str,
        order_type: str,
        quantity: float,
        fee_tier: str,
        slippage_tolerance: float,
        side: str = "buy",
        market_volatility: float = 0.05
    ) -> Dict[str, Any]:
        """
        Simulate a trade and calculate expected costs.
        
        Args:
            exchange: Exchange name (e.g., "OKX")
            asset: Asset name (e.g., "BTC-USDT")
            order_type: Order type (e.g., "Market", "Limit")
            quantity: Trade quantity
            fee_tier: Fee tier name
            slippage_tolerance: Maximum acceptable slippage percentage
            side: Trade side ("buy" or "sell")
            market_volatility: Market volatility as percentage
            
        Returns:
            Dictionary with simulation results
        """
        # Start timing
        self.latency_tracker.start("trade_simulation")
        
        # Step 1: Get current orderbook data
        orderbook = self.get_orderbook_snapshot()
        if 'asks' not in orderbook or 'bids' not in orderbook or orderbook['asks'].empty or orderbook['bids'].empty:
            logger.warning("Cannot simulate trade: Empty orderbook")
            return {
                "success": False,
                "error": "Empty orderbook data"
            }
        
        # Step 2: Calculate base values
        mid_price = (orderbook['asks'].iloc[0]['price'] + orderbook['bids'].iloc[0]['price']) / 2
        notional_value = quantity * mid_price
        
        # Step 3: Predict maker/taker proportion
        self.latency_tracker.start("maker_taker_prediction")
        maker_ratio = self.maker_taker_model.predict_maker_ratio(orderbook, quantity, order_type)
        maker_taker_latency = self.latency_tracker.stop("maker_taker_prediction")
        
        # Step 4: Calculate fees
        self.latency_tracker.start("fee_calculation")
        self.fee_model.set_fee_tier(fee_tier)
        fee_result = self.fee_model.calculate_fees(notional_value, maker_ratio)
        fee_latency = self.latency_tracker.stop("fee_calculation")
        
        # Step 5: Estimate slippage
        self.latency_tracker.start("slippage_estimation")
        slippage_result = self.slippage_model.predict_slippage(
            orderbook, quantity, side, slippage_tolerance
        )
        slippage_latency = self.latency_tracker.stop("slippage_estimation")
        
        # Step 6: Estimate market impact
        self.latency_tracker.start("market_impact_estimation")
        impact_result = self.market_impact_model.estimate_market_impact(
            orderbook, quantity, side, market_volatility
        )
        impact_latency = self.latency_tracker.stop("market_impact_estimation")
        
        # Step 7: Calculate execution price
        reference_price = orderbook['asks'].iloc[0]['price'] if side.lower() == "buy" else orderbook['bids'].iloc[0]['price']
        slippage_amount = (slippage_result['estimated_slippage_pct'] / 100) * reference_price
        impact_amount = impact_result['total_impact']
        
        if side.lower() == "buy":
            execution_price = reference_price + slippage_amount + impact_amount
        else:
            execution_price = reference_price - slippage_amount - impact_amount
        
        # Step 8: Calculate total cost
        execution_cost = quantity * execution_price
        total_fee = fee_result['total_fee']
        total_cost = execution_cost + total_fee if side.lower() == "buy" else execution_cost - total_fee
        total_cost_percentage = ((total_cost / notional_value) - 1) * 100 if side.lower() == "buy" else ((1 - total_cost / notional_value)) * 100
        
        # Stop timing and calculate total latency
        total_latency = self.latency_tracker.stop("trade_simulation")
        
        # Compile simulation results
        simulation_results = {
            "success": True,
            "timestamp": time.time(),
            "exchange": exchange,
            "asset": asset,
            "order_type": order_type,
            "quantity": quantity,
            "side": side,
            "reference_price": reference_price,
            "maker_ratio": maker_ratio,
            "fees": {
                "maker_fee_rate": fee_result['maker_fee_rate'],
                "taker_fee_rate": fee_result['taker_fee_rate'],
                "total_fee": fee_result['total_fee'],
                "fee_percentage": fee_result['fee_percentage']
            },
            "slippage": {
                "estimated_pct": slippage_result['estimated_slippage_pct'],
                "max_tolerance": slippage_result['max_acceptable_slippage_pct']
            },
            "market_impact": {
                "temporary": impact_result['temporary_impact'],
                "permanent": impact_result['permanent_impact'],
                "total": impact_result['total_impact'],
                "bps": impact_result['impact_bps']
            },
            "execution": {
                "price": execution_price,
                "cost": execution_cost,
                "total_cost": total_cost,
                "total_cost_percentage": total_cost_percentage
            },
            "performance": {
                "total_latency_ms": total_latency,
                "maker_taker_latency_ms": maker_taker_latency,
                "fee_latency_ms": fee_latency,
                "slippage_latency_ms": slippage_latency,
                "impact_latency_ms": impact_latency
            }
        }
        
        # Cache the result
        self.last_simulation_results = simulation_results
        
        return simulation_results
    
    def get_latency_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the simulator.
        
        Returns:
            Dictionary with latency statistics
        """
        return self.latency_tracker.get_all_stats()
    
    def get_orderbook_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current orderbook status.
        
        Returns:
            Dictionary with orderbook summary
        """
        orderbook = self.get_orderbook_snapshot()
        
        if 'asks' not in orderbook or 'bids' not in orderbook or orderbook['asks'].empty or orderbook['bids'].empty:
            return {
                "status": "No data",
                "spread": 0.0,
                "depth": 0.0
            }
        
        asks_df = orderbook['asks']
        bids_df = orderbook['bids']
        
        best_ask = asks_df.iloc[0]['price']
        best_bid = bids_df.iloc[0]['price']
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100
        
        # Calculate visible liquidity
        ask_depth = (asks_df['price'] * asks_df['size']).sum()
        bid_depth = (bids_df['price'] * bids_df['size']).sum()
        
        return {
            "status": "Active",
            "best_ask": best_ask,
            "best_bid": best_bid,
            "mid_price": (best_ask + best_bid) / 2,
            "spread": spread,
            "spread_pct": spread_pct,
            "ask_depth": ask_depth,
            "bid_depth": bid_depth,
            "book_imbalance": (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0,
            "last_update_latency": orderbook.get('last_latency_ms', 0)
        }
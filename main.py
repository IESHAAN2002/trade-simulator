"""
Crypto Trading Simulator - Main Application

This script initializes and runs the crypto trading simulator, connecting:
- WebSocket client for real-time orderbook data
- Trade simulation models
- User interface

Usage:
    python main.py
"""

import asyncio
import sys
import logging
import tkinter as tk
import threading
import time
from datetime import datetime
from tkinter import ttk
import asyncio
from websocket.okx_client import OkxOrderbookClient
# Import the UI class
from ui.simulator_ui import CryptoTradeSimulator

# Placeholder for modules that would be imported in a complete application
# For demonstration purposes, we'll create minimal mock versions

class MockLogger:
    """Simple logger for demonstration purposes"""
    def __init__(self, name, level):
        self.name = name
        self.level = level

    def info(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        print(f"{timestamp} - {self.name} - INFO - {message}")

    def error(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        print(f"{timestamp} - {self.name} - ERROR - {message}")

    def critical(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        print(f"{timestamp} - {self.name} - CRITICAL - {message}")

def setup_logger(name, level):
    """Mock setup logger function"""
    return MockLogger(name, level)

class MockTradeSimulator:
    """Mock trade simulator for demonstration purposes"""
    def __init__(self):
        self.connected = False
        self.orderbook = {
            "asks": [
                {"price": 29880.00, "size": 1.5000},
                {"price": 29881.50, "size": 0.7500},
                {"price": 29883.00, "size": 2.1000},
                {"price": 29885.00, "size": 3.0000},
                {"price": 29890.00, "size": 5.0000}
            ],
            "bids": [
                {"price": 29875.00, "size": 1.2000},
                {"price": 29873.50, "size": 0.8500},
                {"price": 29870.00, "size": 2.5000},
                {"price": 29868.00, "size": 1.7500},
                {"price": 29865.00, "size": 3.5000}
            ]
        }

    async def initialize(self):
        """Mock initialization"""
        await asyncio.sleep(1)  # Simulate network connection time
        self.connected = True
        return True

    async def shutdown(self):
        """Mock shutdown"""
        await asyncio.sleep(0.5)  # Simulate disconnect time
        self.connected = False
        return True

    def get_orderbook_summary(self):
        """Return real-time orderbook summary from OKX WebSocket client."""
        if not orderbook_client.running:
            return {"status": "Disconnected"}
        
        snapshot = orderbook_client.get_orderbook_snapshot()
        asks = snapshot['asks']
        bids = snapshot['bids']
        
        if asks.empty or bids.empty:
            return {"status": "Orderbook data not ready"}

        best_ask = asks.iloc[0]['price']
        best_bid = bids.iloc[0]['price']
        spread = best_ask - best_bid
        spread_pct = spread / best_bid if best_bid != 0 else 0

        ask_depth = asks['size'].sum()
        bid_depth = bids['size'].sum()
        book_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) != 0 else 0

        last_latency = snapshot.get('last_latency_ms', 0)

        return {
            "status": "Active",
            "best_ask": round(best_ask, 2),
            "best_bid": round(best_bid, 2),
            "spread": round(spread, 2),
            "spread_pct": round(spread_pct, 4),
            "ask_depth": round(ask_depth, 2),
            "bid_depth": round(bid_depth, 2),
            "book_imbalance": round(book_imbalance, 4),
            "last_update_latency": round(last_latency, 2)
        }

    def get_orderbook_snapshot(self):
        """Return a mock orderbook snapshot"""
        # Create a class to mimic pandas DataFrame for demonstration
        class MockDataFrame:
            def __init__(self, data):
                self.data = data
                self._iloc = MockILoc(data)

            def __len__(self):
                return len(self.data)

            @property
            def iloc(self):
                return self._iloc

        class MockILoc:
            def __init__(self, data):
                self.data = data

            def __getitem__(self, idx):
                return self.data[idx]

        return {
            "asks": MockDataFrame(self.orderbook["asks"]),
            "bids": MockDataFrame(self.orderbook["bids"])
        }

    def simulate_trade(self, **kwargs):
        """Simulate a trade with the given parameters"""
        # Mock a trade simulation result
        side = kwargs.get('side', 'buy')
        quantity = kwargs.get('quantity', 1.0)
        order_type = kwargs.get('order_type', 'Market')
        
        # Calculate mock values based on inputs
        base_price = 29875.00 if side == "buy" else 29880.00
        slippage_pct = 0.15 if order_type == "Market" else 0.05
        
        # Adjust price based on order type and side
        if side == "buy":
            execution_price = base_price * (1 + slippage_pct/100)
        else:
            execution_price = base_price * (1 - slippage_pct/100)
        
        # Calculate fees based on tier
        fee_tier = kwargs.get('fee_tier', 'Tier 1 (0.1%)')
        fee_pct = 0.1  # Default
        if "Tier 2" in fee_tier:
            fee_pct = 0.08
        elif "Tier 3" in fee_tier:
            fee_pct = 0.05
        
        fees = (execution_price * quantity) * (fee_pct / 100)
        final_cost = execution_price * quantity + fees if side == "buy" else execution_price * quantity - fees
        
        return {
            "success": True,
            "slippage": slippage_pct,
            "fees": fees,
            "execution": {
                "price": execution_price,
                "quantity": quantity
            },
            "final_cost": final_cost
        }


# Setup logging
logger = setup_logger("main", logging.INFO)

orderbook_client = OkxOrderbookClient()

async def start_ws_client():
    await orderbook_client.start()

class SimulatorApp:
    """Main application class for the Crypto Trading Simulator."""
    
    def __init__(self):
        """Initialize application components."""
        self.root = None
        self.ui = None
        self.trade_simulator = None
        self.periodic_task = None
        
        # Create the GUI
        self.setup_gui()
        
        # Initialize the simulator
        self.initialize_simulator()
    
    def setup_gui(self):
        """Set up the graphical user interface."""
        logger.info("Setting up GUI...")
        self.root = tk.Tk()
        self.ui = CryptoTradeSimulator(self.root)
        
        # Connect the simulate button to our simulation method
        self.ui.set_simulation_callback(self.run_simulation)
        
        logger.info("GUI setup complete")
    
    def initialize_simulator(self):
        """Initialize the trade simulator."""
        logger.info("Initializing trade simulator...")
        self.trade_simulator = MockTradeSimulator()
        
        # Schedule async initialization
        self.root.after(100, self.schedule_async_initialize)
    
    def schedule_async_initialize(self):
        """Schedule the async initialization on the main thread."""
        threading.Thread(
            target=lambda: asyncio.run(self.async_initialize_simulator()),
            daemon=True
        ).start()
    
    async def async_initialize_simulator(self):
        """Asynchronously initialize WebSocket connections."""
        try:
            # Start your trade simulator first (if needed)
            await self.trade_simulator.initialize()
            logger.info("Trade simulator initialized successfully")
            
            # Start OKX orderbook WebSocket client in background
            asyncio.create_task(start_ws_client())
            
            # Schedule periodic UI update on main thread
            if self.root:
                self.root.after(100, self.schedule_periodic_update)
        except Exception as e:
            logger.error(f"Failed to initialize simulator: {e}")
            if self.ui:
                self.root.after(0, lambda: self.ui.show_error(f"Failed to connect to orderbook: {e}"))
    
    def schedule_periodic_update(self):
        """Schedule periodic updates of the orderbook display."""
        self.update_orderbook_display()
        self.periodic_task = self.root.after(1000, self.schedule_periodic_update)
    
    def update_orderbook_display(self):
        """Update the orderbook display in the UI."""
        if not self.trade_simulator:
            return
        
        try:
            # Get orderbook summary
            summary = self.trade_simulator.get_orderbook_summary()
            
            # Format the orderbook text
            if summary["status"] == "Active":
                orderbook_text = (
                    f"Best Ask: {summary['best_ask']:.2f}\n"
                    f"Best Bid: {summary['best_bid']:.2f}\n"
                    f"Spread: {summary['spread']:.2f} ({summary['spread_pct']:.4f}%)\n\n"
                    f"Ask Depth: ${summary['ask_depth']:.2f}\n"
                    f"Bid Depth: ${summary['bid_depth']:.2f}\n"
                    f"Book Imbalance: {summary['book_imbalance']:.4f}\n\n"
                    f"Last Update: {summary['last_update_latency']:.2f}ms"
                )
                
                # Get full orderbook for detailed display
                orderbook = self.trade_simulator.get_orderbook_snapshot()
                
                # Format top 5 asks and bids
                orderbook_text += "\n\n--- Top 5 Asks ---\n"
                for i in range(min(5, len(orderbook['asks']))):
                    row = orderbook['asks'].iloc[i]
                    orderbook_text += f"${row['price']:.2f} | {row['size']:.4f}\n"
                
                orderbook_text += "\n--- Top 5 Bids ---\n"
                for i in range(min(5, len(orderbook['bids']))):
                    row = orderbook['bids'].iloc[i]
                    orderbook_text += f"${row['price']:.2f} | {row['size']:.4f}\n"
            else:
                orderbook_text = "Waiting for orderbook data..."
            
            # Update the UI
            self.ui.update_orderbook_display(orderbook_text)
            
        except Exception as e:
            logger.error(f"Error updating orderbook display: {e}")
    
    def run_simulation(self):
        """Run the trade simulation based on UI inputs."""
        logger.info("Running trade simulation...")
        
        try:
            # Get input values from UI
            exchange = self.ui.exchange_var.get()
            asset = self.ui.spot_asset_var.get()
            order_type = self.ui.order_type_var.get()
            
            # Validate quantity input
            try:
                quantity = float(self.ui.quantity_var.get())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError as e:
                self.ui.show_error(f"Invalid quantity: {e}")
                return
            
            # Get other inputs
            fee_tier = self.ui.fee_tier_var.get()
            
            # Validate slippage tolerance input
            try:
                slippage_tolerance = float(self.ui.slippage_tolerance_var.get())
                if slippage_tolerance < 0:
                    raise ValueError("Slippage tolerance cannot be negative")
            except ValueError as e:
                self.ui.show_error(f"Invalid slippage tolerance: {e}")
                return
            
            # Set trade side
            side = self.ui.side_var.get()
            
            # Get additional parameters
            volatility = float(self.ui.volatility_var.get())
            
            # Run the simulation
            results = self.trade_simulator.simulate_trade(
                exchange=exchange,
                asset=asset,
                order_type=order_type,
                quantity=quantity,
                fee_tier=fee_tier,
                slippage_tolerance=slippage_tolerance,
                side=side,
                market_volatility=volatility
            )
            
            # Check if simulation was successful
            if not results["success"]:
                self.ui.show_error(f"Simulation failed: {results.get('error', 'Unknown error')}")
                return
            
            # Update UI with results
            self.ui.update_simulation_results(results)
            
            logger.info(f"Simulation completed with execution price: {results['execution']['price']:.2f}")
            
        except Exception as e:
            logger.error(f"Error during simulation: {e}")
            self.ui.show_error(f"Simulation error: {e}")
    
    def run(self):
        """Run the main application loop."""
        logger.info("Starting application...")
        
        # Start the Tkinter main loop
        self.root.mainloop()
        
        # Cleanup on exit
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources before exiting."""
        logger.info("Cleaning up resources...")
        
        # Cancel periodic task if running
        if self.periodic_task:
            self.root.after_cancel(self.periodic_task)
        
        # Shutdown the simulator
        if self.trade_simulator:
            # Run in a separate thread to avoid blocking
            threading.Thread(
                target=lambda: asyncio.run(self.trade_simulator.shutdown()),
                daemon=True
            ).start()
        
        logger.info("Cleanup complete")


if __name__ == "__main__":
    try:
        app = SimulatorApp()
        app.run()
    except Exception as e:
        logger.critical(f"Application crashed: {e}")
        sys.exit(1)
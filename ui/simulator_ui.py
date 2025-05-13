#!/usr/bin/env python3
"""
Crypto Trading Simulator

A basic UI layout for a crypto trade simulator with two panels:
- Left Panel: Trade configuration inputs
- Right Panel: Trade simulation outputs
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont


class CryptoTradeSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trade Simulator")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # Configure the grid layout
        self.root.grid_columnconfigure(0, weight=3, minsize=300)  # Left panel - 30%
        self.root.grid_columnconfigure(1, weight=7, minsize=500)  # Right panel - 70%
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create and configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 11, 'bold'))
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        self.style.configure('Output.TLabel', background='#ffffff', padding=10)
        self.style.configure('Card.TFrame', background='#ffffff', relief='raised')
        
        # Create form variables
        self.exchange_var = tk.StringVar(value="OKX")
        self.spot_asset_var = tk.StringVar(value="BTC-USDT")
        self.order_type_var = tk.StringVar(value="Market")
        self.quantity_var = tk.StringVar(value="1.0")
        self.fee_tier_var = tk.StringVar(value="Tier 1 (0.1%)")
        self.slippage_tolerance_var = tk.StringVar(value="0.5")
        
        # Create main panels
        self.create_left_panel()
        self.create_right_panel()
    
    def create_left_panel(self):
        """Create the left panel with input controls"""
        left_frame = ttk.Frame(self.root, padding="20 20 20 20", style='TFrame')
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ttk.Label(left_frame, text="Trade Configuration", style='Header.TLabel')
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Exchange dropdown
        ttk.Label(left_frame, text="Exchange:").grid(row=1, column=0, sticky="w", pady=(10, 5))
        exchange_combo = ttk.Combobox(left_frame, textvariable=self.exchange_var, state="readonly")
        exchange_combo['values'] = ('OKX', 'Binance', 'Bybit', 'Kraken', 'Coinbase')
        exchange_combo.grid(row=2, column=0, sticky="ew")
        
        # Spot Asset dropdown
        ttk.Label(left_frame, text="Spot Asset:").grid(row=3, column=0, sticky="w", pady=(10, 5))
        spot_asset_combo = ttk.Combobox(left_frame, textvariable=self.spot_asset_var, state="readonly")
        spot_asset_combo['values'] = ('BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'XRP-USDT', 'ADA-USDT')
        spot_asset_combo.grid(row=4, column=0, sticky="ew")
        
        # Order Type dropdown
        ttk.Label(left_frame, text="Order Type:").grid(row=5, column=0, sticky="w", pady=(10, 5))
        order_type_combo = ttk.Combobox(left_frame, textvariable=self.order_type_var, state="readonly")
        order_type_combo['values'] = ('Market', 'Limit', 'Stop-Limit', 'Take-Profit')
        order_type_combo.grid(row=6, column=0, sticky="ew")
        
        # Quantity input
        ttk.Label(left_frame, text="Quantity:").grid(row=7, column=0, sticky="w", pady=(10, 5))
        quantity_entry = ttk.Entry(left_frame, textvariable=self.quantity_var)
        quantity_entry.grid(row=8, column=0, sticky="ew")
        
        # Fee Tier dropdown
        ttk.Label(left_frame, text="Fee Tier:").grid(row=9, column=0, sticky="w", pady=(10, 5))
        fee_tier_combo = ttk.Combobox(left_frame, textvariable=self.fee_tier_var, state="readonly")
        fee_tier_combo['values'] = ('Tier 1 (0.1%)', 'Tier 2 (0.08%)', 'Tier 3 (0.05%)', 'Custom')
        fee_tier_combo.grid(row=10, column=0, sticky="ew")
        
        # Slippage Tolerance input
        ttk.Label(left_frame, text="Slippage Tolerance (%):").grid(row=11, column=0, sticky="w", pady=(10, 5))
        slippage_entry = ttk.Entry(left_frame, textvariable=self.slippage_tolerance_var)
        slippage_entry.grid(row=12, column=0, sticky="ew")
        
        # Simulate Trade button
        simulate_button = ttk.Button(left_frame, text="Simulate Trade", command=self.simulate_trade)
        simulate_button.grid(row=13, column=0, sticky="ew", pady=(20, 0))
    
    def create_right_panel(self):
        """Create the right panel with output displays"""
        right_frame = ttk.Frame(self.root, padding="20 20 20 20", style='TFrame')
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ttk.Label(right_frame, text="Simulation Results", style='Header.TLabel')
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Results cards container
        results_frame = ttk.Frame(right_frame)
        results_frame.grid(row=1, column=0, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_columnconfigure(1, weight=1)
        
        # Create output cards
        self.create_output_card(results_frame, 0, 0, "Expected Slippage", "Waiting for simulation...")
        self.create_output_card(results_frame, 0, 1, "Estimated Fees", "Waiting for simulation...")
        self.create_output_card(results_frame, 1, 0, "Execution Price", "Waiting for simulation...")
        self.create_output_card(results_frame, 1, 1, "Final Quantity/Cost", "Waiting for simulation...")
        
        # Order Book Snapshot
        order_book_frame = ttk.LabelFrame(right_frame, text="Order Book Snapshot", padding="10 10 10 10")
        order_book_frame.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        order_book_frame.grid_columnconfigure(0, weight=1)
        
        # Order book placeholder content
        order_book_content = tk.Text(order_book_frame, height=10, width=40, wrap=tk.WORD)
        order_book_content.grid(row=0, column=0, sticky="nsew")
        order_book_content.insert(tk.END, "Order book data will appear here after simulation...")
        order_book_content.config(state="disabled")
        
        # Configure right panel to expand properly
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_rowconfigure(2, weight=2)
    
    def create_output_card(self, parent, row, col, title, default_value):
        """Create a card-like frame to display output values"""
        card = ttk.Frame(parent, style='Card.TFrame', padding="15 15 15 15")
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        card.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(card, text=title, font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Value
        value_label = ttk.Label(card, text=default_value, style='Output.TLabel')
        value_label.grid(row=1, column=0, sticky="ew")
        
        return value_label  # Return the label for later updates
    
    def simulate_trade(self):
        """Placeholder for trade simulation logic"""
        # In a real application, this would calculate values based on inputs
        # and update the UI with the results
        print("Simulating trade with the following parameters:")
        print(f"Exchange: {self.exchange_var.get()}")
        print(f"Spot Asset: {self.spot_asset_var.get()}")
        print(f"Order Type: {self.order_type_var.get()}")
        print(f"Quantity: {self.quantity_var.get()}")
        print(f"Fee Tier: {self.fee_tier_var.get()}")
        print(f"Slippage Tolerance: {self.slippage_tolerance_var.get()}%")
        
        # This would update the output displays with calculated values
        # For now, we just show a message in the console
        print("Simulation complete! (This is just a placeholder)")


def main():
    root = tk.Tk()
    app = CryptoTradeSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
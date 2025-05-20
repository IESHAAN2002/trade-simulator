"""
Crypto Trading Simulator

A basic UI layout for a crypto trade simulator with two panels:
- Left Panel: Trade configuration inputs
- Right Panel: Trade simulation outputs
"""
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tkinter import messagebox


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
        self.side_var = tk.StringVar(value="buy")
        self.volatility_var = tk.StringVar(value="0.05")
        
        # Initialize the simulation callback function
        self.simulation_callback = None
        
        # Create output label references
        self.output_labels = {}
        
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
        
        # Add Trade Side (Buy/Sell)
        ttk.Label(left_frame, text="Trade Side:").grid(row=7, column=0, sticky="w", pady=(10, 5))
        side_frame = ttk.Frame(left_frame)
        side_frame.grid(row=8, column=0, sticky="ew")
        
        buy_radio = ttk.Radiobutton(side_frame, text="Buy", variable=self.side_var, value="buy")
        buy_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        sell_radio = ttk.Radiobutton(side_frame, text="Sell", variable=self.side_var, value="sell")
        sell_radio.pack(side=tk.LEFT)
        
        # Quantity input
        ttk.Label(left_frame, text="Quantity:").grid(row=9, column=0, sticky="w", pady=(10, 5))
        quantity_entry = ttk.Entry(left_frame, textvariable=self.quantity_var)
        quantity_entry.grid(row=10, column=0, sticky="ew")
        
        # Fee Tier dropdown
        ttk.Label(left_frame, text="Fee Tier:").grid(row=11, column=0, sticky="w", pady=(10, 5))
        fee_tier_combo = ttk.Combobox(left_frame, textvariable=self.fee_tier_var, state="readonly")
        fee_tier_combo['values'] = ('Tier 1 (0.1%)', 'Tier 2 (0.08%)', 'Tier 3 (0.05%)', 'Custom')
        fee_tier_combo.grid(row=12, column=0, sticky="ew")
        
        # Slippage Tolerance input
        ttk.Label(left_frame, text="Slippage Tolerance (%):").grid(row=13, column=0, sticky="w", pady=(10, 5))
        slippage_entry = ttk.Entry(left_frame, textvariable=self.slippage_tolerance_var)
        slippage_entry.grid(row=14, column=0, sticky="ew")
        
        # Market Volatility input
        ttk.Label(left_frame, text="Market Volatility:").grid(row=15, column=0, sticky="w", pady=(10, 5))
        volatility_entry = ttk.Entry(left_frame, textvariable=self.volatility_var)
        volatility_entry.grid(row=16, column=0, sticky="ew")
        
        # Simulate Trade button
        simulate_button = ttk.Button(left_frame, text="Simulate Trade", command=self.simulate_trade)
        simulate_button.grid(row=17, column=0, sticky="ew", pady=(20, 0))
    
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
        self.output_labels["slippage"] = self.create_output_card(results_frame, 0, 0, "Expected Slippage", "Waiting for simulation...")
        self.output_labels["fees"] = self.create_output_card(results_frame, 0, 1, "Estimated Fees", "Waiting for simulation...")
        self.output_labels["execution_price"] = self.create_output_card(results_frame, 1, 0, "Execution Price", "Waiting for simulation...")
        self.output_labels["final_cost"] = self.create_output_card(results_frame, 1, 1, "Final Quantity/Cost", "Waiting for simulation...")
        
        # Order Book Snapshot
        order_book_frame = ttk.LabelFrame(right_frame, text="Order Book Snapshot", padding="10 10 10 10")
        order_book_frame.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        order_book_frame.grid_columnconfigure(0, weight=1)
        
        # Order book content - use Text widget for more control
        self.order_book_content = tk.Text(order_book_frame, height=10, width=40, wrap=tk.WORD)
        self.order_book_content.grid(row=0, column=0, sticky="nsew")
        self.order_book_content.insert(tk.END, "Order book data will appear here after simulation...")
        
        # Add scrollbar to order book
        scrollbar = ttk.Scrollbar(order_book_frame, orient="vertical", command=self.order_book_content.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.order_book_content.config(yscrollcommand=scrollbar.set)
        
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
    
    def set_simulation_callback(self, callback_function):
        """Set the callback function to run when Simulate Trade button is clicked"""
        self.simulation_callback = callback_function
    
    def simulate_trade(self):
        """Handle simulate trade button click"""
        if self.simulation_callback:
            # Call the registered callback function
            self.simulation_callback()
        else:
            # Fallback behavior if no callback is registered
            self.show_error("Simulation functionality not connected!")
    
    def show_error(self, message):
        """Display an error message"""
        messagebox.showerror("Error", message)
    
    def update_simulation_results(self, results):
        """Update the UI with simulation results"""
        if not results or not isinstance(results, dict):
            return
        
        # Update the output cards with simulation results
        if "slippage" in results:
            self.output_labels["slippage"].config(text=f"{results['slippage']:.4f}%")
        
        if "fees" in results:
            self.output_labels["fees"].config(text=f"${results['fees']:.2f}")
        
        if "execution" in results and "price" in results["execution"]:
            self.output_labels["execution_price"].config(text=f"${results['execution']['price']:.2f}")
        
        if "final_cost" in results:
            self.output_labels["final_cost"].config(text=f"${results['final_cost']:.2f}")
    
    def update_orderbook_display(self, orderbook_text):
        """Update the orderbook display text"""
        if not self.order_book_content:
            return
        
        # Clear current content
        self.order_book_content.config(state=tk.NORMAL)
        self.order_book_content.delete(1.0, tk.END)
        
        # Insert new content
        self.order_book_content.insert(tk.END, orderbook_text)
        self.order_book_content.config(state=tk.DISABLED)


# Standalone testing
def main():
    root = tk.Tk()
    app = CryptoTradeSimulator(root)
    
    # For testing, we can add a simple simulation function
    def test_simulation():
        print("Test simulation running...")
        test_results = {
            "success": True,
            "slippage": 0.12,
            "fees": 1.25,
            "execution": {"price": 29876.50},
            "final_cost": 29912.88
        }
        app.update_simulation_results(test_results)
        
        # Update orderbook for testing
        app.update_orderbook_display(
            "Best Ask: 29880.00\n"
            "Best Bid: 29875.00\n"
            "Spread: 5.00 (0.0167%)\n\n"
            "Ask Depth: $120000.00\n"
            "Bid Depth: $135000.00\n"
            "Book Imbalance: -0.0588\n\n"
            "Last Update: 5.24ms\n\n"
            "--- Top 5 Asks ---\n"
            "$29880.00 | 1.5000\n"
            "$29881.50 | 0.7500\n"
            "$29883.00 | 2.1000\n"
            "$29885.00 | 3.0000\n"
            "$29890.00 | 5.0000\n\n"
            "--- Top 5 Bids ---\n"
            "$29875.00 | 1.2000\n"
            "$29873.50 | 0.8500\n"
            "$29870.00 | 2.5000\n"
            "$29868.00 | 1.7500\n"
            "$29865.00 | 3.5000\n"
        )
    
    # Connect the test simulation
    app.set_simulation_callback(test_simulation)
    
    root.mainloop()


if __name__ == "__main__":
    main()
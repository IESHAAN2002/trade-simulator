"""
OKX L2 Orderbook WebSocket Client

This module connects to OKX's WebSocket API to receive and process real-time
Level 2 orderbook data for BTC-USDT-SWAP.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("okx_ws_client")


class OkxOrderbookClient:
    """Client for processing OKX L2 orderbook data via WebSocket."""
    
    def __init__(
        self, 
        ws_url: str = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP",
        max_retries: int = 5,
        retry_delay: float = 2.0
    ):
        """
        Initialize the OKX WebSocket client.
        
        Args:
            ws_url: WebSocket URL for the OKX orderbook feed
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.ws_url = ws_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.websocket = None
        self.running = False
        
        # Orderbook state
        self.asks_df = pd.DataFrame(columns=['price', 'size'])
        self.bids_df = pd.DataFrame(columns=['price', 'size'])
        
        # Performance metrics
        self.message_count = 0
        self.total_processing_time = 0
        self.last_latency = 0
        
    async def connect(self) -> None:
        """Establish WebSocket connection with retry logic."""
        retries = 0
        
        while retries < self.max_retries:
            try:
                logger.info(f"Connecting to {self.ws_url}")
                self.websocket = await websockets.connect(self.ws_url)
                logger.info("Connection established")
                return
            except WebSocketException as e:
                retries += 1
                logger.error(f"Connection attempt {retries} failed: {e}")
                
                if retries >= self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) reached. Giving up.")
                    raise ConnectionError(f"Failed to connect after {self.max_retries} attempts") from e
                
                await asyncio.sleep(self.retry_delay)
    
    def _process_orderbook_data(
        self, 
        asks: List[List[Union[str, float]]], 
        bids: List[List[Union[str, float]]]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process raw orderbook data into pandas DataFrames.
        
        Args:
            asks: List of [price, size] pairs for ask orders
            bids: List of [price, size] pairs for bid orders
            
        Returns:
            Tuple of (asks_df, bids_df) as pandas DataFrames
        """
        # Convert to DataFrames
        asks_df = pd.DataFrame(asks, columns=['price', 'size'])
        bids_df = pd.DataFrame(bids, columns=['price', 'size'])
        
        # Convert string values to float
        asks_df = asks_df.astype(float)
        bids_df = bids_df.astype(float)
        
        # Sort asks ascending, bids descending by price
        asks_df = asks_df.sort_values('price', ascending=True)
        bids_df = bids_df.sort_values('price', ascending=False)
        
        return asks_df, bids_df
    
    async def _handle_message(self, message: str) -> None:
        """
        Process incoming WebSocket message.
        
        Args:
            message: Raw JSON message string from WebSocket
        """
        start_time = time.time()
        
        try:
            data = json.loads(message)
            
            # Extract orderbook data if available
            if 'asks' in data and 'bids' in data:
                # Process the orderbook data
                self.asks_df, self.bids_df = self._process_orderbook_data(
                    data['asks'], data['bids']
                )
                
                # Update performance metrics
                end_time = time.time()
                processing_time = (end_time - start_time) * 1000  # Convert to ms
                self.last_latency = processing_time
                self.total_processing_time += processing_time
                self.message_count += 1
                
                # Log metrics periodically (every 100 messages)
                if self.message_count % 100 == 0:
                    avg_latency = self.total_processing_time / self.message_count
                    logger.info(f"Processed {self.message_count} messages. "
                               f"Current latency: {self.last_latency:.2f}ms, "
                               f"Average latency: {avg_latency:.2f}ms")
                
                # Log individual message processing 
                logger.debug(f"Processed orderbook update in {processing_time:.2f}ms "
                           f"(Asks: {len(self.asks_df)}, Bids: {len(self.bids_df)})")
            else:
                logger.warning(f"Received message without orderbook data: {message[:100]}...")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON message: {message[:100]}...")
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
    
    async def _receive_messages(self) -> None:
        """Listen for and process incoming WebSocket messages."""
        if not self.websocket:
            raise RuntimeError("WebSocket connection not established")
        
        try:
            while self.running:
                message = await self.websocket.recv()
                await self._handle_message(message)
        except ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            if self.running:
                # Try to reconnect if we're still supposed to be running
                await self.connect()
                # Restart the message receive loop
                await self._receive_messages()
        except Exception as e:
            logger.exception(f"Error in message processing loop: {e}")
            
    def get_orderbook_snapshot(self) -> Dict[str, pd.DataFrame]:
        """
        Get the current orderbook snapshot.
        
        Returns:
            Dictionary with 'asks' and 'bids' DataFrames
        """
        return {
            'asks': self.asks_df.copy(),
            'bids': self.bids_df.copy(),
            'last_latency_ms': self.last_latency
        }
    
    async def start(self) -> None:
        """Start the WebSocket client."""
        if self.running:
            logger.warning("Client is already running")
            return
        
        self.running = True
        await self.connect()
        await self._receive_messages()
    
    async def stop(self) -> None:
        """Stop the WebSocket client."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")


async def main():
    """Main entry point for running the client."""
    client = OkxOrderbookClient()
    
    try:
        # Run the client for some time
        client_task = asyncio.create_task(client.start())
        
        # Main application loop
        for _ in range(10):
            await asyncio.sleep(1)
            snapshot = client.get_orderbook_snapshot()
            
            # Print some orderbook stats
            if not snapshot['asks'].empty and not snapshot['bids'].empty:
                best_ask = snapshot['asks'].iloc[0]['price']
                best_bid = snapshot['bids'].iloc[0]['price']
                spread = best_ask - best_bid
                logger.info(f"Best ask: {best_ask:.2f}, Best bid: {best_bid:.2f}, "
                           f"Spread: {spread:.2f}, Latency: {snapshot['last_latency_ms']:.2f}ms")
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.exception(f"Error in main loop: {e}")
    finally:
        # Ensure proper shutdown
        await client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
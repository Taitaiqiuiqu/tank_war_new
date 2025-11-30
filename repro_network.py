import sys
import os
import time
import threading

# Add src to path
sys.path.append(os.getcwd())

from src.network.network_manager import NetworkManager

def test_discovery():
    print("Starting Host...")
    host = NetworkManager()
    host.start_host()
    
    print("Starting Client...")
    client = NetworkManager()
    client.start_client()
    
    print("Client broadcasting discovery...")
    client.broadcast_discovery()
    
    # Wait for response
    time.sleep(2)
    
    print(f"Client found servers: {client.found_servers}")
    
    if len(client.found_servers) > 0:
        print("SUCCESS: Server found!")
    else:
        print("FAILURE: No servers found.")
        
    host.stop()
    client.stop()

if __name__ == "__main__":
    test_discovery()

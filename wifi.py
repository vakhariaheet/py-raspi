#!/usr/bin/env python3

import subprocess
import os
import sys
import time
from getpass import getpass

class WiFiManager:
    def __init__(self):
        self.wpa_supplicant_file = "/etc/wpa_supplicant/wpa_supplicant.conf"
        self.known_networks_file = os.path.expanduser("~/.known_networks")
        
    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            # Get the wireless interface name (usually wlan0)
            result = subprocess.run(['iwconfig'], capture_output=True, text=True)
            interface = None
            for line in result.stdout.split('\n'):
                if 'IEEE 802.11' in line:
                    interface = line.split()[0]
                    break
            
            if not interface:
                print("No wireless interface found!")
                return []
            
            # Scan for networks
            subprocess.run(['sudo', 'iwlist', interface, 'scan'])
            result = subprocess.run(['sudo', 'iwlist', interface, 'scan'], 
                                 capture_output=True, text=True)
            
            networks = []
            current_ssid = None
            current_signal = None
            
            for line in result.stdout.split('\n'):
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:"')[1].split('"')[0]
                    if ssid:  # Only add non-empty SSIDs
                        networks.append({
                            'ssid': ssid,
                            'signal': current_signal if current_signal else 'N/A'
                        })
                elif 'Quality=' in line:
                    # Extract signal strength
                    signal_part = line.split('Quality=')[1].split()[0]
                    current_signal = signal_part
            
            return networks
            
        except Exception as e:
            print(f"Error scanning networks: {str(e)}")
            return []

    def load_known_networks(self):
        """Load previously connected networks"""
        known_networks = set()
        try:
            if os.path.exists(self.known_networks_file):
                with open(self.known_networks_file, 'r') as f:
                    known_networks = set(line.strip() for line in f)
        except Exception as e:
            print(f"Error loading known networks: {str(e)}")
        return known_networks

    def save_known_network(self, ssid):
        """Save network to known networks file"""
        try:
            with open(self.known_networks_file, 'a') as f:
                f.write(f"{ssid}\n")
        except Exception as e:
            print(f"Error saving known network: {str(e)}")

    def connect_to_network(self, ssid, password=None):
        """Connect to a WiFi network"""
        try:
            # Create WPA supplicant configuration
            network_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
            # Backup existing configuration
            subprocess.run(['sudo', 'cp', self.wpa_supplicant_file, 
                          f"{self.wpa_supplicant_file}.backup"])
            
            # Append new network configuration
            with open('/tmp/wpa_supplicant_update', 'w') as f:
                f.write(network_config)
            
            subprocess.run(['sudo', 'bash', '-c', 
                          f'cat /tmp/wpa_supplicant_update >> {self.wpa_supplicant_file}'])
            
            # Reconfigure wireless interface
            subprocess.run(['sudo', 'wpa_cli', 'reconfigure'])
            
            print(f"Attempting to connect to {ssid}...")
            time.sleep(5)  # Give some time for the connection to establish
            
            # Check if connection was successful
            result = subprocess.run(['iwconfig'], capture_output=True, text=True)
            if ssid in result.stdout:
                print(f"Successfully connected to {ssid}")
                self.save_known_network(ssid)
                return True
            else:
                print(f"Failed to connect to {ssid}")
                return False
                
        except Exception as e:
            print(f"Error connecting to network: {str(e)}")
            return False

def main():
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges.")
        sys.exit(1)

    wifi_manager = WiFiManager()
    known_networks = wifi_manager.load_known_networks()
    
    while True:
        print("\nWiFi Network Manager")
        print("1. Scan and connect to networks")
        print("2. View known networks")
        print("3. Exit")
        
        choice = input("Select an option (1-3): ")
        
        if choice == '1':
            print("\nScanning for networks...")
            networks = wifi_manager.scan_networks()
            
            if not networks:
                print("No networks found!")
                continue
                
            print("\nAvailable networks:")
            for i, network in enumerate(networks, 1):
                known = "*" if network['ssid'] in known_networks else " "
                print(f"{i}. {network['ssid']} {known}")
                print(f"   Signal: {network['signal']}")
            print("\n* = Previously connected network")
            
            try:
                network_choice = int(input("\nSelect network number to connect (0 to cancel): "))
                if network_choice == 0:
                    continue
                    
                selected_network = networks[network_choice - 1]['ssid']
                if selected_network in known_networks:
                    print(f"Connecting to known network {selected_network}...")
                    wifi_manager.connect_to_network(selected_network)
                else:
                    password = getpass(f"Enter password for {selected_network}: ")
                    wifi_manager.connect_to_network(selected_network, password)
                    
            except (ValueError, IndexError):
                print("Invalid selection!")
                
        elif choice == '2':
            print("\nKnown networks:")
            for network in known_networks:
                print(f"- {network}")
                
        elif choice == '3':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
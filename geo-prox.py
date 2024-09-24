import json
import random
import os
import shutil
import subprocess
import requests
import time
import argparse

# Paths
PROXYCHAINS_CONF_PATH = "/etc/proxychains.conf"
BACKUP_CONF_PATH = "/etc/proxychains_backup.conf"
PROXY_LIST_PATH = "proxy-list/proxies.json"  # Update path to point to proxies.json in the root directory
TIMEOUT_THRESHOLD = 1.0  # Threshold for filtering based on proxy timeout (in seconds)
REQUEST_TIMEOUT = 5  # Timeout for testing each proxy in seconds

def update_proxy_list_repo():
    """Pull the latest proxy list from GitHub, or clone it if it doesn't exist."""
    if os.path.exists("proxy-list"):
        print("Updating proxy-list repository...")
        try:
            subprocess.run(["git", "-C", "proxy-list", "pull"], check=True)
            print("Proxy-list repository updated.")
        except subprocess.CalledProcessError as e:
            print(f"Error pulling proxy-list repo: {e}")
    else:
        print("Cloning proxy-list repository...")
        try:
            subprocess.run(["git", "clone", "https://github.com/monosans/proxy-list.git"], check=True)
            print("Proxy-list repository cloned.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning proxy-list repo: {e}")

def load_proxies():
    """Load proxies from the proxy list JSON file."""
    if not os.path.exists(PROXY_LIST_PATH):
        print(f"Proxy list not found at {PROXY_LIST_PATH}")
        return []

    with open(PROXY_LIST_PATH, 'r') as f:
        proxies = json.load(f)
    
    return proxies

def ask_for_location(proxies):
    """Ask user for the geo-location and filter proxies by that location."""
    available_countries = sorted(set(
        proxy['geolocation'].get('country', {}).get('names', {}).get('en', 'Unknown') 
        for proxy in proxies
    ))
    
    print("Available Countries:")
    for i, country in enumerate(available_countries, 1):
        print(f"{i}. {country}")
    
    try:
        choice = int(input("Select a country by number (or type '0' for any location): "))
        if choice == 0:
            return None  # User wants any location
        if 1 <= choice <= len(available_countries):
            return available_countries[choice - 1]
        else:
            print("Invalid selection. Please choose a valid number.")
            return ask_for_location(proxies)
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return ask_for_location(proxies)

def filter_proxies_by_country(proxies, selected_country):
    """Filter proxies by the selected country."""
    if selected_country:
        return [
            proxy for proxy in proxies
            if proxy['geolocation'].get('country', {}).get('names', {}).get('en', 'Unknown').lower() == selected_country.lower()
        ]
    return proxies

def test_proxy(proxy):
    """Tests if a proxy is working by sending an HTTP request and checking its response time."""
    try:
        proxy_type = proxy.get('protocol', 'http')
        proxy_url = f"{proxy_type}://{proxy.get('host')}:{proxy.get('port')}"
        proxies = {proxy_type: proxy_url}
        
        # Record response time
        start_time = time.time()
        response = requests.get('http://www.google.com', proxies=proxies, timeout=REQUEST_TIMEOUT)
        elapsed_time = time.time() - start_time

        # If response is successful and fast enough, consider the proxy valid
        if response.status_code == 200 and elapsed_time <= TIMEOUT_THRESHOLD:
            print(f"Proxy passed with response time: {elapsed_time:.2f}s")
            return True
    except requests.RequestException:
        return False
    return False

def filter_working_proxies(proxies, retries=3):
    """Filters out proxies that do not work or are too slow, retrying until enough proxies are found."""
    working_proxies = []
    attempts = 0

    while len(working_proxies) < 5 and attempts < retries:
        for proxy in proxies:
            if len(working_proxies) >= 10:
                break  # Stop when we have enough proxies

            # Filter by the JSON timeout field first
            proxy_timeout = proxy.get('timeout', float('inf'))  # Use infinity if timeout is not defined
            if proxy_timeout > TIMEOUT_THRESHOLD:
                print(f"Skipping slow proxy with timeout: {proxy_timeout:.2f}s ({proxy['host']}:{proxy['port']})")
                continue  # Skip proxies with timeout greater than the threshold

            # Test proxy response time in real-world conditions
            if test_proxy(proxy):
                working_proxies.append(proxy)
            else:
                print(f"Proxy failed: {proxy['host']}:{proxy['port']}")
        attempts += 1
        if len(working_proxies) < 5:
            print(f"Retrying... ({attempts}/{retries})")
            time.sleep(1)  # Small pause before retrying

    return working_proxies

def backup_proxychains_conf():
    """Backs up the current proxychains configuration file."""
    shutil.copy(PROXYCHAINS_CONF_PATH, BACKUP_CONF_PATH)
    print("Backup of proxychains.conf created.")

def restore_proxychains_conf():
    """Restores the proxychains configuration file to its original state."""
    if os.path.exists(BACKUP_CONF_PATH):
        shutil.copy(BACKUP_CONF_PATH, PROXYCHAINS_CONF_PATH)
        print("Proxychains.conf restored to its original state.")
    else:
        print("No backup found to restore.")

def update_proxychains_conf(proxies):
    """Updates the proxychains configuration file with multiple selected proxies and removes Tor default."""
    with open(PROXYCHAINS_CONF_PATH, "r") as file:
        lines = file.readlines()

    # Remove the default Tor entry if it exists (socks4 127.0.0.1 9050)
    lines = [line for line in lines if "127.0.0.1 9050" not in line]

    # Set chain type to random_chain, disable DNS proxying, and set chain length to 1
    for i, line in enumerate(lines):
        if "strict_chain" in line:
            lines[i] = "# strict_chain\n"
        if "dynamic_chain" in line:
            lines[i] = "# dynamic_chain\n"
        if "random_chain" not in line:
            lines[i] = "random_chain\n"  # Ensure random_chain is enabled
        if "proxy_dns" in line:
            lines[i] = "# proxy_dns\n"  # Disable DNS proxying
        if "chain_len" in line:
            lines[i] = "chain_len = 1\n"  # Set chain length to 1

    # Add multiple proxies in the correct format
    for proxy in proxies:
        protocol = proxy.get('protocol', 'http')  # Ensure we use the protocol from the JSON data
        host = proxy.get('host')
        port = proxy.get('port')
        username = proxy.get('username')
        password = proxy.get('password')

        # Building proxychains config line following the correct format: type host port [user pass]
        if username and password:
            proxy_line = f"{protocol} {host} {port} {username} {password}\n"
        else:
            proxy_line = f"{protocol} {host} {port}\n"

        # Add the proxy to the proxychains.conf file
        lines.append(proxy_line)

    with open(PROXYCHAINS_CONF_PATH, "w") as file:
        file.writelines(lines)

    print(f"Added {len(proxies)} proxies to proxychains.conf")

def launch_application(app_name):
    """Launches the specified application through proxychains."""
    try:
        subprocess.run(["proxychains", app_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching {app_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Configure and launch an application with proxychains.')
    parser.add_argument('--num-proxies', type=int, default=10, help='Specify the number of proxies to use (default 10)')
    parser.add_argument('--app', type=str, default='firefox', help='Specify the application to run (default Firefox)')
    args = parser.parse_args()

    # Pull or update the proxy list from the GitHub repository
    update_proxy_list_repo()
    
    # Load proxies from the proxy-list repo
    proxies = load_proxies()
    
    if not proxies:
        print("No proxies available.")
        return
    
    # Ask for a country
    selected_country = ask_for_location(proxies)
    
    # Filter proxies by the selected country
    filtered_proxies = filter_proxies_by_country(proxies, selected_country)

    # Test and filter working proxies based on response time and JSON timeout
    working_proxies = filter_working_proxies(filtered_proxies)

    # Check if we have less than 5 working proxies and ask user if they want to continue
    if len(working_proxies) < 5:
        proceed = input(f"Only {len(working_proxies)} working proxies found. Do you want to continue? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting due to insufficient proxies.")
            return

    # Randomly select proxies (up to the user-specified number or less if fewer available)
    num_proxies_to_add = min(args.num_proxies, len(working_proxies))
    selected_proxies = random.sample(working_proxies, num_proxies_to_add)

    for proxy in selected_proxies:
        print(f"Selected Proxy: {proxy['host']}:{proxy['port']} ({proxy['geolocation'].get('country', {}).get('names', {}).get('en', 'Unknown')})")
    
    # Backup the original proxychains.conf
    backup_proxychains_conf()
    
    # Update proxychains configuration with the selected proxies and remove Tor defaults
    update_proxychains_conf(selected_proxies)
    
    # Launch the specified application using proxychains
    try:
        launch_application(args.app)
    finally:
        # Restore proxychains configuration after the application closes
        restore_proxychains_conf()

if __name__ == "__main__":
    main()

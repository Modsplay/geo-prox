# Geo-prox ProxyChains Automation Script

This script automates configuring **proxychains** to work with a fresh list of proxies. It pulls proxies from an online source ([monosans/proxy-list](https://github.com/monosans/proxy-list)) and sets up **proxychains** to use these proxies for routing traffic through an application of your choice.

## Features

- **Automatic Proxy List Fetching**: Automatically pulls a fresh proxy list from the [monosans/proxy-list GitHub repo](https://github.com/monosans/proxy-list).
- **Proxy Selection by Country**: Choose proxies from specific countries, or select proxies from any country.
- **Working Proxy Validation**: The script tests proxies and only uses the ones that pass a connection test.
- **Customizable Number of Proxies**: You can specify how many proxies you want to add to the proxychains config.
- **Customizable Application**: Specify the application to run through `proxychains` (e.g., `firefox`, `curl`, `chrome`).
- **Random Proxy Selection**: Uses `random_chain` to randomly select a proxy from the list.
- **Proxychains Configuration**:
  - `random_chain` enabled (randomly selects a proxy).
  - `proxy_dns` disabled (DNS queries are resolved locally).
  - `chain_len` set to 1 (only one proxy is used at a time).

## Requirements

Make sure you have the following installed:
- Python 3
- `proxychains`
- Python `requests` module:
  ```bash
  pip install requests
  ```

## Usage

### Basic Usage

Run the script with the default configuration:
- Uses **10 proxies**.
- Launches **Firefox** with proxychains.

```bash
python3 sel-prox.py
```

### Specify Number of Proxies

You can customize the number of proxies used with the `--num-proxies` flag. For example, to use 15 proxies:

```bash
python3 sel-prox.py --num-proxies 15
```

### Specify an Application to Run

Use the `--app` flag to specify a different application to run through `proxychains`. For example, to run `curl` with 10 proxies:

```bash
python3 sel-prox.py --app curl
```

Or to run `chrome` with 20 proxies:

```bash
python3 sel-prox.py --num-proxies 20 --app chrome
```

### Combine Flags

You can combine the `--num-proxies` and `--app` flags to customize both the proxy count and the application. For example:

```bash
python3 sel-prox.py --num-proxies 25 --app curl
```

This will use 25 proxies and run `curl` through proxychains.

### Select Proxies by Country

After starting the script, you’ll be asked to choose proxies from a specific country. The script will display a numbered list of available countries. You can enter the number corresponding to the country you want to select proxies from. To select proxies from any country, type `0`.

Example:
```bash
Available Countries:
1. United States
2. Russia
3. Germany
4. Canada
...
Select a country by number (or type '0' for any location): 1
```

In this example, typing `1` will select proxies from the United States.

### Handling Less Than 5 Working Proxies

If the script finds fewer than 5 working proxies, it will ask whether you want to proceed with fewer proxies. You can choose `y` (yes) to continue, or `n` (no) to exit the script.

Example:
```bash
Only 3 working proxies found. Do you want to continue? (y/n): y
```

Choosing `y` will proceed with the 3 available proxies.

## Example Commands

1. Run **Firefox** with the default 10 proxies:
   ```bash
   python3 sel-prox.py
   ```

2. Run **curl** with **20 proxies**:
   ```bash
   python3 sel-prox.py --num-proxies 20 --app curl
   ```

3. Run **Chrome** with **15 proxies**:
   ```bash
   python3 sel-prox.py --num-proxies 15 --app chrome
   ```

4. Run **wget** with **5 proxies**:
   ```bash
   python3 sel-prox.py --num-proxies 5 --app wget
   ```

## Proxychains Configuration

The script automatically modifies the `proxychains.conf` file to:
- **Enable random chain** selection.
- **Disable DNS proxying** (proxy DNS resolution is disabled).
- **Set chain length to 1**, meaning only one proxy is used per request.

After the script finishes, the `proxychains.conf` file is restored to its original state.

### Troubleshooting

- **Not Enough Working Proxies**: If you encounter the "need more proxies" message, you can lower the number of proxies using `--num-proxies` to proceed with fewer proxies.
  
  Example: 
  ```bash
  python3 sel-prox.py --num-proxies 5 --app firefox
  ```

- **DNS Issues**: The script disables DNS proxying by default, which resolves DNS queries locally. If you want to proxy DNS as well, you can manually edit the `proxychains.conf` file and re-enable `proxy_dns`.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests on GitHub.


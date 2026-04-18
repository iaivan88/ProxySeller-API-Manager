# ProxySeller API Manager

Command-line Python tool for managing ProxySeller residential proxy lists.  
It supports listing, downloading, creating, renaming, and deleting lists through the ProxySeller API.

## What This Tool Does

- View existing proxy lists
- Download proxies from one or multiple lists
- Create one or multiple lists with geo filters and presets
- Rename an existing list
- Delete multiple lists at once
- Export downloaded proxies as TXT, CSV, or JSON
- Save generated and downloaded files into `Results/`

## Requirements

- Python 3.8+
- A valid ProxySeller API key

## Installation

1. Clone this repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Current dependencies:
- `requests`
- `python-dotenv`
- `rich`

## Quick Start

Run:

```bash
python main.py
```

On first launch, the app asks for your ProxySeller API key and securely stores it in a `.env` file (`PROXY_SELLER_API_KEY`). It also supports reading from an existing `api_key.txt` for backwards compatibility.

The CLI interface has been upgraded with the `rich` library to support colored output, interactive menus, and progress bars.

## Menu Actions

When started, the CLI menu provides:

1. Get existing IP lists
2. Download proxies from existing list(s)
3. Create a new list (or multiple lists)
4. Rename a list
5. Delete list(s)
0. Exit

## Download Options

### List Selection

You can select lists by:
- comma-separated numbers (`1,3,5`)
- range syntax (`[10, 20]`)

### Proxy Output Format

- `login:password@host:port` (default)
- `login:password:host:port`
- `host:port:login:password`
- `host:port@login:password`

### Export Format

- `txt` (default)
- `csv`
- `json`

### Merge Mode

During download, you can merge proxies from selected lists into one file or save each list into separate files.

## Create List Options

When creating a list, the tool supports:

- List title
- Number of lists to create (batch creation)
- Country preset or manual country codes
- Optional region, city, and ISP filters
- Ports per list (up to 1000)
- Optional whitelist IPs
- Proxy format selection for generated output

## Country Presets

Built-in presets:
- Worldwide
- Europe
- Asia
- South America
- North America
- Africa

You can also enter country codes manually (comma-separated).

## Files and Storage

- `.env`: securely stores the `PROXY_SELLER_API_KEY`
- `api_key.txt`: fallback/legacy storage for the API key
- `app.log`: log file for runtime information and errors
- `Results/`: downloaded/generated proxy files

File names are generated from list titles and selected countries where possible.

## Notes

- The tool uses ProxySeller API endpoints under `resident`.
- API and network errors are handled and printed in CLI output.
- This project is an independent tool and is not affiliated with ProxySeller.
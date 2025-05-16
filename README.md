# 🌍  GWC Data Library (```gwc_datalib```)
A Python library developed for the Global Wetland Center (GWC) to facilitate seamless access to wetland-related datasets stored in cloud storage. It provides functions for reading and retrieving data while managing authentication via Auth0. The library is designed for use by researchers and developers, ensuring efficient and secure data access.


## Features

- Auth0 authentication to the metadata API
- Search and filter datasets by name or tag
- List datasets uploaded by the current user
- Load datasets from storage backends (currently only Azure supported)
- Auto-handle format-specific reading (e.g. CSV, GeoTIFF)

## Installation

```bash
pip install git+https://github.com/DHI/gwc-datalib.git
```

> ⚠️ You will also need a `.env` file or environment variables to configure Auth0 and API access. See [Configuration](#configuration).

## ⚙️ Configuration

Create a `.env` file in your project directory with the following values:

```env
API_USER=your@email.com
API_PASSWORD=your_password
```

## Usage
See [notebooks/example_exploring_datasets.ipynb](notebooks/example_exploring_datasets.ipynb) for examples

### 1. Initialize the client

```python
from gwc_datalib.client import GWSDataClient

client = GWSDataClient()
```

### 2. Search for datasets

```python
client.list_datasets(
    tag=<some tag to search by>, # Optional
    name=<some dataset name to search by>, # Optional
)
```

### 3. List your uploaded datasets

```python
client.list_user_datasets()
```

### 4. Load a dataset

```python
dataset = client.load_dataset("soil_norway_2024")

# If it's CSV-based:
df = dataset.to_pandas()

# If it's a raster or multidimensional data:
xr_data = dataset.to_xarray()
```

## Project Structure 

```
gwc_datalib/
├── client.py                # Main client interface
├── adapters/                # Per-repository adapters (Azure, Dataverse, ERDA)
│   ├── azure_blob.py
│   └── ...
├── dataset.py               # Unified Dataset wrapper
├── utils/
│   └── authentication.py
├── config.py                # Reads API endpoints and env vars
```


## Development

To run and test locally:

```bash
git clone https://github.com/DHI/gwc-datalib.git
cd gwc-datalib
pip install -e .
```
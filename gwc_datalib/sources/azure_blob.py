from azure.storage.blob import BlobServiceClient
from rasterio.io import MemoryFile
import rioxarray
import xarray as xr
from pathlib import Path
import pandas as pd
from io import BytesIO
import requests
from gwc_datalib.sources.base import BaseDataAdapter
from gwc_datalib import config


class AzureBlobAdapter(BaseDataAdapter):
    def __init__(self, metadata, auth_token):
        """
        Adapter for accessing datasets stored in Azure Blob Storage.

        Parameters:
            metadata (dict): Dataset metadata returned from the metadata API.
            auth_token (str): Auth0 bearer token for authorization with the backend API.
        """
        super().__init__(metadata)
        self.auth_token = auth_token
        self.dataset_name = metadata["dataset_name"]
        self.api_endpoint = config.API_ENDPOINT
        self.files = self._list_files()["files"]
        self.storage_format = metadata.get("storage_format", {})
        self._sas_info = {}  # cache SAS tokens per file

    def _list_files(self):
        """
        List all files that are part of this Azure Blob dataset.

        Returns:
            list of str: Filenames available in the dataset.
        """
        url = f"{self.api_endpoint}/azure-blob/list-files"
        params = {"dataset_name": self.dataset_name}

        response = requests.get(
            url, params=params, headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        response.raise_for_status()
        return response.json()

    def _get_sas_token(self, file_name):
        if file_name in self._sas_info:
            return self._sas_info[file_name]

        url = f"{config.API_ENDPOINT}/azure-blob/generate-blob-sas-token"
        response = requests.get(
            url,
            params={"dataset_name": self.dataset_name, "file_name": file_name},
            headers={"Authorization": f"Bearer {self.auth_token}"},
        )
        sas_info = response.json()
        self._sas_info[file_name] = sas_info
        return sas_info

    def _download_file(self, file_name):
        info = self._get_sas_token(file_name)
        client = BlobServiceClient(
            account_url=info["account_url"], credential=info["sas_token"]
        )
        blob_client = client.get_blob_client(
            container=info["container_name"], blob=info["blob_name"]
        )
        return blob_client.download_blob().readall()

    def get_download_links(self, file_name=None):
        """
        Generates direct download links (with time-limited SAS tokens) for each file in the dataset.

        Returns:
            list of dict: Each dictionary contains 'file' (filename) and 'url' (direct link).

        Example:
            >>> for link in dataset.get_download_links():
            >>>     print(f"{link['file']}: {link['url']}")
        """
        links = []
        if file_name:
            files = [f for f in self.files if f == file_name]
        else:
            files = self.files
        for f in files:
            info = self._get_sas_token(f)
            url = f"{info['account_url']}/{info['container_name']}/{info['blob_name']}?{info['sas_token']}"
            links.append({"file": f, "url": url})
        return links

    def to_pandas(self, file_name=None):
        """
        Reads one or more CSV files from Azure Blob Storage into a Pandas DataFrame.

        Returns:
            pandas.DataFrame: The concatenated DataFrame if multiple CSVs, or a single DataFrame.

        Raises:
            ValueError: If no CSV files are listed in the dataset metadata.

        Example:
            >>> df = dataset.to_pandas()
            >>> print(df.head())
        """
        if file_name:
            csv_files = [f for f in self.files if f == file_name]
        else:
            csv_files = [f for f in self.files if Path(f).suffix == ".csv"]
        if not csv_files:
            raise ValueError("No CSV files found for this dataset.")

        dfs = []
        for f in csv_files:
            stream = self._download_file(f["name"])
            dfs.append(pd.read_csv(BytesIO(stream)))

        return pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]

    def to_xarray(self, file_name=None):
        """
        Reads one or more GeoTIFF files from Azure Blob Storage into xarray DataArray(s).

        Returns:
            xarray.Dataset or list[xarray.Dataset]: A single dataset if one .tif file,
            or a list of datasets if multiple.

        Raises:
            ValueError: If no GeoTIFF (.tif) files are listed in the dataset metadata.

        Example:
            >>> raster = dataset.to_xarray()
            >>> raster.plot()
        """
        if file_name:
            tif_files = [f for f in self.files if f == file_name]
        else:
            tif_files = [f for f in self.files if Path(f).suffix == ".tif"]

        if not tif_files:
            raise ValueError("No TIF files found for this dataset.")

        arrays = []
        for f in tif_files:
            stream = self._download_file(f)
            with MemoryFile(stream) as memfile:
                with memfile.open() as dataset:
                    arrays.append(xr.open_dataset(dataset, engine="rasterio"))

        return arrays if len(arrays) > 1 else arrays[0]

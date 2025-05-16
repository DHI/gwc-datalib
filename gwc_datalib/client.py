from gwc_datalib.sources.azure_blob import AzureBlobAdapter
from gwc_datalib.sources.dataverse import DataverseAdapter
import requests
from gwc_datalib import config
from gwc_datalib.auth.auth0_manager import get_auth0_token


class GWSDataClient:
    def __init__(self):
        """
        Initializes the GWSDataClient for interacting with the metadata API
        and loading datasets from supported storage backends (e.g., Azure, Dataverse, ERDA).

        Handles authentication via Auth0.
        """
        self.auth_token = get_auth0_token()

    # ---------- METADATA API INTERFACE ----------

    def list_datasets(self, name=None, tag=None):
        """
        Searches available datasets in the catalog using optional filters.

        Parameters:
            name (str, optional): Substring to search in dataset names.
            tag (str, optional): A tag to filter datasets by.

        Returns:
            list of dict: Matching datasets from the catalog.

        Example:
            >>> client.list_datasets(name="soil")
            >>> client.list_datasets(tag="norway")
        """
        url = f"{config.API_ENDPOINT}/dataset/search"
        params = {}
        if name:
            params["dataset_name"] = name
        if tag:
            params["tag"] = tag

        response = requests.get(url, headers=self._auth(), params=params)
        response.raise_for_status()
        return response.json()

    def list_user_datasets(self):
        """
        Lists all datasets owned or uploaded by the authenticated user.

        Returns:
            list of dict: Datasets owned by the current user.

        Example:
            >>> client.list_user_datasets()
        """
        url = f"{config.API_ENDPOINT}/dataset/user-datasets"
        response = requests.get(url, headers=self._auth())
        response.raise_for_status()
        return response.json()

    def get_dataset_metadata(self, dataset_name):
        """
        Retrieves full metadata for a specific dataset.

        Parameters:
            dataset_name (str): Unique name of the dataset.

        Returns:
            dict: Metadata for the given dataset.

        Example:
            >>> meta = client.get_dataset_metadata("soil_data_2024")
            >>> print(meta["title"])
        """
        url = f"{config.API_ENDPOINT}/dataset"
        params = {"dataset_name": dataset_name}
        response = requests.get(url, headers=self._auth(), params=params)
        return response.json()

    def add_dataset(self, metadata_dict):
        """
        Adds a new dataset entry to the metadata API.

        Parameters:
            metadata_dict (dict): Full metadata schema describing the dataset,
                                  including repository info, files, and structure.

        Returns:
            dict: The newly created dataset metadata.

        Raises:
            HTTPError: If the request to the API fails.

        Example:
            >>> client.add_dataset({
            >>>     "id": "sensor_abc",
            >>>     "title": "ABC Sensor data",
            >>>     "repository": {
            >>>         "type": "azure",
            >>>         "files": [{"name": "abc.csv", "type": "csv"}]
            >>>     },
            >>>     "structure": {"representation": "tabular"}
            >>> })
        """
        url = f"{config.API_ENDPOINT}/dataset"
        response = requests.post(url, json=metadata_dict, headers=self._auth())
        response.raise_for_status()
        return response.json()

    # ---------- DATA LOADING ----------

    def load_dataset(self, dataset_name):
        """
        Loads a dataset by ID and returns an adapter for interacting with its contents.

        Parameters:
            dataset_name (str): Unique name of the dataset.

        Returns:
            BaseDataAdapter: A dataset adapter instance that supports methods like `.to_pandas()`,
                             `.to_xarray()`, and `.get_download_links()` depending on type.

        Raises:
            ValueError: If the repository type is unsupported.

        Example:
            >>> dataset = client.load_dataset("soil_data_2024")
            >>> df = dataset.to_pandas()
        """
        metadata = self.get_dataset_metadata(dataset_name)
        source_type = metadata["storage_service"]

        if source_type == "AzureBlob":
            return AzureBlobAdapter(metadata, self.auth_token)
        elif source_type == "Dataverse":
            return DataverseAdapter(metadata)
        else:
            raise ValueError(f"Unsupported repository type: {source_type}")

    def _auth(self):
        """Returns an authorization header with the current token."""
        return {"Authorization": f"Bearer {self.auth_token}"}

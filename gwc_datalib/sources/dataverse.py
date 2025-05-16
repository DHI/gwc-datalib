from gwc_datalib.sources.base import BaseDataAdapter


class DataverseAdapter(BaseDataAdapter):
    def to_pandas(self):
        # TODO: Use Dataverse API to download file by DOI
        raise NotImplementedError

    def to_xarray(self):
        # Optional: handle netCDF or GeoTIFF if needed
        raise NotImplementedError

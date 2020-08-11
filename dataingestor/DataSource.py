"""
Author: Mark McDonald
Abstract class that is extended to add new data sources
"""
from abc import ABC, abstractmethod


class DataSource(ABC):
    """
    Abstract class for a datasource.
    This class is extended for every data source of the application
    required methods:
    >
    """
    def __init__(self, name: str, description: str = None):
        self._name = name
        self._description = description
        # self._token = None

    def __str__(self):
        return "DataSource: {} // {}".format(self._name, self._description)

    @property
    def NAME(self):
        return self._name

    @property
    def DESCRIPTION(self):
        return self._description

    # @property
    # def TOKEN(self):
    #     if not self._token:
    #         self.set_token()
    #     return self._token

    # @abstractmethod
    # def set_token(self) -> str:
    #     """
    #     Retrieve a token for the service.  Set variable _token to the retrieved token value.
    #     """
    #     ...

    @abstractmethod
    def load_data(self, **kwargs) -> str:
        """
        Run process to retrieve and load data from datasource.
        This method should accept keyword arguments that are used
        to determine which data to retrieve and are specific to the source.
        These kwargs are usually used in the URL to retrieve data.
        :param kwargs:
        :return: string of confirmation message
        """
        ...

    @abstractmethod
    def load_dummy_data(self):
        ...

    # @abstractmethod
    # def get_data(self, **kwargs):
    #     """
    #     Retrieve data from the local database.
    #     Kwargs represent the field names and values for which to filter data.
    #     :param kwargs: <data source dependent.  Should be values in the data model.>
    #     :return:
    #     """
    #     ...
    #

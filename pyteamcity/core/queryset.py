import itertools
import requests

from .. import exceptions
from .locator import Locator


class QuerySet(object):
    """Base class for constructing an http query.

    Attributes:
        base_url (str): URL for the access point.

    Raises:
        exception_class: [description]
        exceptions.MultipleObjectsReturned: [description]
    """

    base_url = None
    # Factory to construct object from fetched data, needs from_dict function
    _entity_factory = None

    def __init__(self, teamcity):
        """Construct a query for a given Teamcity instance.

        Arguments:
            teamcity {Teamcity} -- Teamcity instance to create query for.
        """
        self.teamcity = teamcity
        self.base_url = self.teamcity.base_url + self.__class__.uri
        self._locator = Locator()
        self._data_dict = {}

    def _add_pred(self, name, value):
        return self._locator.add_pred(name, value)

    def _get_url(self, details=False, href=None):
        """Return the URL to use for making a query.

        Keyword Arguments:
            details {bool} -- [description] (default: False)
            href {str} -- Hyperlink reference to use instead of base_url. (default: None)

        Returns:
            str -- Constructed URL ex. http://server.com/access/point
        """
        if href is not None:
            return "http://" + self.teamcity.server + href

        url = self.base_url

        locator_str = str(self._locator)
        if locator_str:
            if details:
                url += locator_str
            else:
                url += "?locator=" + locator_str

        return url

    def _fetch(self, details=False, href=None):
        """Execute the query on the server.

        Keyword Arguments:
            details {bool} -- [description] (default: {False})
            href {str} -- Hyperlink reference to use instead of base_url. (default: None)

        Raises:
            UnauthorizedError: Not authorized for server.
            HTTPError: Bad status code.

        Returns:
            dict -- Decoded json response.
        """
        self.url = self._get_url(details=details, href=href)
        res = self.teamcity.session.get(self.url)

        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                exception_class = exceptions.UnauthorizedError
            else:
                exception_class = exceptions.HTTPError
            raise exception_class(
                status_code=status_code, reason=str(e), text=e.response.text
            )

        data = res.json()
        return data

    def _data(self, details=False, href=None):
        """Return the data form the query, performing the query if necessary.

        Keyword Arguments:
            details {bool} -- [description] (default: {False})
            href {str} -- Hyperlink reference to use instead of base_url. (default: None)

        Returns:
            dict -- Data from query.
        """
        if not self._data_dict:
            self._data_dict = self._fetch(details=details, href=href)

        return self._data_dict

    @classmethod
    def _from_dict(cls, d, query_set):
        return cls._entity_factory.from_dict(d, query_set)

    def get(self, just_url=False, raise_multiple_objects_returned=False, **kwargs):
        """Perform the query or return the URL of the query.

        Keyword Arguments:
            just_url {bool} -- Return the URL for the query. (default: False)
            raise_multiple_objects_returned {bool} -- Raise a MultipleObjectsReturned exception when more than one objects retrieved. (default: False)

        Raises:
            exceptions.MultipleObjectsReturned: [description]

        Returns:
            #TODO|str -- Executed query or URL for the query.
        """
        self.filter(**kwargs)
        if raise_multiple_objects_returned and len(self) > 1:
            raise exceptions.MultipleObjectsReturned()
        self._data_dict = None
        if just_url:
            return self._get_url(details=True)
        else:
            return self.__class__._from_dict(self._data(details=True), self)

    def __len__(self):
        data = self._data()
        return data["count"]

    def __next__(self):  # pragma: no cover
        return next(self.__iter__())

    next = __next__

    def __getitem__(self, index):
        try:
            return next(itertools.islice(self, index, index + 1))
        except TypeError:  # pragma: no cover
            return list(itertools.islice(self, index.start, index.stop, index.step))

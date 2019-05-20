import os

import requests

from .core.manager import Manager
from .core.utils import parse_date_string, raise_on_status

from .agent import AgentQuerySet
from .agent_pool import AgentPoolQuerySet
from .build import BuildQuerySet
from .build_type import BuildTypeQuerySet
from .change import ChangeQuerySet
from .project import ProjectQuerySet
from .queued_build import QueuedBuildQuerySet
from .user import UserQuerySet
from .user_group import UserGroupQuerySet
from .vcs_root import VCSRootQuerySet


class Plugin(object):
    """Object to represent a Teamcity plugin.

    Attributes:
        name {str} -- Name of plugin.
        display_name {str} -- How plugin is displayed in Teamcity.
        version {str} -- Version of the plugin
        load_path {str} -- # TODO: Not sure
    """

    def __init__(self, name, display_name, version, load_path):
        """Create plugin.

        Arguments:
            name {str} -- Name of plugin.
            display_name {str} -- How plugin is displayed in Teamcity.
            version {str} -- Version of the plugin
            load_path {str} -- # TODO: Not sure
        """
        self.name = name
        self.display_name = display_name
        self.version = version
        self.load_path = load_path

    def __repr__(self):
        return "<%s.%s: name=%r display_name=%r version=%r>" % (
            self.__module__,
            self.__class__.__name__,
            self.name,
            self.display_name,
            self.version,
        )


class TeamCity(object):
    """[summary]
    """
    username = None
    password = None
    server = None
    protocol = None
    port = None
    session = None

    def __init__(
        self,
        username=None,
        password=None,
        protocol="http",
        server="127.0.0.1",
        port=None,
        session=None,
    ):
        """Create Teamcity instance to interact with a sever.

        Keyword Arguments:
            username {str} -- Username to access server with. (default: None)
            password {str} -- Passowrd to access server with. (default: None)
            protocol {str} -- Which protocol to use. ('http', 'https') (default: 'http')
            server {str} -- Address of the server. (default: '127.0.0.1')
            port {int} -- Port of the server. Only specify if not standard for protocol. (default: None)
            session {requests.Session} -- An existing requests.Session to the server. (default: None)
        """
        self.username = username
        self.password = password
        self.protocol = protocol
        self.server = server
        self.port = port or (443 if protocol == "https" else 80)
        self.session = session or requests.Session()
        self.session.auth = (username, password)
        self.session.headers["Accept"] = "application/json"
        self.projects = Manager(teamcity=self, query_set_factory=ProjectQuerySet)
        self.build_types = Manager(teamcity=self, query_set_factory=BuildTypeQuerySet)
        self.builds = Manager(teamcity=self, query_set_factory=BuildQuerySet)
        self.queued_builds = Manager(
            teamcity=self, query_set_factory=QueuedBuildQuerySet
        )
        self.users = Manager(teamcity=self, query_set_factory=UserQuerySet)
        self.user_groups = Manager(teamcity=self, query_set_factory=UserGroupQuerySet)
        self.agents = Manager(teamcity=self, query_set_factory=AgentQuerySet)
        self.agent_pools = Manager(teamcity=self, query_set_factory=AgentPoolQuerySet)
        self.vcs_roots = Manager(teamcity=self, query_set_factory=VCSRootQuerySet)
        self.changes = Manager(teamcity=self, query_set_factory=ChangeQuerySet)

        self.base_base_url = "%s://%s" % (self.protocol, self.server)
        if self.protocol == "http" and self.port != 80:
            self.base_base_url += ":%d" % self.port
        if self.protocol == "https" and self.port != 443:
            self.base_base_url += ":%d" % self.port

        if self.username and self.password:
            self.base_url = self.base_base_url + "/httpAuth"
            self.auth = (self.username, self.password)
        else:
            self.base_url = self.base_base_url + "/guestAuth"
            self.auth = None

    def relative_url(self, uri):
        """Construct a full URL given a relative URI.
        BASE_URL / uri

        Arguments:
            uri {str} -- Relative URI to the base url server.

        Returns:
            str -- Constructed URL.
        """
        return "%s/%s" % (self.base_url, uri)

    @classmethod
    def from_environ(cls):
        """Construct a Teamcity instance from the environment. Requires the following to be defined.
            TEAMCITY_PROTO
            TEAMCITY_USER
            TEAMCITY_PASSWORD
            TEAMCITY_HOST

        Returns:
            Teamctiy -- Constructed instance.
        """
        return TeamCity(
            protocol=os.environ.get("TEAMCITY_PROTO"),
            username=os.environ.get("TEAMCITY_USER"),
            password=os.environ.get("TEAMCITY_PASSWORD"),
            server=os.environ.get("TEAMCITY_HOST"),
        )

    def plugins(self):
        """Get a list of installed plugins on the server.

        Returns:
            list(Plugins) -- Installed plugins.
        """
        url = self.base_url + "/app/rest/server/plugins"
        res = self.session.get(url)
        raise_on_status(res)  # TODO: Examine the reason for this.
        data = res.json()
        plugins = []
        for plugin in data["plugin"]:
            plugins.append(
                Plugin(
                    name=plugin.get("name"),
                    display_name=plugin.get("displayName"),
                    version=plugin.get("version"),
                    load_path=plugin.get("loadPath"),
                )
            )
        return plugins

    @property
    def server_info(self):
        """Get all generic information related to Teamcity server.

        Returns:
            TeamcityServerInfo -- Information about Teamcity server.
        """
        url = self.base_url + "/app/rest/server"
        res = self.session.get(url)
        raise_on_status(res)

        data = res.json()
        return TeamCityServerInfo(
            version=data["version"],
            version_major=data["versionMajor"],
            version_minor=data["versionMinor"],
            build_number=data["buildNumber"],
            start_time_str=data["startTime"],
            current_time_str=data["currentTime"],
            build_date_str=data["buildDate"],
            internal_id=data["internalId"],
            web_url=data["webUrl"],
        )


class TeamCityServerInfo(object):
    """Object to represent generic Teamcity server information.

    Attributes:
        name {str} -- Name of plugin.
        display_name {str} -- How plugin is displayed in Teamcity.
        version {str} -- Version of the plugin
        load_path {str} -- # TODO: Not sure
    """

    def __init__(
        self,
        version,
        version_major,
        version_minor,
        build_number,
        start_time_str,
        current_time_str,
        build_date_str,
        internal_id,
        web_url,
    ):
        """Create generic Teamcity information.

        Arguments:
            version {str} -- [description]
            version_major {str} -- [description]
            version_minor {str} -- [description]
            build_number {str} -- [description]
            start_time_str {#TODO} -- [description]
            current_time_str {#TODO} -- [description]
            build_date_str {str} -- [description]
            internal_id {str} -- [description]
            web_url {str} -- [description]
        """
        self.version = version
        self.version_major = version_major
        self.version_minor = version_minor
        self.build_number = build_number
        self.start_time_str = start_time_str
        self.current_time_str = current_time_str
        self.build_date_str = build_date_str
        self.internal_id = internal_id
        self.web_url = web_url

    def __repr__(self):
        return "<%s.%s: web_url=%r version=%r>" % (
            self.__module__,
            self.__class__.__name__,
            self.web_url,
            self.version,
        )

    @property
    def start_time(self):
        return parse_date_string(self.start_time_str)

    @property
    def current_time(self):
        return parse_date_string(self.current_time_str)

    @property
    def build_date(self):
        return parse_date_string(self.build_date_str)

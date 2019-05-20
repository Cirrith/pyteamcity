class Manager(object):
    """Manage a query set factory.
    """

    def __init__(self, teamcity, query_set_factory):
        """Create a manager for a specific teamcity instance

        Arguments:
            teamcity {Teamcity} -- Teamcity instance to manage query set for.
            query_set_factory {QuerySet} -- Query set.
        """
        self.teamcity = teamcity
        self.query_set_factory = query_set_factory

    def all(self):
        """# TODO

        Returns:
            [type] -- [description]
        """
        return self.query_set_factory(teamcity=self.teamcity)

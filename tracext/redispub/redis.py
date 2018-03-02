"""Core Redis client component."""

from __future__ import absolute_import


from trac.config import Option, IntOption, PathOption
from trac.core import Component, TracError

import redis


class RedisClient(Component):
    """
    A mini-component for managing a `redis.Redis` client instance (and its
    underlying connection pool) for use by other components that use Redis, as
    well as options passed to the client.
    """

    _config_section = 'redis_client'

    _redis_client_options = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'unix_socket_path': (None, 'path')
    }


    _type_to_option_getter = {
        type(None): 'get',
        str: 'get',
        int: 'getint',
        'path': 'getpath'
    }

    def __init__(self):
        super(RedisClient, self).__init__()
        self.redis = redis.Redis(**self._client_options())

    def _client_options(self):
        """
        Read supported arguments to `redis.Redis` from the Trac config.
        """

        options = {}
        for key, value in self._redis_client_options.items():
            if isinstance(value, tuple):
                if len(value) == 1:
                    default = value[0]
                    type_ = None
                elif len(value) == 2:
                    default, type_ = value
            else:
                default = value
                type_ = None

            if type_ is None:
                # Infer type from the default type
                type_ = type(default)

            getter = getattr(self.env.config,
                             self._type_to_option_getter[type_])
            options[key] = getter(self._config_section, key, default)

        return options


class RedisComponent(Component):
    """
    A simple base class for `Component`s that provides a ``.redis`` property
    returning the `Redis` client instance of the `RedisClient` component.
    """

    channel_prefix = Option('redispub', 'channel_prefix', 'trac',
                            doc="Prefix to use for channels published to by "
                                "components of this plug-in.  All other "
                                "channels are dotted with this name; e.g. "
                                "trac.<envname>.ticket.created")

    _realm = None
    """
    The realm (e.g. 'ticket', 'wiki') handled by subclasses of this component.
    """

    def __init__(self):
        if not self.env.is_enabled(RedisClient):
            raise TracError(
                "The {0}.{1} component must be enabled in order to use the "
                "{0}.{2} component.".format(__name__, RedisClient.__name__,
                                            self.__class__.__name__))

        super(RedisComponent, self).__init__()

    @property
    def redis(self):
        """Returns the `Redis` client instance."""

        return self.env[RedisClient].redis

    def _channel_name(self, method):
        channel = method
        if self._realm is not None:
            channel = self._realm + '.' + channel
        channel = self.env.name + '.' + channel
        if self.channel_prefix:
            channel = self.channel_prefix + '.' + channel
        return channel

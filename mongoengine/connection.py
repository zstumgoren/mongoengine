from pymongo import Connection
from pymongo.master_slave_connection import MasterSlaveConnection


__all__ = ['ConnectionError', 'connect', 'register_connection']

"""
Sample configuration:

DATABASES = {
    'default': {
        'host': '127.0.0.1',
        'port': 27017,
        'slaves': ['slave1', 'slave2']
    },
    'slave1': {
        'host': '127.0.0.1',
        'port': 28001,
        'slave': True,
    },
    'slave2': {
        'host': '127.0.0.1',
        'port': 28002,
        'slave': True,
    },
}
"""

DEFAULT_CONNECTION_NAME = 'default'

class ConnectionError(Exception):
    pass


_connection_settings = {}
_connections = {}
_dbs = {}

def register_connection(alias, name, host='localhost', port=27017, 
                        is_slave=False, slaves=None, pool_size=1, 
                        username=None, password=None):
    """Add a connection. 
    
    :param alias: the name that will be used to refer to this connection 
        throughout MongoEngine
    :param name: the name of the specific database to use
    :param host: the host name of the :program:`mongod` instance to connect to
    :param port: the port that the :program:`mongod` instance is running on
    :param is_slave: whether the connection can act as a slave
    :param slaves: a list of aliases of slave connections; each of these must
        be a registered connection that has :attr:`is_slave` set to ``True``
    :param pool_size: the size of the connection pool - cannot be used with
        authentication
    :param username: username to authenticate with
    :param password: password to authenticate with
    """
    global _connection_settings
    _connection_settings[alias] = {
        'name': name,
        'host': host,
        'port': port,
        'is_slave': is_slave,
        'slaves': slaves or [],
        'pool_size': pool_size,
        'username': username,
        'password': password,
    }

def _get_connection(alias=DEFAULT_CONNECTION_NAME):
    global _connections
    # Connect to the database if not already connected
    if alias not in _connections:
        if alias not in _connection_settings:
            msg = 'Connection with alias "%s" has not been defined'
            if alias == DEFAULT_CONNECTION_NAME:
                msg = 'You have not defined a default connection'
            raise ConnectionError(msg)
        conn_settings = _connection_settings[alias]

        # Get all the slave connections
        slaves = []
        for slave_alias in conn_settings['slaves']:
            slaves.append(_get_connection(slave_alias))

        try:
            conn = Connection(
                host=conn_settings['host'], 
                port=conn_settings['port'],
                pool_size=conn_settings['pool_size'],
                slave_okay=conn_settings['is_slave']
            )
            # Create a master slave connection if slaves have been specified
            if slaves:
                conn = MasterSlaveConnection(conn, slaves)
            _connections[alias] = conn
        except Exception, e:
            raise e
            raise ConnectionError('Cannot connect to database %s' % alias)
    return _connections[alias]


def _get_db(alias=DEFAULT_CONNECTION_NAME):
    global _dbs
    if alias not in _dbs:
        conn = _get_connection(alias)
        conn_settings = _connection_settings[alias]
        _dbs[alias] = conn[conn_settings['name']]

        # Authenticate if necessary
        if conn_settings['username'] and conn_settings['password']:
            _dbs[alias].authenticate(conn_settings['username'],
                                     conn_settings['password'])
    return _dbs[alias]

def connect(name, **kwargs):
    """Connect to the database specified by the 'db' argument. Connection 
    settings may be provided here as well if the database is not running on
    the default port on localhost. If authentication is needed, provide
    username and password arguments as well.

    .. note::
       In this is now just a shortcut for 
       :func:`mongoengine.connection.register_connection`, with :attr:`alias`
       set to ``default``.
    """
    register_connection(DEFAULT_CONNECTION_NAME, name, **kwargs)

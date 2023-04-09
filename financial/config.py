"""
Variables used in both local and prod
So we don't need to re reclare and miss
the fields if we ever refactor...
"""
import os
import logging


def get(key, default):
    # Get default config from dev vs prod
    value = os.environ.get(key)
    if not value and ENV == PRODUCTION:
        raise Exception('env config "{0}" is missing'.format(key))
    return value or default


# Environment Specific
LOCAL = 'local'
PRODUCTION = 'production'
ENV = os.environ.get('FLASK_ENV', LOCAL)


if ENV == LOCAL:
    LOG_LEVEL = logging.DEBUG
    DEBUG = True

elif ENV == PRODUCTION:
    LOG_LEVEL = logging.INFO
    DEBUG = False


# Flask
SECRET_KEY = get('FLASK_SECRET_KEY', 'dev')


# App 
DB_HOST = os.environ.get('DB_HOST', '172.17.0.1')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_PORT = os.environ.get('DB_PORT', 3306)
DB_DATABASE = os.environ.get('DB_DATABASE', 'dev')
DB_TABLE = os.environ.get('DB_TABLE', 'financial_data')

DB_CONNECT_STR = 'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}'.format(
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE)

API_CONNECT_DB_STR = 'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}'.format(
    DB_USER, DB_PASSWORD, '127.0.0.1' , DB_PORT, DB_DATABASE)

# Third party
API_KEY = os.environ.get('API_KEY', 'YTAZ2LQUO5JP1C01')
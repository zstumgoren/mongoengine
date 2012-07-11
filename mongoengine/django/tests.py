#coding: utf-8
from django.conf import settings
from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner

from mongoengine import connect
from mongoengine.connection import register_connection, DEFAULT_CONNECTION_NAME

class MongoTestCase(TestCase):
    """
    TestCase class that clears the collection between the tests
    """
    test_db = 'test_%s' % settings.MONGO_DATABASE_NAME

    def __init__(self, methodName='runtest'):
        self.db = connect(DEFAULT_CONNECTION_NAME)[self.test_db]
        super(MongoTestCase, self).__init__(methodName)

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        for collection in self.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)

class MongoTestRunner(DjangoTestSuiteRunner):
    """Test runner for Mongo and, optionally, a RDBMS backend.

    In addition to invoking standard Django test db creation for relational backends,
    this test suite runner creates a test Mongo database.

    Inspired by `django-mongorunner <https://github.com/xintron/django-mongorunner>`_

    USAGE

    In settings.py, configure the following variables:

        MONGO_DATABASE_NAME = 'my-mongo-db'
        TEST_RUNNER = 'mongoengine.django.tests.MongoTestRunner'

    This create a temporary 'test_my-mongo-db' database for each test run.

    """

    rdbms = settings.DATABASES['default'].get('NAME','')
    test_db = 'test_%s' % settings.MONGO_DATABASE_NAME

    def setup_databases(self, **kwargs):
        # If a relational db is configured, invoke standard Django RDBMS setup
        if self.rdbms:
            self.old_config = super(MongoTestRunner, self).setup_databases(**kwargs)
        register_connection('default', self.test_db)
        print 'Creating test Mongo database: ' + self.test_db
        return self.test_db

    def teardown_databases(self, db_name, **kwargs):
        # If a RDBMS is configured, invoke standard Django RDBMS teardown
        if self.rdbms:
            super(MongoTestRunner, self).teardown_databases(self.old_config, **kwargs)
        from pymongo import Connection
        conn = Connection()
        conn.drop_database(db_name)
        print 'Dropping test Mongo database: ' + db_name 

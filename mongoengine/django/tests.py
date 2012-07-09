#coding: utf-8
from django.conf import settings
from django.test import TestCase, TransactionTestCase
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

class MongoTestCase2(TransactionTestCase):
    """TestCase for standalone MongoDB backend that rebuilds db for each test method.

        MONGO_DATABASE_NAME = 'my-mongo-db'
        TEST_RUNNER = 'mongoengine.django.tests.MongoTestRunner'

    USAGE:
    
        from mongoengine.django.tests import MongoTestCase2
        from myapp.models import MyDoc

        class MyTestCase(MongoTestCase2)

            def test_stuff(self):
                mydoc = MyDoc(foo='bar')
                mydoc.save()
                self.assertEquals(mydoc.foo, 'bar')

    """

    def _fixture_setup(self):
        pass


class MongoTestRunner(DjangoTestSuiteRunner):
    """Test runner for running Mongo without an RDBMS

    Sets up and tears down a test database for each test method.
    Inspired by `django-mongorunner <https://github.com/xintron/django-mongorunner>`_

    USAGE:

    In settings.py, configure the following variables:

        TEST_RUNNER = 'mongoengine.django.tests.MongoTestRunner'

    """

    test_db = 'test_%s' % settings.MONGO_DATABASE_NAME

    def setup_databases(self, **kwargs):
        register_connection('default', self.test_db)
        print 'Creating test database: ' + self.test_db
        return self.test_db

    def teardown_databases(self, db_name, **kwargs):
        from pymongo import Connection
        conn = Connection()
        conn.drop_database(self.db_name)
        print 'Dropping test database: ' + self.db_name

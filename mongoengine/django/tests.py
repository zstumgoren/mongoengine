#coding: utf-8
from django.conf import settings
from django.test import TransactionTestCase
from django.test.simple import DjangoTestSuiteRunner

from mongoengine import connect
from mongoengine.connection import register_connection, DEFAULT_CONNECTION_NAME

class MongoTestRunner(DjangoTestSuiteRunner):
    """Test runner for Mongo and, optionally, a relational database backend.

    Extends `DjangoTestsuiteRunner's <https://github.com/django/django/blob/master/django/test/simple.py>`_
    setup_databases and teardown_databases methods.  MongoTestRunner always creates a test Mongo db, but
    only creates a test relational db if an RDBMS has been configured in settings.py. 

    Intended for use with MongoTestCase.

    Inspired by `django-mongorunner <https://github.com/xintron/django-mongorunner>`_
    
    USAGE

    ~ settings.py ~

        MONGO_DATABASE_NAME = 'my-mongo-db'
        TEST_RUNNER = 'mongoengine.django.tests.MongoTestRunner'

    Once configured, import MongoTestCase in test files and use in same 
    way as standard unittest or Django TestCase. 
    
    """
    rdbms = settings.DATABASES['default'].get('NAME','')
    test_db = 'test_%s' % settings.MONGO_DATABASE_NAME

    def setup_databases(self, **kwargs):
        """Extends DjangoTestSuiteRunner to setup test mongo db."""
        # If a relational db is configured, invoke standard Django RDBMS setup
        if self.rdbms:
            self.old_config = super(MongoTestRunner, self).setup_databases(**kwargs)
        register_connection('default', self.test_db)
        print 'Creating test Mongo database: ' + self.test_db
        return self.test_db

    def teardown_databases(self, db_name, **kwargs):
        """Extends DjangoTestSuiteRunner to tear down test mongo db."""
        # If a RDBMS is configured, invoke standard Django RDBMS teardown
        if self.rdbms:
            super(MongoTestRunner, self).teardown_databases(self.old_config, **kwargs)
        from pymongo import Connection
        conn = Connection()
        conn.drop_database(db_name)
        print 'Dropping test Mongo database: ' + db_name 

class MongoTestCase(TransactionTestCase):
    """TestCase class that clears the test Mongo db collections between tests methods.

    In order to use this class, you must first configure the MongoTestRunner in settings.py

    ~ tests.py ~

        from mongoengine.django.tests import MongoTestCase
        from myapp.documents import Person

        class FooTest(MongoTestCase):
            
            def setUp(self):
                person = Person(name='Guido',title='BDFL')
                person.save()
                 
            def test_person_lookup(self):
                self.assertEquals(Person.objects.get(title='BDFL').name, 'Guido')


    """
    test_db = 'test_%s' % settings.MONGO_DATABASE_NAME

    def __init__(self, methodName='runtest'):
        self.db = connect(DEFAULT_CONNECTION_NAME)[self.test_db]
        super(MongoTestCase, self).__init__(methodName)

    def _fixture_setup(self):
        pass

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        for collection in self.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)


#!/usr/bin/env python
"""
_DBFormatterTest_

Unit tests for the DBFormatter class

"""

__revision__ = "$Id: DBFormatter_t.py,v 1.5 2008/11/04 15:42:41 fvlingen Exp $"
__version__ = "$Revision: 1.5 $"

import commands
import logging
import unittest
import os
import threading

from WMCore.Database.DBFactory import DBFactory
from WMCore.Database.DBFormatter import DBFormatter
from WMCore.Database.Transaction import Transaction

class DBFormatterTest(unittest.TestCase):
    """
    _DBFormatterTest_
    
    Unit tests for the DBFormatter class
    
    """

    _setup = False
    _teardown = False

    def setUp(self):
        "make a logger instance and create tables"
     
        if not DBFormatterTest._setup:
            logging.basicConfig(level=logging.NOTSET,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='%s.log' % __file__.replace('.py',''),
                    filemode='w')
        
            myThread = threading.currentThread()
            myThread.logger = logging.getLogger('DBFormatterTest')
            myThread.dialect = 'MySQL'

            options = {}
            dburl = ''
            if os.getenv("DATABASE"):
                dburl = os.getenv("DATABASE")
                options['unix_socket'] = os.getenv("DBSOCK")
                myThread.create = """
create table test (bind1 varchar(20), bind2 varchar(20)) ENGINE=InnoDB """
            else:
                dburl = 'sqlite:///:memory:'
                myThread.create = """
                    create table test (bind1 varchar(20), bind2 varchar(20))"""
                
            dbFactory = DBFactory(myThread.logger, dburl, \
                options)

            myThread.dbi = dbFactory.connect()

            
        
            myThread.insert = """
insert into test (bind1, bind2) values (:bind1, :bind2) """
            myThread.insert_binds = \
              [ {'bind1':'value1a', 'bind2': 'value2a'},\
                {'bind1':'value1b', 'bind2': 'value2b'},\
                {'bind1':'value1c', 'bind2': 'value2d'} ]
            myThread.select = "select * from test"
            DBFormatterTest._setup = True
            
    def tearDown(self):
        """
        Delete the databases
        """
        myThread = threading.currentThread()
        if DBFormatterTest._teardown and myThread.dialect == 'MySQL':
            # call the script we use for cleaning:
            command = os.getenv('WMCOREBASE')+ '/standards/./cleanup_mysql.sh'
            result = commands.getstatusoutput(command)
            for entry in result:
                print(str(entry))

        DBFormatterTest._teardown = False

    def testAPrepare(self):
        """
        Prepare database by inserting schema and values

        """

        myThread = threading.currentThread()
        myThread.transaction = Transaction(myThread.dbi)
        myThread.transaction.processData(myThread.create)
        myThread.transaction.processData(myThread.insert, myThread.insert_binds)
        myThread.transaction.commit()

    def testBFormatting(self):
        """
        Test various formats
        """

        myThread = threading.currentThread()
        dbformatter = DBFormatter(myThread.logger, myThread.dbi)
        myThread.transaction.begin()

        result = myThread.transaction.processData(myThread.select)
        output = dbformatter.format(result)
        assert output ==  [['value1a', 'value2a'], \
            ['value1b', 'value2b'], ['value1c', 'value2d']]
        result = myThread.transaction.processData(myThread.select)
        output = dbformatter.formatOne(result)
        print('test1 '+str(output))
        assert output == ['value1a', 'value2a']
        result = myThread.transaction.processData(myThread.select)
        output = dbformatter.formatDict(result)
        assert output == [{'bind2': 'value2a', 'bind1': 'value1a'}, \
            {'bind2': 'value2b', 'bind1': 'value1b'},\
            {'bind2': 'value2d', 'bind1': 'value1c'}]
        result = myThread.transaction.processData(myThread.select)
        output = dbformatter.formatOneDict(result)
        assert output ==  {'bind2': 'value2a', 'bind1': 'value1a'}
        DBFormatterTest.__teardown = True

    def runTest(self):
        self.testAPrepare()
        self.testBFormatting()
            
if __name__ == "__main__":
    unittest.main()     
             

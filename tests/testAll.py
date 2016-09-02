import unittest
from testAccount import AccountTest
from testQuery import QueryTest
from testReports import ReportTest
import sys


def test_suite():
    """ Test Suite for omnitue module """

    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(AccountTest))
    test_suite.addTest(unittest.makeSuite(QueryTest))
    test_suite.addTest(unittest.makeSuite(ReportTest))

    return test_suite

mySuite = test_suite()

runner = unittest.TextTestRunner()
ret = runner.run(mySuite).wasSuccessful()
sys.exit(not ret)

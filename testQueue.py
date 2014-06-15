#!/usr/bin/python

import unittest
import omniture
import sys
import os
import pprint

creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.analytics = omniture.authenticate(creds['username'], creds['secret'])
        reportdef = self.analytics.suites[0].report
        queue = []
        queue.append(reportdef)
        self.report = omniture.sync(queue)

    def test_ranked(self):
        basic_report = self.analytics.suites[0].report.element("page")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)

        for report in response:
            self.assertEqual(report.elements[0].id, "page", "The element is wrong")
            self.assertEqual(len(report.elements), 1, "There are too many elements")
            self.assertEqual(report.type, "ranked", "This is the wrong type of report it should be ranked")

    def test_report_run(self):
        self.assertIsInstance(self.analytics.suites[0].report.run(), omniture.Report, "The run method doesn't work to create a report")
    
    def test_bad_element(self):
        self.assertRaises(KeyError,self.analytics.suites[0].report.element, "pages")
    

    def test_overtime(self):
        basic_report = self.analytics.suites[0].report.metric("orders").granularity("hour")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
    

    def test_double_element(self):
        basic_report = self.analytics.suites[0].report.element("page").element("browser")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.elements[0].id,"page", "The 1st element is wrong")
            self.assertEqual(report.elements[1].id,"browser", "The 2nd element is wrong")
            self.assertEqual(len(report.elements), 2, "The number of elements is wrong")
            self.assertEqual(report.type, "ranked", "This is the wrong type of report it should be ranked")

   
    def test_double_metric(self):
        basic_report = self.analytics.suites[0].report.metric("pageviews").metric("visits")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.metrics[0].id,"pageviews", "The 1st element is wrong")
            self.assertEqual(report.metrics[1].id,"visits", "The 2nd element is wrong")
            self.assertEqual(len(report.metrics), 2, "The number of elements is wrong")
            self.assertEqual(report.type, "overtime", "This is the wrong type of report it should be overtime")
    
    def test_element_paratmers(self):
        """Test the top and startingWith parameters
        This isn't a conclusive test. I really should run to two reports and compare the results to make sure it is corrent
        However, these tests need to be able run on any report suite and some reports suites (like ones that are currenly being 
        used) don't have 10 items in the page name
        """
        basic_report = self.analytics.suites[0].report.element("page", top=5, startingWith=5)
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.elements['page'].id, "page" ,"The parameters might have screwed this up")
    
    @unittest.skip("don't have this one done yet")
    def test_anamoly_detection(self):
        basic_report = self.analytics.suites[0].report.metric("pageviews").range('2014-05-1', '2014-05-07').anomaly_detection()
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.metrics, "upper bound" ,"Anomaly Detection isn't working")
            
    def test_sortBy(self):
            """ Make sure sortBy gets put in report description """
            basic_report = self.analytics.suites[0].report.element('page').metric('pageviews').metric('visits').sortBy('visits')
            self.assertEqual(basic_report.raw['sortBy'], "visits")

    def test_current_data(self):
        """ Make sure the current data flag gets set correctly """
        basic_report = self.analytics.suites[0].report.element('page').metric('pageviews').metric('visits').currentData()
        self.assertEqual(basic_report.raw['currentData'], True)


if __name__ == '__main__':
    unittest.main()

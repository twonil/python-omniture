#!/usr/bin/python

import unittest
import omniture
import sys
import os
import pprint

creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']
test_suite = 'omniture.api-gateway'


class QueryTest(unittest.TestCase):
    def setUp(self):
        self.analytics = omniture.authenticate(creds['username'], creds['secret'])
        reportdef = self.analytics.suites[test_suite].report
        queue = []
        queue.append(reportdef)
        self.report = omniture.sync(queue)

    def test_ranked(self):
        basic_report = self.analytics.suites[test_suite].report.element("page")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)

        for report in response:
            self.assertEqual(report.elements[0].id, "page", "The element is wrong")
            self.assertEqual(len(report.elements), 1, "There are too many elements")
            self.assertEqual(report.type, "ranked", "This is the wrong type of report it should be ranked")

    def test_report_run(self):
        self.assertIsInstance(self.analytics.suites[test_suite].report.run(), omniture.Report, "The run method doesn't work to create a report")
    
    def test_bad_element(self):
        self.assertRaises(KeyError,self.analytics.suites[test_suite].report.element, "pages")
    

    def test_overtime(self):
        basic_report = self.analytics.suites[test_suite].report.metric("orders").granularity("hour")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
    

    def test_double_element(self):
        basic_report = self.analytics.suites[test_suite].report.element("page").element("browser")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.elements[0].id,"page", "The 1st element is wrong")
            self.assertEqual(report.elements[1].id,"browser", "The 2nd element is wrong")
            self.assertEqual(len(report.elements), 2, "The number of elements is wrong")
            self.assertEqual(report.type, "ranked", "This is the wrong type of report it should be ranked")

    def test_elements(self):
        report = self.analytics.suites[test_suite].report.elements("page","browser").run()
        self.assertEqual(report.elements[0].id,"page", "The 1st element is wrong")
        self.assertEqual(report.elements[1].id,"browser", "The 2nd element is wrong")
        self.assertEqual(len(report.elements), 2, "The number of elements is wrong")
        self.assertEqual(report.type, "ranked", "This is the wrong type of report it should be ranked")
        
    def test_double_metric(self):
        basic_report = self.analytics.suites[test_suite].report.metric("pageviews").metric("visits")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.metrics[0].id,"pageviews", "The 1st element is wrong")
            self.assertEqual(report.metrics[1].id,"visits", "The 2nd element is wrong")
            self.assertEqual(len(report.metrics), 2, "The number of elements is wrong")
            self.assertEqual(report.type, "overtime", "This is the wrong type of report it should be overtime")
    
    def test_metrics(self):
        report = self.analytics.suites[test_suite].report.metrics("pageviews", "visits").run()
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
        basic_report = self.analytics.suites[test_suite].report.element("page", top=5, startingWith=5)
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.elements['page'].id, "page" ,"The parameters might have screwed this up")
    
    @unittest.skip("don't have this one done yet")
    def test_anamoly_detection(self):
        basic_report = self.analytics.suites[test_suite].report.metric("pageviews").range('2014-05-1', '2014-05-07').anomaly_detection()
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)
        
        for report in response:
            self.assertEqual(report.metrics, "upper bound" ,"Anomaly Detection isn't working")
            
    def test_sortBy(self):
            """ Make sure sortBy gets put in report description """
            basic_report = self.analytics.suites[test_suite].report.element('page').metric('pageviews').metric('visits').sortBy('visits')
            self.assertEqual(basic_report.raw['sortBy'], "visits")

    def test_current_data(self):
        """ Make sure the current data flag gets set correctly """
        basic_report = self.analytics.suites[test_suite].report.element('page').metric('pageviews').metric('visits').currentData()
        self.assertEqual(basic_report.raw['currentData'], True)
        
    def test_inline_segments(self):
        """ Make sure inline segments work """
        report = self.analytics.suites[test_suite].report.element('page').metric('pageviews').metric('visits').filter(element='page', selected=["test","test1"])
        self.assertEqual(report.raw['segments'][0]['element'], "page", "The inline segment element isn't getting set")
        self.assertEqual(report.raw['segments'][0]['selected'], ["test","test1"], "The inline segment selected field isn't getting set")

    def test_hour_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_suite].report.granularity('hour')
        self.assertEqual(report.raw['dateGranularity'], "hour", "Hourly granularity can't be set via the granularity method")
   
    def test_day_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_suite].report.granularity('day')
        self.assertEqual(report.raw['dateGranularity'], "day", "daily granularity can't be set via the granularity method")
 
    def test_week_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_suite].report.granularity('day')
        self.assertEqual(report.raw['dateGranularity'], "day", "Weekly granularity can't be set via the granularity method")

    def test_quarter_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_suite].report.granularity('quarter')
        self.assertEqual(report.raw['dateGranularity'], "quarter", "Quarterly granularity can't be set via the granularity method")
        
    def test_year_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_suite].report.granularity('year')
        self.assertEqual(report.raw['dateGranularity'], "year", "Yearly granularity can't be set via the granularity method")
        
    def test_single_date_range(self):
        """ Make sure date range works with a single date """
        report = self.analytics.suites[test_suite].report.range('2014-01-01')
        self.assertEqual(report.raw['date'], "2014-01-01", "Can't set a single date")
        
    def test_date_range(self):
        """ Make sure date range works with two dates """
        report = self.analytics.suites[test_suite].report.range('2014-01-01','2014-01-02')
        self.assertEqual(report.raw['dateFrom'], "2014-01-01", "Start date isn't getting set correctly")
        self.assertEqual(report.raw['dateTo'], "2014-01-02", "End date isn't getting set correctly")
        
    def test_granularity_date_range(self):
        """ Make sure granularity works in the date range app """
        report = self.analytics.suites[test_suite].report.range('2014-01-01','2014-01-02', granularity='hour')
        self.assertEqual(report.raw['dateFrom'], "2014-01-01", "Start date isn't getting set correctly")
        self.assertEqual(report.raw['dateTo'], "2014-01-02", "End date isn't getting set correctly")  
        self.assertEqual(report.raw['dateGranularity'], "hour", "Hourly granularity can't be set via the range method")
        
        
if __name__ == '__main__':
    unittest.main()

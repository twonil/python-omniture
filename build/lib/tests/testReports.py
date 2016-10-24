#!/usr/bin/python
from __future__ import print_function


import unittest
import omniture
import os
from datetime import date
import pandas
import datetime
import requests_mock


creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']
test_report_suite = 'omniture.api-gateway'


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with requests_mock.mock() as m:
            path = os.path.dirname(__file__)
            #read in mock response for Company.GetReportSuites to make tests faster
            with open(path+'/mock_objects/Company.GetReportSuites.json') as get_report_suites_file:
                report_suites = get_report_suites_file.read()

            with open(path+'/mock_objects/Report.GetMetrics.json') as get_metrics_file:
                metrics = get_metrics_file.read()

            with open(path+'/mock_objects/Report.GetElements.json') as get_elements_file:
                elements = get_elements_file.read()

            with open(path+'/mock_objects/Segments.Get.json') as get_segments_file:
                segments = get_segments_file.read()

            #setup mock responses
            m.post('https://api.omniture.com/admin/1.4/rest/?method=Company.GetReportSuites', text=report_suites)
            m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.GetMetrics', text=metrics)
            m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.GetElements', text=elements)
            m.post('https://api.omniture.com/admin/1.4/rest/?method=Segments.Get', text=segments)


            self.analytics = omniture.authenticate(creds['username'], creds['secret'])
            #force requests to happen in this method so they are cached
            self.analytics.suites[test_report_suite].metrics
            self.analytics.suites[test_report_suite].elements
            self.analytics.suites[test_report_suite].segments

    def tearDown(self):
        self.analytics = None

    @requests_mock.mock()
    def test_basic_report(self,m):
        """ Make sure a basic report can be run
        """

        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        response = self.analytics.suites[test_report_suite].report.run()

        self.assertIsInstance(response.data, list, "Something went wrong with the report")

        #Timing Info
        self.assertIsInstance(response.timing['queue'], float, "waitSeconds info is missing")
        self.assertIsInstance(response.timing['execution'], float, "Execution info is missing")
        #Raw Reports
        self.assertIsInstance(response.report, dict, "The raw report hasn't been populated")
        #Check Metrics
        self.assertIsInstance(response.metrics, list, "The metrics weren't populated")
        self.assertEqual(response.metrics[0].id,"pageviews", "Wrong Metric")
        #Check Elements
        self.assertIsInstance(response.elements, list, "The elements is the wrong type")
        self.assertEqual(response.elements[0].id,"datetime", "There are elements when there shouldn't be")

        #check time range
        checkdate = date(2016,9,4).strftime("%a. %e %h. %Y")
        self.assertEqual(response.period, checkdate)

        #check segmetns
        self.assertIsNone(response.segments)

        #Check Data
        self.assertIsInstance(response.data, list, "Data isn't getting populated right")
        self.assertIsInstance(response.data[0] , dict, "The data isn't getting into the dict")
        self.assertIsInstance(response.data[0]['datetime'], datetime.datetime, "The date isn't getting populated in the data")
        self.assertIsInstance(response.data[0]['pageviews'], int, "The pageviews aren't getting populated in the data")

    @requests_mock.mock()
    def test_ranked_report(self, m):
        """ Make sure the ranked report is being processed
        """

        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/ranked_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        ranked = self.analytics.suites[test_report_suite].report.element("page").metric("pageviews").metric("visits")
        queue = []
        queue.append(ranked)
        response = omniture.sync(queue)

        for report in response:
            #Check Data
            self.assertIsInstance(report.data, list, "Data isn't getting populated right")
            self.assertIsInstance(report.data[0] , dict, "The data isn't getting into the dict")
            self.assertIsInstance(report.data[0]['page'], str, "The page isn't getting populated in the data")
            self.assertIsInstance(report.data[0]['pageviews'], int, "The pageviews aren't getting populated in the data")
            self.assertIsInstance(report.data[0]['visits'], int, "The visits aren't getting populated in the data")

    @requests_mock.mock()
    def test_trended_report(self,m):
        """Make sure the trended reports are being processed corretly"""

        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/trended_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)


        trended = self.analytics.suites[test_report_suite].report.element("page").metric("pageviews").granularity('hour').run()
        self.assertIsInstance(trended.data, list, "Treneded Reports don't work")
        self.assertIsInstance(trended.data[0] , dict, "The data isn't getting into the dict")
        self.assertIsInstance(trended.data[0]['datetime'], datetime.datetime, "The date isn't getting propulated correctly")
        self.assertIsInstance(trended.data[0]['page'], str, "The page isn't getting populated in the data")
        self.assertIsInstance(trended.data[0]['pageviews'], int, "The pageviews aren't getting populated in the data")

    @requests_mock.mock()
    def test_dataframe(self,m):
        """Make sure the pandas data frame object can be generated"""


        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/trended_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        trended = self.analytics.suites[test_report_suite].report.element("page").metric("pageviews").granularity('hour').run()
        self.assertIsInstance(trended.dataframe, pandas.DataFrame, "Data Frame Object doesn't work")

    @requests_mock.mock()
    def test_segments_id(self,m):
        """ Make sure segments can be added """

        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/segmented_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        suite = self.analytics.suites[test_report_suite]
        report = suite.report.filter(suite.segments[0]).run()

        self.assertEqual(report.segments[0], suite.segments[0], "The segments don't match")

    @unittest.skip("skip inline segments because checked in Query")
    def test_inline_segment(self):
        """ Make sure inline segments work """
        #pretty poor check but need to make it work with any report suite
        report = self.analytics.suites[0].report.element('page').metric('pageviews').metric('visits').filter(element='browser', selected=["::unspecified::"]).run()
        self.assertIsInstance(report.data, list, "inline segments don't work")

    @requests_mock.mock()
    def test_multiple_classifications(self, m):
        """Makes sure the report can parse multiple classifications correctly since they have the same element ID"""
        #load sample file
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/multi_classifications.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            ReportQueue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=ReportQueue)

        report = self.analytics.suites[0].report\
            .element('evar2',classification="Classification 1", disable_validation=True)\
            .element('evar2',classification="Classification 2", disable_validation=True)\

        report = report.run()

        self.assertTrue('evar2 | Classification 1' in report.data[0], "The Value of report.data[0] was:{}".format(report.data[0]))
        self.assertTrue('evar2 | Classification 2' in report.data[0], "The Value of report.data[0] was:{}".format(report.data[0]))

    @requests_mock.mock()
    def test_mixed_classifications(self, m):
        """Makes sure the report can parse reports with classifications and
        regular dimensionscorrectly since they have the same element ID"""
        #load sample files with responses for mock objects
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/mixed_classifications.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            ReportQueue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=ReportQueue)

        report = self.analytics.suites[0].report\
            .element('evar3',classification="Classification 1", disable_validation=True)\
            .element('evar5', disable_validation=True)\

        report = report.run()

        self.assertTrue('evar3 | Classification 1' in report.data[0], "The Value of report.data[0] was:{}".format(report.data[0]))
        self.assertTrue('evar5' in report.data[0], "The Value of report.data[0] was:{}".format(report.data[0]))

    @requests_mock.mock()
    def test_repr_html_(self,m):
        """Test the _repr_html_ method used by iPython for notebook display"""
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/trended_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        with open(path+'/mock_objects/trended_report.html') as basic_html_file:
            basic_html = basic_html_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        trended = self.analytics.suites[test_report_suite].report\
            .element("page").metric("pageviews").granularity('hour').run()


        self.assertEqual(trended._repr_html_(),basic_html)

    @requests_mock.mock()
    def test__div__(self,m):
        """Test the __div__ method for tab autocompletion"""
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        response = self.analytics.suites[test_report_suite].report.run()
        self.assertEqual(response.__div__(), \
                         ['data','dataframe', 'metrics','elements', 'segments', 'period', 'type', 'timing'],
                         "the __dir__ method broke: {}".format(response.__div__()))

    @requests_mock.mock()
    def test__repr__(self,m):
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        response = self.analytics.suites[test_report_suite].report.run()
        test_string = """<omniture.Report
(metrics)
ID pageviews                 | Name: Page Views 
(elements)
ID datetime                  | Name: Date 
>"""
        self.assertEqual(response.__repr__(),test_string)


if __name__ == '__main__':
    unittest.main()

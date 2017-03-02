#!/usr/bin/python

import unittest
import requests_mock
import omniture
import os

creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']
test_report_suite = 'omniture.api-gateway'
dateTo = "2015-06-02"
dateFrom = "2015-06-01"
date = dateTo


class QueryTest(unittest.TestCase):
    def setUp(self):
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

    def test_ranked(self):
        """Test that a basic query can be generated """
        basic_report = self.analytics.suites[test_report_suite].report.element("page")
        self.assertEqual(basic_report.raw['elements'][0]['id'], "page", "The element is wrong: {}".format(basic_report.raw['elements'][0]['id']))
        self.assertEqual(len(basic_report.raw['elements']), 1, "There are too many elements: {}".format(basic_report.raw['elements']))

    @requests_mock.mock()
    def test_report_run(self,m):
        """Make sure that are report can actually be run """
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)


        self.assertIsInstance(self.analytics.suites[test_report_suite].report.run(), omniture.Report, "The run method doesn't work to create a report")
        
    @requests_mock.mock()
    def test_report_run(self,m):
        """Make sure that the interval gets passed down. Needs a bit of work to make the test usefule """
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)


        self.assertIsInstance(self.analytics.suites[test_report_suite].report.run(interval=0.01), omniture.Report, "The run method doesn't work to create a report")
        self.assertIsInstance(self.analytics.suites[test_report_suite].report.run(interval=2), omniture.Report, "The run method doesn't work to create a report")
        self.assertIsInstance(self.analytics.suites[test_report_suite].report.run(interval=31), omniture.Report, "The run method doesn't work to create a report")

    @requests_mock.mock()
    def test_report_async(self,m):
        """Make sure that are report are run Asynchrnously """
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/basic_report.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        query = self.analytics.suites[test_report_suite].report.async()
        self.assertIsInstance(query, omniture.Query, "The Async method doesn't work")
        self.assertTrue(query.check(), "The check method is weird")
        self.assertIsInstance(query.get_report(), omniture.Report, "The check method is weird")
    
    @requests_mock.mock()
    def test_report_bad_async(self,m):
        """Make sure that are report can't be checked on out of order """
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/Report.Get.NotReady.json') as data_file:
            json_response = data_file.read()

        with open(path+'/mock_objects/Report.Queue.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Get', text=json_response)
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        
        with self.assertRaises(omniture.query.ReportNotSubmittedError): 
            self.analytics.suites[test_report_suite].report.get_report()
        query = self.analytics.suites[test_report_suite].report.async()
        self.assertIsInstance(query, omniture.Query, "The Async method doesn't work")
        self.assertFalse(query.check(), "The check method is weird")
        with self.assertRaises(omniture.reports.ReportNotReadyError): 
            query.get_report()
            
    #@unittest.skip("skip")
    def test_bad_element(self):
        """Test to make sure the element validation is working"""
        self.assertRaises(KeyError,self.analytics.suites[test_report_suite].report.element, "pages")

    @unittest.skip("Test Not Finished")
    def test_overtime(self):
        basic_report = self.analytics.suites[test_report_suite].report.metric("orders").granularity("hour")
        queue = []
        queue.append(basic_report)
        response = omniture.sync(queue)

    #@unittest.skip("skip")
    def test_double_element(self):
        """Test to make sure two elements will work in the report"""
        basic_report = self.analytics.suites[test_report_suite].report.element("page").element("browser")
        self.assertEqual(basic_report.raw['elements'][0]['id'],"page", "The 1st element is wrong")
        self.assertEqual(basic_report.raw['elements'][1]['id'],
                         "browser", "The 2nd element is wrong: {}"
                         .format(basic_report.raw['elements'][1]['id']))
        self.assertEqual(len(basic_report.raw['elements']), 2, "The number of elements is wrong: {}".format(basic_report.raw['elements']))


    #@unittest.skip("skip")
    def test_elements(self):
        """ Make sure the Elements method works as a shortcut for adding multiple
        elements"""
        basic_report = self.analytics.suites[test_report_suite].report.elements("page","browser")
        self.assertEqual(basic_report.raw['elements'][0]['id'],"page", "The 1st element is wrong: {}".format(basic_report.raw['elements'][0]['id']))
        self.assertEqual(basic_report.raw['elements'][1]['id'],"browser", "The 2nd element is wrong: {}".format(basic_report.raw['elements'][1]['id']))
        self.assertEqual(len(basic_report.raw['elements']), 2, "The number of elements is wrong: {}".format(basic_report.raw['elements']))

    #@unittest.skip("skip")
    def test_double_metric(self):
        """ Make sure multiple metric calls get set correcly """
        basic_report = self.analytics.suites[test_report_suite].report.metric("pageviews").metric("visits")

        self.assertEqual(basic_report.raw['metrics'][0]['id'],"pageviews", "The 1st element is wrong")
        self.assertEqual(basic_report.raw['metrics'][1]['id'],"visits", "The 2nd element is wrong")
        self.assertEqual(len(basic_report.raw['metrics']), 2, "The number of elements is wrong")

    #@unittest.skip("skip")
    def test_metrics(self):
        """ Make sure the metrics method works as a shortcut for multiple
        metrics"""
        basic_report = self.analytics.suites[test_report_suite].report.metrics("pageviews", "visits")

        self.assertEqual(basic_report.raw['metrics'][0]['id'],"pageviews", "The 1st element is wrong")
        self.assertEqual(basic_report.raw['metrics'][1]['id'],"visits", "The 2nd element is wrong")
        self.assertEqual(len(basic_report.raw['metrics']), 2, "The number of elements is wrong")


    #@unittest.skip("skip")
    def test_element_parameters(self):
        """Test the top and startingWith parameters
        """
        basic_report = self.analytics.suites[test_report_suite].report.element("page", top=5, startingWith=5)

        self.assertEqual(basic_report.raw['elements'][0]['id'],
                         "page" ,
                         "The parameters might have screwed this up: {}"
                         .format(basic_report.raw['elements'][0]['id']))
        self.assertEqual(basic_report.raw['elements'][0]['top'],
                         5 ,
                         "The top parameter isn't 5: {}"
                         .format(basic_report.raw['elements'][0]['top']))
        self.assertEqual(basic_report.raw['elements'][0]['startingWith'],
                         5 ,
                         "The startingWith parameter isn't 5: {}"
                         .format(basic_report.raw['elements'][0]['startingWith']))
        
    def test_breakown_parameters(self):
        """Test the top and startingWith parameters
        """
        basic_report = self.analytics.suites[test_report_suite].report.breakdown("page", top=5, startingWith=5)

        self.assertEqual(basic_report.raw['elements'][0]['id'],
                         "page" ,
                         "The parameters might have screwed this up: {}"
                         .format(basic_report.raw['elements'][0]['id']))
        self.assertEqual(basic_report.raw['elements'][0]['top'],
                         5 ,
                         "The top parameter isn't 5: {}"
                         .format(basic_report.raw['elements'][0]['top']))
        self.assertEqual(basic_report.raw['elements'][0]['startingWith'],
                         5 ,
                         "The startingWith parameter isn't 5: {}"
                         .format(basic_report.raw['elements'][0]['startingWith']))
        
    def test_set(self):
        """ Make sure the set parameter can create custom parameters okay """
        report = self.analytics.suites[test_report_suite].report\
            .set('anomalyDetection',True)\
            .set({"test":"abc","currentData":True})
            
        self.assertEqual(report.raw['anomalyDetection'], True)
        self.assertEqual(report.raw['test'], "abc")
        self.assertEqual(report.raw['currentData'], True)
        
        with self.assertRaises(ValueError):
            report.set()

    @unittest.skip("don't have this one done yet")
    def test_anamoly_detection(self):
        basic_report = self.analytics.suites[test_report_suite].report.metric("pageviews").range(dateFrom, dateTo).anomaly_detection()

        self.assertEqual(basic_report.raw['anomalyDetection'],"True", "anomalyDetection isn't getting set: {}".format(basic_report.raw))

    #@unittest.skip("skip")
    def test_sortBy(self):
            """ Make sure sortBy gets put in report description """
            basic_report = self.analytics.suites[test_report_suite].report.element('page').metric('pageviews').metric('visits').sortBy('visits')
            self.assertEqual(basic_report.raw['sortBy'], "visits")

    #@unittest.skip("skip")
    def test_current_data(self):
        """ Make sure the current data flag gets set correctly """
        basic_report = self.analytics.suites[test_report_suite].report.element('page').metric('pageviews').metric('visits').currentData()
        self.assertEqual(basic_report.raw['currentData'], True)

    #@unittest.skip("skip")
    def test_inline_segments(self):
        """ Make sure inline segments work """
        report = self.analytics.suites[test_report_suite].report\
            .element('page')\
            .metric('pageviews')\
            .metric('visits')\
            .filter(element='page', selected=["test","test1"])
        self.assertEqual(report.raw['segments'][0]['element'], "page", "The inline segment element isn't getting set")
        self.assertEqual(report.raw['segments'][0]['selected'], ["test","test1"], "The inline segment selected field isn't getting set")

    def test_inline_segments_disable_validation(self):
        """ Make sure inline segments work with disable_validation = True """
        report = self.analytics.suites[test_report_suite].report\
            .element('page')\
            .metric('pageviews')\
            .metric('visits')\
            .filter(element='page', selected=["test","test1"], disable_validation=True)
        self.assertEqual(report.raw['segments'][0]['element'], "page", "The inline segment element isn't getting set")
        self.assertEqual(report.raw['segments'][0]['selected'], ["test","test1"], "The inline segment selected field isn't getting set")

    
    def test_filter(self):
        """ Make sure the filter command sets the segments right """
        report1 = self.analytics.suites[test_report_suite].report\
            .filter("s4157_55b1ba24e4b0a477f869b912")\
            .filter(segment = "s4157_56097427e4b0ff9bcc064952")
        reportMultiple = self.analytics.suites[test_report_suite].report\
            .filter(segments = ["s4157_55b1ba24e4b0a477f869b912","s4157_56097427e4b0ff9bcc064952"])
            
        self.assertIn({'id': u's4157_55b1ba24e4b0a477f869b912'}\
                      ,report1.raw['segments'], "Report1 failing")
        self.assertIn({'id': u's4157_56097427e4b0ff9bcc064952'}\
                      ,report1.raw['segments'], "report1 failing")
        
        self.assertIn({'id': u's4157_55b1ba24e4b0a477f869b912'}\
                      ,reportMultiple.raw['segments'], "reportMultiple failing")
        self.assertIn({'id': u's4157_56097427e4b0ff9bcc064952'}\
                      ,reportMultiple.raw['segments'], "reportMultiple failing")
        
        with self.assertRaises(ValueError):
            report1.filter()
        
        
    def test_filter_disable_validation(self):
        """ Make sure the filter command sets the segments 
        right when validation is disabled"""
        report1 = self.analytics.suites[test_report_suite].report\
            .filter("s4157_55b1ba24e4b0a477f869b912", disable_validation=True)\
            .filter(segment = "s4157_56097427e4b0ff9bcc064952",\
                    disable_validation=True)
        reportMultiple = self.analytics.suites[test_report_suite].report\
            .filter(segments = ["s4157_55b1ba24e4b0a477f869b912","s4157_56097427e4b0ff9bcc064952"],\
                    disable_validation=True)
            
        self.assertIn({'id': u's4157_55b1ba24e4b0a477f869b912'}\
                      ,report1.raw['segments'], "Report1 failing")
        self.assertIn({'id': u's4157_56097427e4b0ff9bcc064952'}\
                      ,report1.raw['segments'], "report1 failing")
        
        self.assertIn({'id': u's4157_55b1ba24e4b0a477f869b912'}\
                      ,reportMultiple.raw['segments'], "reportMultiple failing")
        self.assertIn({'id': u's4157_56097427e4b0ff9bcc064952'}\
                      ,reportMultiple.raw['segments'], "reportMultiple failing")
        
        with self.assertRaises(ValueError):
            report1.filter(disable_validation=True)
        

    #@unittest.skip("skip")
    def test_hour_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_report_suite].report.granularity('hour')
        self.assertEqual(report.raw['dateGranularity'], "hour", "Hourly granularity can't be set via the granularity method")

    #@unittest.skip("skip")
    def test_day_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_report_suite].report.granularity('day')
        self.assertEqual(report.raw['dateGranularity'], "day", "daily granularity can't be set via the granularity method")

    #@unittest.skip("skip")
    def test_week_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_report_suite].report.granularity('day')
        self.assertEqual(report.raw['dateGranularity'], "day", "Weekly granularity can't be set via the granularity method")

    #@unittest.skip("skip")
    def test_quarter_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_report_suite].report.granularity('quarter')
        self.assertEqual(report.raw['dateGranularity'], "quarter", "Quarterly granularity can't be set via the granularity method")

    #@unittest.skip("skip")
    def test_year_granularity(self):
        """ Make sure granularity works """
        report = self.analytics.suites[test_report_suite].report.granularity('year')
        self.assertEqual(report.raw['dateGranularity'], "year", "Yearly granularity can't be set via the granularity method")

    def test_bad_granularity(self):
        """ Make sure granularity works """
        with self.assertRaises(ValueError):
            self.analytics.suites[test_report_suite].report.granularity('bad')
            
    #@unittest.skip("skip")
    def test_single_date_range(self):
        """ Make sure date range works with a single date """
        report = self.analytics.suites[test_report_suite].report.range(date)
        self.assertEqual(report.raw['date'], date, "Can't set a single date")

    #@unittest.skip("skip")
    def test_date_range(self):
        """ Make sure date range works with two dates """
        report = self.analytics.suites[test_report_suite].report.range(dateFrom,dateTo)
        self.assertEqual(report.raw['dateFrom'], dateFrom, "Start date isn't getting set correctly")
        self.assertEqual(report.raw['dateTo'], dateTo, "End date isn't getting set correctly")
        
    def test_date_range_days(self):
        """Make sure the dayes can be passed into the range function and that they work correctly"""
        cDateFrom = "2017-01-01"
        cDateTo = "2017-01-02"
        report = self.analytics.suites[test_report_suite].report.range(cDateFrom,days=2)
        self.assertEqual(report.raw['dateFrom'],cDateFrom, "Start Data isnt' working")
        self.assertEqual(report.raw['dateTo'], cDateTo,"Check the days param of the range function")

    def test_date_range_months(self):
        """Make sure the dayes can be passed into the range function and that they work correctly"""
        cDateFrom = "2017-01-01"
        cDateTo = "2017-03-31"
        report = self.analytics.suites[test_report_suite].report.range(cDateFrom,months=3)
        self.assertEqual(report.raw['dateFrom'],cDateFrom, "Start Data isnt' working")
        self.assertEqual(report.raw['dateTo'], cDateTo,"Check the days param of the range function")


    #@unittest.skip("skip")
    def test_granularity_date_range(self):
        """ Make sure granularity works in the date range app """
        report = self.analytics.suites[test_report_suite].report.range(dateFrom,dateTo, granularity='hour')
        self.assertEqual(report.raw['dateFrom'], dateFrom, "Start date isn't getting set correctly")
        self.assertEqual(report.raw['dateTo'], dateTo, "End date isn't getting set correctly")
        self.assertEqual(report.raw['dateGranularity'], "hour", "Hourly granularity can't be set via the range method")

    ##@unittest.skip("skip")
    def test_jsonReport(self):
        """Check the JSON deserializer"""
        report = self.analytics.suites[test_report_suite].report.range(dateFrom,dateTo,granularity='day')\
            .set("source","standard")\
            .metric("pageviews")\
            .metric("visits")\
            .element("page")\
            .element("sitesection", top=100, startingWith=1)\
            .set("locale","en_US")\
            .sortBy("visits")\
            .set("anomalyDetection",True)\
            .set("currentData", True)\
            .set("elementDataEncoding","utf8")

        testreport = self.analytics.suites[test_report_suite].jsonReport(report.json())
        self.assertEqual(report.json(),testreport.json(), "The reportings aren't deserializing from JSON the same old:{} new:{}".format(report.json(),testreport.json()))
        self.assertEqual(report.json(),testreport.__str__(), "The reportings aren't deserializing to string __str__ the same old:{} new:{}".format(report.json(),testreport.__str__()))
        
    @requests_mock.mock()
    def test_disable_validate_metric(self,m):
        """checks that the no validate flag works for metrics"""
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/invalid_metric.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        with self.assertRaises(omniture.InvalidReportError) as e:
            report = self.analytics.suites[test_report_suite].report\
                .metric("bad_metric", disable_validation=True)\
                .run()

        self.assertTrue(("metric_id_invalid" in e.exception.message),"The API is returning an error that might mean this is broken")

    @requests_mock.mock()
    def test_disable_validate_element(self,m):
        """checks that the no validate flag works for elements"""
        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/invalid_element.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        with self.assertRaises(omniture.InvalidReportError) as e:
            report = self.analytics.suites[test_report_suite].report\
                .element("bad_element", disable_validation=True)\
                .run()

        self.assertTrue(("element_id_invalid" in e.exception.message),"The API is returning an error that might mean this is broken")

    @requests_mock.mock()
    def test_disable_validate_segments(self,m):
        """checks that the no validate flag works for segments"""

        path = os.path.dirname(__file__)

        with open(path+'/mock_objects/invalid_segment.json') as queue_file:
            report_queue = queue_file.read()

        #setup mock object
        m.post('https://api.omniture.com/admin/1.4/rest/?method=Report.Queue', text=report_queue)

        with self.assertRaises(omniture.InvalidReportError) as e:
            report = self.analytics.suites[test_report_suite].report\
                .filter("bad_segment", disable_validation=True)\
                .run()

        self.assertTrue(("segment_invalid" in e.exception.message),
                        "The API is returning an error that might mean this is broken: {}"
                        .format(e.exception.message))

    def test_multiple_classifications(self):
        """Checks to make sure that multiple classificaitons are handled correctly """
        report = self.analytics.suites[test_report_suite].report\
            .element("page", classification="test")\
            .element("page", classification= "test2")

        self.assertEqual("test",  report.raw['elements'][0]['classification'],"The classifications aren't getting set right")
        self.assertEqual("test2",  report.raw['elements'][1]['classification'],"The second classification isn't getting set right")

    def test__dir__(self):
        valid_value = ['async', 'breakdown', 'cancel', 'clone', 'currentData',
                 'element', 'filter', 'granularity', 'id', 'json',
                 'metric', 'queue', 'range', 'raw', 'report', 'request',
                 'run', 'set', 'sortBy', 'suite']
        test_value = self.analytics.suites[test_report_suite].report.__dir__()

        self.assertEqual(test_value,valid_value,
                         "The __dir__ method isn't returning right: {}"
                         .format(test_value))

    def test_repr_html_(self):
        """Make sure the HTML representation fo iPython is working corretly"""
        valid_html = "Current Report Settings</br><b>elements</b>: [{'id': 'page'}] </br><b>metrics</b>: [{'id': 'pageviews'}] </br><b>reportSuiteID</b>: "+test_report_suite+" </br>"
        test_html = self.analytics.suites[test_report_suite]\
            .report\
            .element('page')\
            .metric('pageviews')\
            ._repr_html_()


        self.assertEqual(test_html,valid_html,
                         "the HTML isn't generating correctly: {}"
                         .format(test_html))

    def test_repr_html_report_id(self):
        """Make sure the HTML representation fo iPython is working corretly
        with a report id"""
        valid_html = "Current Report Settings</br><b>elements</b>: [{'id': 'page'}] </br><b>metrics</b>: [{'id': 'pageviews'}] </br><b>reportSuiteID</b>: "+test_report_suite+" </br>This report has been submitted</br><b>ReportId</b>: 123 </br>"
        test_html = self.analytics.suites[test_report_suite]\
            .report\
            .element('page')\
            .metric('pageviews')
        test_html.id = "123"
        test_html = test_html._repr_html_()


        self.assertEqual(str(test_html),valid_html,
                         "the HTML isn't generating correctly: {}"
                         .format(test_html))
        
    def test_serialize_values(self):
        """Test the serialize method """
        
        
        single = self.analytics.suites[test_report_suite].report\
            ._serialize_values("s4157_55b1ba24e4b0a477f869b912", 'segments')
            
        double = self.analytics.suites[test_report_suite].report\
            ._serialize_values(["s4157_56097427e4b0ff9bcc064952"\
                               ,"s4157_55b1ba24e4b0a477f869b912"], 'segments')
            
        self.assertEqual(single, [{'id':"s4157_55b1ba24e4b0a477f869b912"}])
        self.assertEqual(double, [{'id':"s4157_56097427e4b0ff9bcc064952"},
                                  {'id':"s4157_55b1ba24e4b0a477f869b912"}])
        
    def test_serialize(self):
        l = self.analytics.suites[test_report_suite].report\
            ._serialize(['1','2'])
        obj = self.analytics.suites[test_report_suite].report\
            ._serialize(omniture.Value('title',"id",{}))
            
        self.assertEqual(l, ['1','2'])
        self.assertEqual(list(obj), ["id"])


if __name__ == '__main__':
    unittest.main()

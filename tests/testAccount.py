#!/usr/bin/python

import unittest
import requests_mock
import omniture
import os

creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']
test_report_suite = "omniture.api-gateway"


class AccountTest(unittest.TestCase):
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


    def test_os_environ(self):
        test = omniture.authenticate({'OMNITURE_USERNAME':creds['username'],
                                           'OMNITURE_SECRET':creds['secret']})
        self.assertEqual(test.username,creds['username'],
                         "The username isn't getting set right: {}"
                         .format(test.username))

        self.assertEqual(test.secret,creds['secret'],
                         "The secret isn't getting set right: {}"
                         .format(test.secret))

    def test_suites(self):
        self.assertIsInstance(self.analytics.suites, omniture.utils.AddressableList, "There are no suites being returned")
        self.assertIsInstance(self.analytics.suites[test_report_suite], omniture.account.Suite, "There are no suites being returned")

    def test_simple_request(self):
        """ simplest request possible. Company.GetEndpoint is not an authenticated method
        """
        urls = ["https://api.omniture.com/admin/1.4/rest/",
                "https://api2.omniture.com/admin/1.4/rest/",
                "https://api3.omniture.com/admin/1.4/rest/",
                "https://api4.omniture.com/admin/1.4/rest/",
                "https://api5.omniture.com/admin/1.4/rest/"]
        self.assertIn(self.analytics.request('Company', 'GetEndpoint'),urls, "Company.GetEndpoint failed" )

    def test_authenticated_request(self):
        """ Request that requires authentication to make sure the auth is working
        """
        reportsuites = self.analytics.request('Company','GetReportSuites')
        self.assertIsInstance(reportsuites, dict, "Didn't get a valid response back")
        self.assertIsInstance(reportsuites['report_suites'], list, "Response doesn't contain the list of report suites might be an authentication issue")

    def test_metrics(self):
        """ Makes sure the suite properties can get the list of metrics
        """
        self.assertIsInstance(self.analytics.suites[test_report_suite].metrics, omniture.utils.AddressableList)

    def test_elements(self):
        """ Makes sure the suite properties can get the list of elements
        """
        self.assertIsInstance(self.analytics.suites[test_report_suite].elements, omniture.utils.AddressableList)

    def test_basic_report(self):
        """ Make sure a basic report can be run
        """
        report = self.analytics.suites[test_report_suite].report
        queue = []
        queue.append(report)
        response = omniture.sync(queue)
        self.assertIsInstance(response, list)

    def test_json_report(self):
        """Make sure reports can be generated from JSON objects"""
        report = self.analytics.suites[test_report_suite].report\
            .element('page')\
            .metric('pageviews')\
            .sortBy('pageviews')\
            .filter("s4157_55b1ba24e4b0a477f869b912")\
            .range("2016-08-01","2016-08-31")\
            .set('sortMethod',"top")\
            .json()
        self.assertEqual(report, self.analytics.jsonReport(report).json(), "The reports aren't serializating or de-serializing correctly in JSON")

    
    def test_account_repr_html_(self):
        """Make sure the account are printing out in 
            HTML correctly for ipython notebooks"""
        html = self.analytics._repr_html_()
        test_html = "<b>Username</b>: jgrover:Justin Grover Demo</br><b>Secret</b>: ***************</br><b>Report Suites</b>: 2</br><b>Endpoint</b>: https://api.omniture.com/admin/1.4/rest/</br>"
        self.assertEqual(html, test_html)
        
    def test_account__str__(self):
        """ Make sure the custom str works """
        mystr = self.analytics.__str__()
        test_str = "Analytics Account -------------\n Username:             jgrover:Justin Grover Demo \n Report Suites: 2 \n Endpoint: https://api.omniture.com/admin/1.4/rest/"
        self.assertEqual(mystr, test_str)

    def test_suite_repr_html_(self):
        """Make sure the Report Suites are printing okay for 
        ipython notebooks """
        html = self.analytics.suites[0]._repr_html_()
        test_html = "<td>omniture.api-gateway</td><td>test_suite</td>"
        self.assertEqual(html, test_html)
        
    def test_suite__str__(self):
        """Make sure the str represntation is working """
        mystr = self.analytics.suites[0].__str__()
        test_str = "ID omniture.api-gateway      | Name: test_suite \n"
        self.assertEqual(mystr,test_str)


if __name__ == '__main__':
    unittest.main()

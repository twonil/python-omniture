import requests
import binascii
import time
import sha
import json
from datetime import datetime
from elements import Value, Element, Segment
from query import Query
import reports
import utils
import logging
import random
import uuid

class Account(object):
    """ A wrapper for the Adobe Analytics API. Allows you to query the reporting API """
    DEFAULT_ENDPOINT = 'https://api.omniture.com/admin/1.4/rest/'

    def __init__(self, username, secret, endpoint=DEFAULT_ENDPOINT):
        """Authentication to make requests."""
        self.log = logging.getLogger(__name__)
        self.username = username
        self.secret = secret
        self.endpoint = endpoint
        data = self.request('Company', 'GetReportSuites')['report_suites']
        suites = [Suite(suite['site_title'], suite['rsid'], self) for suite in data]
        self.suites = utils.AddressableList(suites)
        
    def request(self, api, method, query={}):
        """
        Make a request to the Adobe APIs.

        * api -- the class of APIs you would like to call (e.g. Report,
            ReportSuite, Company, etc.)
        * method -- the method you would like to call inside that class
            of api
        * query -- a python object representing the parameters you would
            like to pass to the API
        """
        self.log.info("Request: %s.%s  Parameters: %s", api, method, query)
        response = requests.post(
            self.endpoint,
            params={'method': api + '.' + method},
            data=json.dumps(query),
            headers=self._build_token()
            )
        self.log.debug("Response for %s.%s:%s", api, method, response.text)
        json_response = response.json()

        if type(json_response) == dict:
            self.log.debug("Error Code %s", json_response.get('error'))
            if json_response.get('error') == 'report_not_ready':
                raise reports.ReportNotReadyError(json_response)
            elif json_response.get('error') != None:
                raise reports.InvalidReportError(json_response)
            else:
                return json_response
        else:
            return json_response

    def _serialize_header(self, properties):
        header = []
        for key, value in properties.items():
            header.append('{key}="{value}"'.format(key=key, value=value))
        return ', '.join(header)

    def _build_token(self):
        nonce = str(uuid.uuid4())
        base64nonce = binascii.b2a_base64(binascii.a2b_qp(nonce))
        created_date = datetime.utcnow().isoformat() + 'Z'
        sha_object = sha.new(nonce + created_date + self.secret)
        password_64 = binascii.b2a_base64(sha_object.digest())

        properties = {
            "Username": self.username,
            "PasswordDigest": password_64.strip(),
            "Nonce": base64nonce.strip(),
            "Created": created_date,
        }
        header = 'UsernameToken ' + self._serialize_header(properties)

        return {'X-WSSE': header}

    def _repr_html_(self):
        """ Format in HTML for iPython Users """
        html = ""
        html += "<b>{0}</b>: {1}</br>".format("Username", self.username)
        html += "<b>{0}</b>: {1}</br>".format("Secret", "***************")
        html += "<b>{0}</b>: {1}</br>".format("Report Suites", len(self.suites))
        html += "<b>{0}</b>: {1}</br>".format("Endpoint", self.endpoint)
        return html

    def __str__(self):
        return "Analytics Account -------------\n Username: \
            {0} \n Report Suites: {1} \n Endpoint: {2}" \
            .format(self.username, len(self.suites), self.endpoint)


class Suite(Value):
    """Lets you query a specific report suite. """
    def request(self, api, method, query={}):
        raw_query = {}
        raw_query.update(query)
        if method == 'GetMetrics' or method == 'GetElements':
            raw_query['reportSuiteID'] = self.id

        return self.account.request(api, method, raw_query)

    def __init__(self, title, id, account):
        self.log = logging.getLogger(__name__)
        super(Suite, self).__init__(title, id, account)
        self.account = account

    @property
    @utils.memoize
    def metrics(self):
        """ Return the list of valid metricsfor the current report suite"""
        data = self.request('Report', 'GetMetrics')
        return Value.list('metrics', data, self, 'name', 'id')

    @property
    @utils.memoize
    def elements(self):
        """ Return the list of valid elementsfor the current report suite """
        data = self.request('Report', 'GetElements')
        return Element.list('elements', data, self, 'name', 'id')

    @property
    @utils.memoize
    def segments(self):
        """ Return the list of valid segments for the current report suite """
        data = self.request('Segments', 'Get')
        return Segment.list('segments', data, self, 'name', 'id')

    @property
    def report(self):
        """ Return a report to be run on this report suite """
        return Query(self)
    
    def _repr_html_(self):
        """ Format in HTML for iPython Users """
        return "<td>{0}</td><td>{1}</td>".format(self.id, self.title)
    
    def __str__(self):
        return "ID {0:25} | Name: {1} \n".format(self.id, self.title)

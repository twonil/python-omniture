# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function

import time
from copy import copy, deepcopy
import functools
from dateutil.relativedelta import relativedelta
import json
import logging
import sys

from .elements import Value
from . import reports
from . import utils


def immutable(method):
    @functools.wraps(method)
    def wrapped_method(self, *vargs, **kwargs):
        obj = self.clone()
        method(obj, *vargs, **kwargs)
        return obj

    return wrapped_method

class ReportNotSubmittedError(Exception):
    """ Exception that is raised when a is requested by hasn't been submitted 
        to Adobe
    """
    def __init__(self,error):
        self.log = logging.getLogger(__name__)
        self.log.debug("Report Has not been submitted, call async() or run()")
        super(ReportNotSubmittedError, self).__init__("Report Not Submitted")

class Query(object):
    """ Lets you build a query to the Reporting API for Adobe Analytics.

    Methods in this object are chainable. For example
    >>> report = report.element("page").element("prop1").
        metric("pageviews").granularity("day").run()
    Making it easy to create a report.

    To see the raw definition use
    >>> print report
    """

    GRANULARITY_LEVELS = ['hour', 'day', 'week', 'month', 'quarter', 'year']
    STATUSES = ["Not Submitted","Not Ready","Done"]

    def __init__(self, suite):
        """ Setup the basic structure of the report query. """
        self.log = logging.getLogger(__name__)
        self.suite = suite
        self.raw = {}
        #Put the report suite in so the user can print
        #the raw query and have it work as is
        self.raw['reportSuiteID'] = str(self.suite.id)
        self.id = None
        self.method = "Get"
        self.status = self.STATUSES[0]
        #The report object
        self.report = reports.Report
        #The fully hydrated report object
        self.processed_response = None  
        self.unprocessed_response = None

    def _normalize_value(self, value, category):
        if isinstance(value, Value):
            return value
        else:
            return getattr(self.suite, category)[value]

    def _serialize_value(self, value, category):
        return self._normalize_value(value, category).serialize()

    def _serialize_values(self, values, category):
        if not isinstance(values, list):
            values = [values]

        return [self._serialize_value(value, category) for value in values]

    def _serialize(self, obj):
        if isinstance(obj, list):
            return [self._serialize(el) for el in obj]
        elif isinstance(obj, Value):
            return obj.serialize()
        else:
            return obj

    def clone(self):
        """ Return a copy of the current object. """
        query = Query(self.suite)
        query.raw = copy(self.raw)
        query.report = self.report
        query.status = self.status
        query.processed_response = self.processed_response
        query.unprocessed_response = self.unprocessed_response
        return query

    @immutable
    def range(self, start, stop=None, months=0, days=0, granularity=None):
        """
        Define a date range for the report.

        * start -- The start date of the report. If stop is not present
            it is assumed to be the to and from dates.
        * stop (optional) -- the end date of the report (inclusive).
        * months (optional, named) -- months to run used for relative dates
        * days (optional, named)-- days to run used for relative dates)
        * granulartiy (optional, named) -- set the granularity for the report
        """
        start = utils.date(start)
        stop = utils.date(stop)

        if days or months:
            stop = start + relativedelta(days=days-1, months=months)
        else:
            stop = stop or start

        if start == stop:
            self.raw['date'] = start.isoformat()
        else:
            self.raw.update({
                'dateFrom': start.isoformat(),
                'dateTo': stop.isoformat(),
            })

        if granularity:
            self.raw = self.granularity(granularity).raw

        return self

    @immutable
    def granularity(self, granularity):
        """
        Set the granulartiy for the report.

        Values are one of the following
        'hour', 'day', 'week', 'month', 'quarter', 'year'
        """
        if granularity not in self.GRANULARITY_LEVELS:
                levels = ", ".join(self.GRANULARITY_LEVELS)
                raise ValueError("Granularity should be one of: " + levels)

        self.raw['dateGranularity'] = granularity

        return self

    @immutable
    def set(self, key=None, value=None, **kwargs):
        """
        Set a custom property in the report

        `set` is a way to add raw properties to the request,
        for features that python-omniture does not support but the
        SiteCatalyst API does support. For convenience's sake,
        it will serialize Value and Element objects but will
        leave any other kind of value alone.
        """

        if key and value:
            self.raw[key] = self._serialize(value)
        elif key or kwargs:
            properties = key or kwargs
            for key, value in properties.items():
                self.raw[key] = self._serialize(value)
        else:
            raise ValueError("Query#set requires a key and value, \
                             a properties dictionary or keyword arguments.")

        return self

    @immutable
    def filter(self, segment=None, segments=None, disable_validation=False, **kwargs):
        """ Set Add a segment to the report. """
        # It would appear to me that 'segment_id' has a strict subset
        # of the functionality of 'segments', but until I find out for
        # sure, I'll provide both options.
        if 'segments' not in self.raw:
            self.raw['segments'] = []

        if disable_validation == False:
            if segments:
                self.raw['segments'].extend(self._serialize_values(segments, 'segments'))
            elif segment:
                self.raw['segments'].append({"id":self._normalize_value(segment,
                                                                            'segments').id})
            elif kwargs:
                self.raw['segments'].append(kwargs)
            else:
                raise ValueError()

        else:
            if segments:
                self.raw['segments'].extend([{"id":segment} for segment in segments])
            elif segment:
                self.raw['segments'].append({"id":segment})
            elif kwargs:
                self.raw['segments'].append(kwargs)
            else:
                raise ValueError()
        return self

    @immutable
    def element(self, element, disable_validation=False, **kwargs):
        """
        Add an element to the report.

        This method is intended to be called multiple time. Each time it will
            add an element as a breakdown
        After the first element, each additional element is considered
            a breakdown
        """

        if self.raw.get('elements', None) == None:
            self.raw['elements'] = []

        if disable_validation == False:
            element = self._serialize_value(element, 'elements')
        else:
            element = {"id":element}

        if kwargs != None:
            element.update(kwargs)
        self.raw['elements'].append(deepcopy(element))

        #TODO allow this method to accept a list
        return self


    def breakdown(self, element, **kwargs):
        """ Pass through for element. Adds an element to the report. """
        return self.element(element, **kwargs)


    def elements(self, *args, **kwargs):
        """ Shortcut for adding multiple elements. Doesn't support arguments """
        obj = self
        for e in args:
            obj = obj.element(e, **kwargs)

        return obj

    @immutable
    def metric(self, metric, disable_validation=False):
        """
        Add an metric to the report.

        This method is intended to be called multiple time.
            Each time a metric will be added to the report
        """
        if self.raw.get('metrics', None) == None:
            self.raw['metrics'] = []
        if disable_validation == False:
            self.raw['metrics'].append(self._serialize_value(metric, 'metrics'))
        else:
            self.raw['metrics'].append({"id":metric})
        #self.raw['metrics'] = self._serialize_values(metric, 'metrics')
        #TODO allow this metric to accept a list
        return self

    def metrics(self, *args, **kwargs):
        """ Shortcut for adding multiple metrics """
        obj = self
        for m in args:
            obj = obj.metric(m, **kwargs)

        return obj

    @immutable
    def sortBy(self, metric):
        """ Specify the sortBy Metric """
        self.raw['sortBy'] = metric
        return self

    @immutable
    def currentData(self):
        """ Set the currentData flag """
        self.raw['currentData'] = True
        return self


    def build(self):
        """ Return the report descriptoin as an object """
        return {'reportDescription': self.raw}

    def queue(self):
        """ Submits the report to the Queue on the Adobe side. """
        q = self.build()
        self.log.debug("Suite Object: %s  Method: %s, Query %s",
                       self.suite, self.report.method, q)
        self.id = self.suite.request('Report',
                                     self.report.method,
                                     q)['reportID']
        self.status = self.STATUSES[1]
        return self

    def probe(self, heartbeat=None, interval=1, soak=False):
        """ Keep checking until the report is done"""
        #Loop until the report is done
        while self.is_ready() == False:
            if heartbeat:
                heartbeat()
            time.sleep(interval)
            #Use a back off up to 30 seconds to play nice with the APIs
            if interval < 1:
                interval = 1
            elif interval < 30:
                interval = round(interval * 1.5)
            else:
                interval = 30
            self.log.debug("Check Interval: %s seconds", interval)
            
    def is_ready(self):
        """ inspects the response to see if the report is ready """
        if self.status == self.STATUSES[0]:
            raise ReportNotSubmittedError('{"message":"Doh! the report needs to be submitted first"}')
        elif self.status == self.STATUSES[1]:
            try:
                # the request method catches the report and populates it automatically
                response = self.suite.request('Report','Get',{'reportID': self.id})
                self.status = self.STATUSES[2]
                self.unprocessed_response = response
                self.processed_response = self.report(response, self)
                return True
            except reports.ReportNotReadyError:
                self.status = self.STATUSES[1]
                #raise reports.InvalidReportError(response)
                return False
        elif self.status == self.STATUSES[2]:
            return True
        

    def sync(self, heartbeat=None, interval=0.01):
        """ Run the report synchronously,"""
        print("sync called")
        if self.status == self.STATUSES[0]:
            print("Queing Report")
            self.queue()
            self.probe(heartbeat, interval)
        if self.status == self.STATUSES[1]:
            self.probe()
        return self.processed_response

    def async(self, callback=None, heartbeat=None, interval=1):
        """ Run the Report Asynchrnously """
        if self.status == self.STATUSES[0]:
            self.queue()
        return self
        
    def get_report(self):
        self.is_ready()
        if self.status == self.STATUSES[2]:
            return self.processed_response
        else:
            raise reports.ReportNotReadyError('{"message":"Doh! the report is not ready yet"}')
        
    def run(self, defaultheartbeat=True, heartbeat=None, interval=0.01):
        """Shortcut for sync(). Runs the current report synchronously. """
        if defaultheartbeat == True:
            rheartbeat = self.heartbeat
        else:
            rheartbeat = heartbeat

        return self.sync(rheartbeat, interval)

    def heartbeat(self):
        """ A default heartbeat method that prints a dot for each request """
        sys.stdout.write('.')
        sys.stdout.flush()


    def check(self):
        """
            Basically an alias to is ready to make the interface a bit better
        """
        return self.is_ready()

    def cancel(self):
        """ Cancels a the report from the Queue on the Adobe side. """
        return self.suite.request('Report',
                                      'CancelReport',
                                      {'reportID': self.id})
    def json(self):
        """ Return a JSON string of the Request """
        return str(json.dumps(self.build(), indent=4, separators=(',', ': '), sort_keys=True))

    def __str__(self):
        return self.json()

    def _repr_html_(self):
        """ Format in HTML for iPython Users """
        report = { str(key):value for key,value in self.raw.items() }
        html = "Current Report Settings</br>"
        for k,v in sorted(list(report.items())):
            html += "<b>{0}</b>: {1} </br>".format(k,v)
        if self.id:
            html += "This report has been submitted</br>"
            html += "<b>{0}</b>: {1} </br>".format("ReportId", self.id)
        return html


    def __dir__(self):
        """ Give sensible options for Tab Completion mostly for iPython """
        return ['async','breakdown','cancel','clone','currentData', 'element',
                'filter', 'granularity', 'id','json' ,'metric', 'queue', 'range', 'raw', 'report',
                'request', 'run', 'set', 'sortBy', 'suite']

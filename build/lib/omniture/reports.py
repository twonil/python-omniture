# encoding: utf-8

from elements import Value, Element, Segment
import utils
import logging
from collections import OrderedDict
import json


class InvalidReportError(Exception):
    def normalize(self, error):
        print 'error', error
        return {
            'error': error.get('error'),
            'error_description': error.get('error_description'),
            'error_uri': error.get('error_uri', ''),
        }

    def __init__(self, error):
        self.log = logging.getLogger(__name__)
        error = self.normalize(error)
        message = "{error}: {error_description} ({error_uri})".format(**error)
        super(InvalidReportError, self).__init__(message)
        
class ReportNotReadyError(Exception):
    """ Exception that is raised when a report is not ready to be downloaded
    """
    def __init__(self,error):
        self.log = logging.getLogger(__name__)
        self.log.debug("Report Not Ready")
        super(ReportNotReadyError, self).__init__("Report Not Ready")


#  TODO: also make this iterable (go through rows)
class Report(object):
    def process(self):
        """ Parse out the relevant data from the report and store it for easy access
            Should only be used internally to the class
        """
        self.timing = {
            'queue': float(self.raw['waitSeconds']),
            'execution': float(self.raw['runSeconds']),
        }
        self.log.debug("Report Wait Time: %s, Report Execution Time: %s", self.timing['queue'], self.timing['execution'])
        self.report = report = self.raw['report']
        self.metrics = Value.list('metrics', report['metrics'], self.suite, 'name', 'id')
        self.elements = Value.list('elements', report['elements'], self.suite, 'name', 'id')
        self.period = str(report['period'])
        self.type = str(report['type'])
        
        segment = report.get('segment_id') 
        if segment:
            self.segment = self.query.suite.segments[report['segment_id']]
        else:
            self.segment = None

        #Set as none until it is actually used
        self.dict_data = None
        self.pandas_data = None

    @property
    def data(self):
        """ Returns the report data as a set of dicts for easy quering
            It generates the dicts on the 1st call then simply returns the reference to the data in subsequent calls
        """
        #If the data hasn't been generate it generate the data
        if self.dict_data == None:
            self.dict_data = self.parse_rows(self.report['data'])
            
        return self.dict_data
    
    def parse_rows(self,row, level=0, upperlevels=None):
        """ 
        Parse through the data returned by a repor. Return a list of dicts. 
        
        This method is recursive.
        """
        #self.log.debug("Level %s, Upperlevels %s, Row Type %s, Row: %s", level,upperlevels, type(row), row)
        data = {}
        data_set = []
        
        #merge in the upper levels
        if upperlevels != None:
            data.update(upperlevels)
            
        
        if type(row) == list:
            for r in row:
                #on the first call set add to the empty list 
                pr = self.parse_rows(r,level, data.copy())
                if type(pr) == dict:
                    data_set.append(pr)
                #otherwise add to the existing list
                else:
                    data_set.extend(pr)
                    
        #pull out the metrics from the lowest level
        if type(row) == dict:  
            #pull out any relevant data from the current record
            #Handle datetime isn't in the elements list for trended reports
            if level == 0 and self.type == "trended":
                element = "datetime"
            elif self.type == "trended":
                element = str(self.elements[level-1].id)
            else:
                element = str(self.elements[level].id)
            data[element] = str(row['name'])
            #parse out any breakdowns and add to the data set    
            if row.has_key('breakdown'):
                data_set.extend(self.parse_rows(row['breakdown'], level+1, data))
            elif row.has_key('counts'):
                for index, metric in enumerate(row['counts']):
                        #decide what type of event
                        if self.metrics[index].decimals > 0: 
                            data[str(self.metrics[index].id)] = float(metric)
                        else:
                            data[str(self.metrics[index].id)] = int(metric)
        
            
                                
        if len(data_set)>0: 
            return data_set
        else:   
            return data
                    
    @property    
    def dataframe(self):
        """ 
        Returns pandas DataFrame for additional analysis. 
        
        Will generate the data the first time it is called otherwise passes a cached version
        """
        
        if self.pandas_data is None:
            self.pandas_data = self.to_dataframe()
        
        return self.pandas_data
    
    
    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame.from_dict(self.data)
        

    def serialize(self, verbose=False):
        if verbose:
            facet = 'title'
        else:
            facet = 'id'

        d = {}
        for el in self.data:
            key = getattr(el, facet)
            d[key] = el.value
        return d

    def __init__(self, raw, query):
        self.log = logging.getLogger(__name__)
        self.raw = raw
        self.query = query
        self.suite = query.suite
        self.process()

    def __repr__(self):
        info = {
            'metrics': ", ".join(map(str, self.metrics)), 
            'elements': ", ".join(map(str, self.elements)), 
        }
        return "<omniture.RankedReport (metrics) {metrics} (elements) {elements}>".format(**info)
    
    def __str__(self):
        return json.dumps(self.report,indent=4, separators=(',', ': '))

Report.method = "Queue"
    

class OverTimeReport(Report):
    def process(self):
        super(OverTimeReport, self).process()

        # TODO: this works for over_time reports and I believe for ranked
        # reports as well, but trended reports have their data in 
        # `data.breakdown:[breakdown:[counts]]`
        for row in self.report['data']:
            for i, value in enumerate(row['counts']):
                if self.metrics[i].type == 'number':
                    value = float(value)
                self.data[i].append(value)

OverTimeReport.method = 'QueueOvertime'


class RankedReport(Report):
    def process(self):
        super(RankedReport, self).process()

        for row in self.report['data']:
            for i, value in enumerate(row['counts']):
                if self.metrics[i].type == 'number':
                    value = float(value)
                self.data[i].append((row['name'], row['url'], value))

RankedReport.method = 'QueueRanked'


class TrendedReport(Report):
    def process(self):
        super(TrendedReport, self).process()

TrendedReport.method = 'QueueTrended'


class DataWarehouseReport(object):
    pass

DataWarehouseReport.method = 'Request'


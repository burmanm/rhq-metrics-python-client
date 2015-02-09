import json
import urllib2
import httplib
import time

class MetricType:
    Numeric = 'numeric'
    Availability = 'availability'

    @staticmethod
    def short(metric_type):
        if metric_type is 'numeric':
            return 'num'
        else:
            return 'avail'

class Availability:
    Down = 'down'
    Up = 'up'

class RHQMetricsClient:
    """
    Creates new client for RHQ Metrics. If you intend to use the batching feature, remember to call
    flush() on certain intervals to avoid data being stale on the client side for too long.
    """

    """
    Availability data and numeric data can't be posted in the same call anymore..
    So they should be separated
    """
    
    #last_sent = None
    _batch = []
    
    def __init__(self,
                 tenant_id,
                 host='localhost',
                 port=8080,
                 batch_size=1):
        """
        A new instance of RHQMetricsClient is created with the following defaults:

        host = localhost
        port = 8080
        batch_size = 1 (avoid batching)

        The url that is called by default is:

        http://{host}:{port}/rhq-metrics/
        """
        self.tenant_id = tenant_id
        self.host = host
        self.port = port
        self.batch_size = batch_size

    """
    Internal methods
    """

    def _get_url(self, service):
        return "http://{0}:{1}/rhq-metrics/{2}/{3}".format(self.host, str(self.port), self.tenant_id, service)

    def _get_metrics_url(self, metric_type):
        return self._get_url('metrics') + "/{0}".format(metric_type)

    def _get_metrics_data_url(self, metric_type):
        return self._get_metrics_url(metric_type) + '/data'
    
    def _time_millis(self):
        return int(round(time.time() * 1000))

    def _post(self, url, json_data):
        print url
        
        try:
            req = urllib2.Request(url=url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            res = urllib2.urlopen(req)

            # Finally, close
            res.close()

        except urllib2.HTTPError, e:
            print "Error, RHQ Metrics responded with http code: " + str(e.code)

        except urllib2.URLError, e:
            print "Error, could not send event to RHQ Metrics: " + str(e.reason)

    def _get(self, url):
        try:
            req = urllib2.Request(url=url)
            req.add_header('Content-Type', 'application/json')
            res = urllib2.urlopen(req)        
            data = json.load(res)

            res.close()
            return data
        
        except urllib2.HTTPError, e:
            print "Error, RHQ Metrics responded with http code: " + str(e.code)

        except urllib2.URLError, e:
            print "Error, could not send event to RHQ Metrics: " + str(e.reason)

            
    """
    External methods
    """
    def put(self, metric_type, metric_id, data):
        """
        Send datapoint(s) to the server.

        data is a dict containing the keys: id, value, timestamp or a list
        of such dicts
        """
        if isinstance(data, list):
            batch = data
            # self._batch.extend(data)
        else:
            batch = []
            batch.append(data)
            # self._batch.append(data)

        # if len(self._batch) >= self.batch_size:
        #     self.flush()

        post_dict = [{ 'name': metric_id, 'data': batch }]        
        json_data = json.dumps(post_dict, indent=2)
        self._post(self._get_metrics_data_url(metric_type), json_data)
        """
        Allow setting maximum interval between flushes:
          - set up a timer task that does self._flush() after X seconds
            - recreate new one
          - If a batch size is met, reset that timer
        """

    def push(self, metric_id, value, timestamp=None):
        """
        Creates new datapoint and sends to the server. Value should be
        type of "Availability" or "up", "down" for availability metrics and otherwise
        a float type of for numerical values.
        """
        if timestamp is None:
            timestamp = self._time_millis()

        if self._isfloat(value):
            metric_type = MetricType.Numeric
        else:
            metric_type = MetricType.Availability
            
        # only str ("up", "down" and floats are allowed, rest should be converted)
        # if isinstance(value, Availability):
        #     value = str(value)
        # elif isinstance(value, int):
        #     value = float(value)
        # elif isinstance(value, long):
        #     value = float(value)
            
        item = { 'timestamp': timestamp,
                 'value': value
        }

        self.put(metric_type, metric_id, item)

    def flush(self):
        """
        Flushes the internal batch queue to the server, regardless if the size limit has
        been reached.

        Numerics and availability data.. uh
        """
        """
        if len(self._batch) > 0:
            json_data = json.dumps(self._batch, indent=2)
            self._post(self._get_metrics(MetricType.Numeric), json_data)
            self._batch = []
        """
        
    def query_metadata(self, query_type):
        """
        Query available metric metadata. Use 'avail' or 'num' or MetricType.Availability / MetricType.Numeric
        """
        if isinstance(query_type, MetricType):
            query_type = MetricType.short(query_type)
            
        metadata_url = self._get_url('metrics') + '?type=' + MetricType.short(query_type)
        return self._get(metadata_url)
    
    def _isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

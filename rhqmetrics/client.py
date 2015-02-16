import json
import urllib2
import urllib
import httplib
import time

"""
TODO: Remember to do imports for Python 3 also and check the compatibility..
"""

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

class RHQMetricsError(urllib2.HTTPError):
    pass

class RHQMetricsConnectionError(urllib2.URLError):
    pass
    
class RHQMetricsClient:
    """
    Creates new client for RHQ Metrics. If you intend to use the batching feature, remember to call
    flush() on certain intervals to avoid data being stale on the client side for too long.
    """

    """
    Availability data and numeric data can't be posted in the same call anymore..
    So they should be separated
    """
    
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

    def _get_base_url(self):
        return "http://{0}:{1}/rhq-metrics/".format(self.host, str(self.port))
    
    def _get_url(self, service):
        return self._get_base_url() + '{0}/{1}'.format(self.tenant_id, service)

    def _get_metrics_url(self, metric_type):
        return self._get_url('metrics') + "/{0}".format(metric_type)

    def _get_metrics_single_url(self, metric_type, metric_id):
        return self._get_metrics_url(metric_type) + '/{0}'.format(metric_id)
    
    def _get_metrics_data_url(self, metrics_url):
        return metrics_url + '/data'

    def _get_tenants_url(self):
        return self._get_base_url() + 'tenants'
    
    def _time_millis(self):
        return int(round(time.time() * 1000))

    def _post(self, url, json_data):
        try:
            req = urllib2.Request(url=url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            res = urllib2.urlopen(req)

            # Finally, close
            res.close()

        except urllib2.HTTPError, e:
            print "Error, RHQ Metrics responded with http code: " + str(e.code)
            raise RHQMetricsError(e)

        except urllib2.URLError, e:
            print"Error, could not send event(s) to the RHQ Metrics: " + str(e.reason)
            raise RHQMetricsConnectionError(e)

    def _get(self, url, **url_params):
        try:
            params = urllib.urlencode(url_params)
            if len(params) > 0:
                url = url + params

            req = urllib2.Request(url)                
            req.add_header('Content-Type', 'application/json')
            res = urllib2.urlopen(req)        
            data = json.load(res)

            res.close()
            return data
        
        except urllib2.HTTPError, e:
            print "Error, RHQ Metrics responded with http code: " + str(e.code)
            raise RHQMetricsError(e)

        except urllib2.URLError, e:
            print"Error, could not send event(s) to the RHQ Metrics: " + str(e.reason)
            raise RHQMetricsConnectionError(e)

    def _isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    """
    External methods
    """
    
    """
    Metrics related methods
    """

    def put(self, metric_type, metric_id, data):
        """
        Send datapoint(s) to the server.

        data is a dict containing the keys: value, timestamp or a list
        of such dicts
        """
        if isinstance(data, list):
            batch = data
            # self._batch.extend(data)
        else:
            batch = []
            batch.append(data)
            # self._batch.append(data)

        post_dict = [{ 'name': metric_id, 'data': batch }]        
        json_data = json.dumps(post_dict, indent=2)
        self._post(self._get_metrics_data_url(self._get_metrics_url(metric_type)), json_data)
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

        This method is assisting the put method by trying to detect what sort of
        metric type is sent, as well as generating a timestamp.
        """
        if self._isfloat(value):
            metric_type = MetricType.Numeric
        else:
            metric_type = MetricType.Availability

        item = self.create_metric_dict(value, timestamp)

        self.put(metric_type, metric_id, item)

    def create_metric_dict(self, value, timestamp=None):
        if timestamp is None:
            timestamp = self._time_millis()

        item = { 'timestamp': timestamp,
                 'value': value }

        return item
        
    def get(self, metric_type, metric_id, **search_options):
        """
        Supported search options are [optional]: start, end and buckets
        """
        return self._get(
            self._get_metrics_data_url(
                self._get_metrics_single_url(metric_type, metric_id)),
            **search_options)

    def query_single_numeric(self, metric_id, **search_options):
        return self.get(MetricType.Numeric, metric_id, **search_options)

    def query_single_availability(self, metric_id, **search_options):
        return self.get(MetricType.Availability, metric_id, **search_options)
    
    def query_metadata(self, query_type):
        """
        Query available metric metadata. Use 'avail' or 'num' or MetricType.Availability / MetricType.Numeric
        """
        if isinstance(query_type, MetricType):
            query_type = MetricType.short(query_type)
            
        metadata_url = self._get_url('metrics') + '?type=' + MetricType.short(query_type)
        return self._get(metadata_url)


    def create_metric_metadata(self, metric_id, metric_type, **kwargs):
        item = { 'name': metric_id }
        if len(kwargs) > 0:
            # We have some arguments to pass..
            data_retention = kwargs.pop('dataRetention')
            if data_retention is not None:
                item['dataRetention'] = data_retention

            metadata = {}
            for k, v in kwargs.items():
                metadata[k] = v

            if len(metadata) > 0:
                item['tags'] = metadata

        json_data = json.dumps(item, indent=2)
        self._post(self._get_metrics_url(metric_type), json_data)

    def create_numeric_metadata(self, metric_id, **options):
        self.create_metric_metadata(metric_id, MetricType.Numeric, **options)

    def create_availability_metadata(self, metric_id, **options):
        self.create_metric_metadata(metric_id, MetricType.Availability, **options)
        
    """
    Tenant related queries
    """
    
    def query_tenants(self):
        """
        Query available tenants and their information.
        """
        return self._get(self._get_tenants_url())

    def create_tenant(self, tenant_id, **retentions):
        """
        Create a tenant. Give parameters availability and numeric to provide custom
        retention times.
        """        
        avail_reten = retentions.get('availability')
        num_reten = retentions.get('numeric')

        item = { 'id': tenant_id }

        if avail_reten is not None and num_reten is not None:
            retens = { 'availability': avail_reten,
                       'numeric': num_reten }
            item['retentions'] = retens

        tenants_url = self._get_tenants_url()
        self._post(tenants_url, json.dumps(item, indent=2))
        

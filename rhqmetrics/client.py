import json
import urllib2
import urllib
import httplib
import time

"""
TODO: Remember to do imports for Python 3 also and check the compatibility..
TODO: Search datapoints with tags.. tag datapoints.
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

class HTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    """
    Hawkular-Metrics uses http codes 201, 204
    """
    def http_response(self, request, response):

        if response.code in [200, 201, 204]:
            return response
        return urllib2.HTTPErrorProcessor.http_response(self, request, response)
  
    https_response = http_response

class RHQMetricsClient:
    """
    Creates new client for RHQ Metrics. As tenant_id, give intended tenant_id, even if it's not
    created yet. Use one instance of RHQMetricsClient for each tenant.
    """
    def __init__(self,
                 tenant_id,
                 host='localhost',
                 port=8080):
        """
        A new instance of RHQMetricsClient is created with the following defaults:

        host = localhost
        port = 8080
        tenant_id = tenant_id

        The url that is called by default is:

        http://{host}:{port}/hawkular-metrics/
        """
        self.tenant_id = tenant_id
        self.host = host
        self.port = port

        opener = urllib2.build_opener(HTTPErrorProcessor())
        urllib2.install_opener(opener)

    """
    Internal methods
    """

    def _clean_metric_id(self, metric_id):
        return urllib.quote(metric_id, '')

    def _get_base_url(self):
        return "http://{0}:{1}/hawkular-metrics/".format(self.host, str(self.port))
    
    def _get_url(self, service):
        return self._get_base_url() + '{0}/{1}'.format(self.tenant_id, service)

    def _get_metrics_url(self, metric_type):
        return self._get_url('metrics') + "/{0}".format(metric_type)

    def _get_metrics_single_url(self, metric_type, metric_id):
        return self._get_metrics_url(metric_type) + '/{0}'.format(self._clean_metric_id(metric_id))
    
    def _get_metrics_data_url(self, metrics_url):
        return metrics_url + '/data'

    def _get_metrics_tags_url(self, metrics_url):
        return metrics_url + '/tags'

    def _get_tenants_url(self):
        return self._get_base_url() + 'tenants'
    
    def _time_millis(self):
        return int(round(time.time() * 1000))

    def _http(self, url, method, data=None):
        res = None

        try:
            req = urllib2.Request(url=url)
            req.add_header('Content-Type', 'application/json')

            if isinstance(data, dict):
                data = json.dumps(data, indent=2)

            if data:
                req.add_data(data)

            req.get_method = lambda: method    
            res = urllib2.urlopen(req)
            if method == 'GET':
                if res.getcode() == 200:
                    data = json.load(res)
                    # return data
                elif res.getcode() == 204:
                    data = {}

                return data

        except Exception as e:
            self._handle_error(e)

        finally:
            if res:
                res.close()        
    
    def _put(self, url, data):
        self._http(url, 'PUT', data)

    def _delete(self, url):
        self._http(url, 'DELETE')    
        
    def _post(self, url, data):
        self._http(url, 'POST', data)

    def _get(self, url, **url_params):
        params = urllib.urlencode(url_params)
        if len(params) > 0:
            url = url + params
            
        return self._http(url, 'GET')        
        
    def _handle_error(self, e):
        if isinstance(e, urllib2.HTTPError):
            # Cast to RHQMetricsError
            e.__class__ = RHQMetricsError
            err_json = e.read()

            try:
                err_d = json.loads(err_json)
                e.msg = err_d['errorMsg']
            except:
                # We keep the original payload, couldn't parse it
                e.msg = err_json

            raise e
        elif isinstance(e, urllib2.URLError):
            # Cast to RHQMetricsConnectionError
            e.__class__ = RHQMetricsConnectionError
            e.msg = "Error, could not send event(s) to the RHQ Metrics: " + str(e.reason)
            raise e
        else:
            raise e
        
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
    def create_metric_dict(self, value, timestamp=None, **tags):
        if timestamp is None:
            timestamp = self._time_millis()

        item = { 'timestamp': timestamp,
                 'value': value }

        if tags is not None:
            item['tags'] = tags

        return item

    def create_data_dict(self, metric_id, metric_dict):
        """
        Create RHQ Metrics' submittable structure, metric_dict is a
        dict created with create_metric_dict(value, timestamp)
        """
        if isinstance(metric_dict, list):
            batch = metric_dict
            # self._batch.extend(data)
        else:
            batch = []
            batch.append(metric_dict)
            # self._batch.append(data)

        return { 'id': metric_id, 'data': batch }

    def put_multi(self, metric_type, data):
        """
        Send multiple different metric_ids to the server in a single
        batch.

        data is a list of dicts created with create_data_dict(metric_id, metric_dict)
        """
        json_data = json.dumps(data, indent=2)
        self._post(self._get_metrics_data_url(self._get_metrics_url(metric_type)), json_data)

    def put(self, metric_type, metric_id, data):
        """
        Send single metric datapoint(s) to the server.

        data is a dict containing the keys: value, timestamp or a list
        of such dicts
        """
        post_dict = [self.create_data_dict(metric_id, data)]
        json_data = json.dumps(post_dict, indent=2)
        self._post(self._get_metrics_data_url(self._get_metrics_url(metric_type)), json_data)

    def push(self, metric_id, value, timestamp=None, **tags):
        """
        Creates new datapoint and sends to the server. Value should be
        type of "Availability" or "up", "down" for availability metrics and otherwise
        a float type of for numerical values.

        This method is an assistant method for the put method by trying to detect what sort of
        metric type is sent, as well as generating a timestamp if none is given.
        """
        if self._isfloat(value):
            metric_type = MetricType.Numeric
        else:
            metric_type = MetricType.Availability

        item = self.create_metric_dict(value, timestamp, **tags)

        self.put(metric_type, metric_id, item)

    def query_metric(self, metric_type, metric_id, **search_options):
        """
        Query for metrics from the server. 

        Supported search options are [optional]: start, end and buckets

        Use methods query_single_numeric and query_single_availability for simple access
        """
        return self._get(
            self._get_metrics_data_url(
                self._get_metrics_single_url(metric_type, metric_id)),
            **search_options)

    def query_single_numeric(self, metric_id, **search_options):
        """
        See query_metrics
        """
        return self.query_metric(MetricType.Numeric, metric_id, **search_options)

    def query_single_availability(self, metric_id, **search_options):
        """
        See query_metrics
        """
        return self.query_metric(MetricType.Availability, metric_id, **search_options)
    
    def query_definitions(self, query_type):
        """
        Query available metric definitions. Use 'avail' or 'num' or MetricType.Availability / MetricType.Numeric
        """
        if isinstance(query_type, MetricType):
            query_type = MetricType.short(query_type)
            
        definition_url = self._get_url('metrics') + '?type=' + MetricType.short(query_type)
        return self._get(definition_url)

    # def query_metric_definition(self, metric_type, metric_id):
    #     # This is actually using the tags method because of weird behavior in HWKMETRICS
    #     # TODO Fix this once Hawkular-Metrics is fixed.
    #     pass
    
    def create_metric_definition(self, metric_id, metric_type, **options):
        """
        Create metric definition with custom definition. **options should be a set of tags, such as
        units, env ..

        Use methods create_numeric_definition and create_availability_definition to avoid using
        MetricType.Numeric / MetricType.Availability
        """
        item = { 'id': metric_id }
        if len(options) > 0:
            # We have some arguments to pass..
            data_retention = options.pop('dataRetention',None)
            if data_retention is not None:
                item['dataRetention'] = data_retention

            tags = {}
            for k, v in options.items():
                tags[k] = v

            if len(tags) > 0:
                item['tags'] = tags

        json_data = json.dumps(item, indent=2)
        self._post(self._get_metrics_url(metric_type), json_data)

    def create_numeric_definition(self, metric_id, **options):
        """
        See create_metric_definition
        """
        self.create_metric_definition(metric_id, MetricType.Numeric, **options)

    def create_availability_definition(self, metric_id, **options):
        """
        See create_metric_definition
        """
        self.create_metric_definition(metric_id, MetricType.Availability, **options)
        
    def query_metric_tags(self, metric_type, metric_id):
        # Slightly overlapping with query_definition, as that would return tags also.. 
        # 200 ok, 204 ok, but nothing found
        # @Path("/{tenantId}/metrics/numeric/{id}/tags")
        definition = self._get(self._get_metrics_tags_url(self._get_metrics_single_url(metric_type, metric_id)))
        return definition.get('tags', {})

    def update_metric_tags(self, metric_type, metric_id, **tags):
        # This will replace all the tags with PUT
        self._put(self._get_metrics_tags_url(self._get_metrics_single_url(metric_type, metric_id)), tags)

    def delete_metric_tags(self, metric_type, metric_id, **deleted_tags):
        # 400 is tags are invalid
        tags = ','.join("%s:%s" % (key,val) for (key,val) in deleted_tags.iteritems())
        tags_url = self._get_metrics_tags_url(self._get_metrics_single_url(metric_type, metric_id)) + '/{0}'.format(tags)

        self._delete(tags_url)

    # def query_data_with_tags(self, metric_type, **tags):
    #     # 400 if invalid tags, 204 is nothing found
    #     pass

    # def change_datapoint_tags(self, metric_type, metric_id, timestamp=None, start=None, end=None, **tags):
    #     # TagRequest model.. mm?
    #     pass
    

    # def query_metric_definitions_with_tag(self, metric_type, **tags):
    #     # The description in Metrics REST-API is confusing, which one is datapoints and which one definions? Fix.
    #     pass
    
        
    """
    Tenant related queries
    """
    
    def query_tenants(self):
        """
        Query available tenants and their information.
        """
        return self._get(self._get_tenants_url())

    def create_tenant(self, tenant_id):
        """
        Create a tenant. Currently nothing can be set (to be fixed after the master
        version of Hawkular-Metrics has fixed implementation.
        """        
        item = { 'id': tenant_id }

        # if retention_time is not None:
        #     item['dataRetention'] = retention_time

        # if len(tags) > 0:
        #     item.extend(tags)

        tenants_url = self._get_tenants_url()
        self._post(tenants_url, json.dumps(item, indent=2))
        

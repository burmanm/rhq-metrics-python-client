import json
import urllib2
import httplib
import time

class RHQMetricsClient:
    """
    Creates new client for RHQ Metrics. If you intend to use the batching feature, remember to call
    flush() on certain intervals to avoid data being stale on the client side for too long.
    """

    #last_sent = None
    _batch = []
    
    def __init__(self, 
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
        self.host = host
        self.port = port
        self.batch_size = batch_size

    """
    Internal methods
    """

    def _get_url(self, service):
        return "http://{0}:{1}/rhq-metrics/{2}".format(self.host, str(self.port), service)

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

        except urllib2.URLError, e:
            print "Error, could not send event to RHQ Metrics: " + str(e.reason)

            
    """
    External methods
    """
    def put(self, data):
        """
        Send datapoint(s) to the server.

        data is a dict containing the keys: id, value, timestamp or a list
        of such dicts
        """
        if isinstance(data, list):
            self._batch.extend(data)
        else:
            self._batch.append(data)

        if len(self._batch) >= self.batch_size:
            self.flush()
        """
        Allow setting maximum interval between flushes:
          - set up a timer task that does self._flush() after X seconds
            - recreate new one
          - If a batch size is met, reset that timer
        """
        
    def create(self, id, value, timestamp=None):
        """
        Creates new datapoint and sends to the server.
        """
        if timestamp is None:
            timestamp = self._time_millis()

        item = { 'id': id,
                 'timestamp': timestamp,
                 'value': float(value)}

        self.put(item)

    def flush(self):
        """
        Flushes the internal batch queue to the server, regardless if the size limit has
        been reached.
        """
        if len(self._batch) > 0:
            json_data = json.dumps(self._batch, indent=2)
            self._post(self._get_url('metrics'), json_data)
            self._batch = []

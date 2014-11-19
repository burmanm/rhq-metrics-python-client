import json
import urllib2
import httplib
import time

"""
class IdDataPoint:

    def __init__(self, id, timestamp, value):
        self.id = id # string
        self.timestamp = timestamp # long
        self.value = value # double

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)
"""

class RHQMetricsClient:

    def __init__(self, 
                 host='localhost',
                 port=8080):
        self.host = host
        self.port = port

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

        except HTTPError, e:
            print "Response Code was: " + e.code

        except URLError, e:
            print "Error was: " + e.reason

    """
    External methods
    """

    def put_batch(self, datapoints):        
        url = self._get_url('metrics')
        data = json.dumps(datapoints, indent=2)

        """
        print url
        print json.dumps(datapoints, indent=2)
        """

        self._post(url, data)

    def put(self, id, value, timestamp=None):

        if timestamp is None:
            timestamp = self._time_millis()

        item = { 'id': id,
                 'timestamp': timestamp,
                 'value': value}

        ls = []
        ls.append(item)

        self.put_batch(ls)

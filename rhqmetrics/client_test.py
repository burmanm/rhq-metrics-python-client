import unittest
#import client
from client import *
#from client import RHQMetricsClient

class TestMetricFunctionsBase(unittest.TestCase):

    def setUp(self):
        self.client = RHQMetricsClient(tenant_id=1)


class TenantTestCase(TestMetricFunctionsBase):

    # def runTest(self):
        # Create tenant
        # Fetch tenants and check that the new created one is there..
        # pass

    def test_tenant_creation(self):
        # Create tenant
        # Check that tenant was created with correct values
        pass    

class MetricsTestCase(TestMetricFunctionsBase):

    # def runTest(self):
    #     # Create numeric metrics
    #     # Read numeric metrics
    #     # Create availability metric
    #     # Read availability metric
    #     #self.test_numeric()
    #     self.test_availability()
    #     pass

    def test_numeric(self):
        self.client.push('test.numeric', float(4.35))
        # Assert that query_metadata returns info about num id = 1
        # meta = self.client.query_metadata(MetricType.Numeric)
        # Assert that value is 4.35
        pass

    def test_availability(self):
        self.client.push('test.avail.1', Availability.Up)
        self.client.push('test.avail.2', 'down')
        meta = self.client.query_metadata(MetricType.Availability)
        # Assert that we have two of them, and one is availability and one is numeric
        # with correct names..
        pass        

    def test_multi(self):
        # Insert multiple availability & numeric in the same call
        # Test fetching of the data
        pass

    def test_tenant(self):
        self.client.create_tenant('2')
        self.client.create_tenant('3', availability='40', numeric='50')
        
if __name__ == '__main__':
    unittest.main()

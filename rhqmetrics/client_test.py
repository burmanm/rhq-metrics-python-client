import unittest
import uuid
from client import *

class TestMetricFunctionsBase(unittest.TestCase):

    def setUp(self):
        self.test_tenant = str(uuid.uuid4())
        self.client = RHQMetricsClient(tenant_id=self.test_tenant)
        
class TenantTestCase(TestMetricFunctionsBase):
    """
    Test creating and fetching tenants. Each creation test should also
    fetch the tenants to test that functionality also
    """
    
    def test_tenant_creation(self):
        tenant = str(uuid.uuid4())
        self.client.create_tenant(tenant)
        tenants = self.client.query_tenants()
        for item in tenants:
            if item['id'] == tenant:
                return
            
        self.fail('Created tenant could not be found')

    def test_tenant_creation_with_retentions(self):
        tenant = str(uuid.uuid4())
        self.client.create_tenant(tenant, availability='40', numeric='50')
        tenants = self.client.query_tenants()
        for item in tenants:
            if item['id'] == tenant:
                self.assertEquals(item['retentions']['availability'], 40)
                self.assertEquals(item['retentions']['numeric'], 50)
                return

        self.fail('Created tenant could not be found')
        
class MetricsTestCase(TestMetricFunctionsBase):
    """
    Test metric functionality, both adding metadata and querying for metadata, 
    as well as adding new numeric and availability metrics. 

    Metric metadata creation should also test fetching the metadata, while
    metric inserts should test also fetching the metric data.
    """
    
    def test_numeric_creation(self):
        # Create numeric metric
        # Fetch metrics and check that it did appear
        # Test with empty details and added details
        self.fail("Not implemented")

    def test_availability_creation(self):
        # Create availability metric
        # Fetch mterics and check that it did appear
        self.fail("Not implemented")

    def test_update_metric(self):
        # Create metric
        # Update metric
        # Fetch metric
        # Test that metric is updated value
        self.fail('Not implemented')
        
    def test_add_numeric_single(self):
        metric = float(4.35)
        self.client.push('test.numeric', metric)
        data = self.client.query_single_numeric('test.numeric')
        self.assertEquals(float(data['data'][0]['value']), metric)

    def test_add_availability_single(self):
        self.client.push('test.avail.1', Availability.Up)
        self.client.push('test.avail.2', 'down')

        up = self.client.query_single_availability('test.avail.1')
        self.assertEquals(up['data'][0]['value'], 'up')
        
        down = self.client.query_single_availability('test.avail.2')
        self.assertEquals(down['data'][0]['value'], 'down')

    def test_add_numeric_multi(self):
        self.fail('Not implemented')

    def test_add_availability_multi(self):
        self.fail('Not implemented')
        
if __name__ == '__main__':
    unittest.main()

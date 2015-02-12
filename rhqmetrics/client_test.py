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

        expect = { 'id': tenant, 'retentions': {} }
        self.assertIn(expect, tenants)
        
    def test_tenant_creation_with_retentions(self):
        tenant = str(uuid.uuid4())
        self.client.create_tenant(tenant, availability='40', numeric='50')
        tenants = self.client.query_tenants()

        expect = { 'id': tenant, 'retentions': { 'availability': 40, 'numeric': 50 } }
        self.assertIn(expect, tenants)
        
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
        self.assertEqual(float(data['data'][0]['value']), metric)

    def test_add_availability_single(self):
        self.client.push('test.avail.1', Availability.Up)
        self.client.push('test.avail.2', 'down')

        up = self.client.query_single_availability('test.avail.1')
        self.assertEqual(up['data'][0]['value'], 'up')
        
        down = self.client.query_single_availability('test.avail.2')
        self.assertEqual(down['data'][0]['value'], 'down')

    def test_add_numeric_multi(self):
        metric1 = self.client.create_metric(float(1.45))
        metric2 = self.client.create_metric(float(2.00), '1423734467561')

        batch = []
        batch.append(metric1)
        batch.append(metric2)

        self.client.put(MetricType.Numeric, 'test.numeric.multi', batch)
        data = self.client.query_single_numeric('test.numeric.multi')

        datad = data['data']
        self.assertEqual(len(datad), 2)
        self.assertEqual(datad[0]['value'], float(1.45))
        self.assertEqual(datad[1]['value'], float(2.00))

    def test_add_availability_multi(self):
        up = self.client.create_metric('up', '1423734467561')
        down = self.client.create_metric('down')

        batch = []
        batch.append(up)
        batch.append(down)

        self.client.put(MetricType.Availability, 'test.avail.multi', batch)
        data = self.client.query_single_availability('test.avail.multi')

        datad = data['data']
        self.assertEqual(len(datad), 2)
        self.assertEqual(datad[0]['value'], 'down')
        self.assertEqual(datad[1]['value'], 'up')
        
if __name__ == '__main__':
    unittest.main()

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
        self.client.create_numeric_metadata('test.create.numeric.1')
        self.client.create_numeric_metadata('test.create.numeric.2', dataRetention=90)
        self.client.create_numeric_metadata('test.create.numeric.3', dataRetention=90, units='bytes', env='qa')
        # Fetch metrics and check that it did appear
        m = self.client.query_metadata(MetricType.Numeric)
        self.assertEqual(3, len(m))
        self.assertEqual('bytes', m[2]['tags']['units'])
        # Test with empty details and added details

    def test_availability_creation(self):
        # Create availability metric
        # Fetch mterics and check that it did appear
        self.client.create_availability_metadata('test.create.avail.1')
        self.client.create_availability_metadata('test.create.avail.2', dataRetention=90)
        self.client.create_availability_metadata('test.create.avail.3', dataRetention=94, env='qa')
        # Fetch metrics and check that it did appear
        m = self.client.query_metadata(MetricType.Availability)        
        self.assertEqual(3, len(m))
        self.assertEqual(94, m[2]['dataRetention'])

    # def test_update_metric(self):
    #     # Update previously created metric (from tests above)
    #     # Fetch metrics
    #     # Test that metric has an updated value
    #     self.fail('Not implemented')
        
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
        metric1 = self.client._create_metric_dict(float(1.45))
        metric2 = self.client._create_metric_dict(float(2.00), (self.client._time_millis() - 2000))

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
        up = self.client._create_metric_dict('up', (self.client._time_millis() - 2000))
        down = self.client._create_metric_dict('down')

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

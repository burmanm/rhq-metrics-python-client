import unittest
import uuid
from client import *

class TestMetricFunctionsBase(unittest.TestCase):

    def setUp(self):
        self.test_tenant = str(uuid.uuid4())
        self.client = RHQMetricsClient(tenant_id=self.test_tenant, port=8081)
        
class TenantTestCase(TestMetricFunctionsBase):
    """
    Test creating and fetching tenants. Each creation test should also
    fetch the tenants to test that functionality also
    """
    
    def test_tenant_creation(self):
        tenant = str(uuid.uuid4())
        self.client.create_tenant(tenant)
        tenants = self.client.query_tenants()

        expect = { 'id': tenant }
        self.assertIn(expect, tenants)

    def test_tenant_creation_with_retentions_and_aggregations(self):
        # This feature isn't finished in the current master version of Hawkular-Metrics
        pass
        # tenant = str(uuid.uuid4())
        # self.client.create_tenant(tenant, 40)
        # tenants = self.client.query_tenants()

        # expect = { 'id': tenant, 'dataRetention': 40 }
        # self.assertIn(expect, tenants)
        
class MetricsTestCase(TestMetricFunctionsBase):
    """
    Test metric functionality, both adding definition and querying for definition, 
    as well as adding new numeric and availability metrics. 

    Metric definition creation should also test fetching the definition, while
    metric inserts should test also fetching the metric data.
    """
    
    def test_numeric_creation(self):
        """
        Test creating numeric metric definitions with different tags and definition.
        """
        # Create numeric metrics with empty details and added details
        self.client.create_numeric_definition('test.create.numeric.1')
        self.client.create_numeric_definition('test.create.numeric.2', dataRetention=90)
        self.client.create_numeric_definition('test.create.numeric.3', dataRetention=90, units='bytes', env='qa')

        # Fetch metrics definition and check that the ones we created appeared also
        m = self.client.query_definitions(MetricType.Numeric)
        self.assertEqual(3, len(m))
        self.assertEqual(self.test_tenant, m[0]['tenantId'])
        self.assertEqual('bytes', m[2]['tags']['units'])

        # This is what the returned dict should look like
        expect = [
            {'id': 'test.create.numeric.1',
             'tenantId': self.test_tenant },
            {'dataRetention': 90, 'id': 'test.create.numeric.2', 'tenantId': self.test_tenant},
            {'tags': {'units': 'bytes', 'env': 'qa'},
             'id': 'test.create.numeric.3', 'dataRetention': 90, 'tenantId': self.test_tenant}]

        self.assertEqual(m, expect) # Did it?

        # Lets try creating a duplicate metric
        try:
            self.client.create_numeric_definition('test.create.numeric.1')
            self.fail('Should have received an exception, metric with the same name was already created')
        except RHQMetricsError, e:
            # Check return code 400 and that the failure message was correctly parsed
            self.assertEqual(409, e.code)
            self.assertEqual('A metric with name [test.create.numeric.1] already exists', e.msg)

    def test_availability_creation(self):
        # Create availability metric
        # Fetch mterics and check that it did appear
        self.client.create_availability_definition('test.create.avail.1')
        self.client.create_availability_definition('test.create.avail.2', dataRetention=90)
        self.client.create_availability_definition('test.create.avail.3', dataRetention=94, env='qa')
        # Fetch metrics and check that it did appear
        m = self.client.query_definitions(MetricType.Availability)        
        self.assertEqual(3, len(m))
        self.assertEqual(94, m[2]['dataRetention'])

    def test_tags_modifications(self):
        m = 'test.create.tags.1'
        # Create metric without tags
        self.client.create_numeric_definition(m)
        e = self.client.query_metric_tags(MetricType.Numeric, m)
        self.assertEqual({}, e) # Should not be None

        # Add tags
        self.client.update_metric_tags(MetricType.Numeric, m, hostname='machine1', a='b')
        # Fetch metric - check for tags
        tags = self.client.query_metric_tags(MetricType.Numeric, m)
        self.assertEqual(2, len(tags))
        self.assertEqual("b", tags['a'])
        # Delete some metric tags
        self.client.delete_metric_tags(MetricType.Numeric, m, a='b', hostname='machine1')
        # Fetch metric - check that tags were deleted
        tags_2 = self.client.query_metric_tags(MetricType.Numeric, m)
        self.assertEqual(0, len(tags_2))

    def test_tags_finding(self):
        pass
        # Create metrics with tags
        # Push some data to them
        # Fetch data with certain tags
        
    # def test_update_metric(self):
    #     # Update previously created metric (from tests above)
    #     # Fetch metrics
    #     # Test that metric has an updated value
    #     self.fail('Not implemented')

    # def test_delete_metric(self):

    # def test_tags_behavior(self):
    #     print 'START: TEST TAGS'
    #     metric = float(1.2345)
    #     print 'CREATE'
    #     self.client.create_numeric_definition('test.numeric.single.tags.1', hostname='')
    #     print 'POST'
    #     self.client.push('test.numeric.single.tags.1', metric, hostname='localhost')
    #     print 'GET'
    #     data = self.client.query_single_numeric('test.numeric.single.tags.1')
    #     print data
    #     print 'END: TEST TAGS'
    
    def test_add_numeric_single(self):
        metric = float(4.35)
        self.client.push('test.numeric./', metric)
        data = self.client.query_single_numeric('test.numeric./')
        self.assertEqual(float(data[0]['value']), metric)

        self.client.push('test.numeric.single.tags', metric, hostname='localhost')
        data = self.client.query_single_numeric('test.numeric.single.tags')
        # self.assertEqual(data[0]['tags']['localhost'], 'localhost')

    def test_add_availability_single(self):
        self.client.push('test.avail.1', Availability.Up)
        self.client.push('test.avail.2', 'down')

        up = self.client.query_single_availability('test.avail.1')
        self.assertEqual(up[0]['value'], 'up')
        
        down = self.client.query_single_availability('test.avail.2')
        self.assertEqual(down[0]['value'], 'down')

    def test_add_numeric_multi(self):
        metric1 = self.client.create_metric_dict(float(1.45))
        metric2 = self.client.create_metric_dict(float(2.00), (self.client._time_millis() - 2000))

        batch = []
        batch.append(metric1)
        batch.append(metric2)

        self.client.put(MetricType.Numeric, 'test.numeric.multi', batch)
        data = self.client.query_single_numeric('test.numeric.multi')

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], float(1.45))
        self.assertEqual(data[1]['value'], float(2.00))

    def test_add_availability_multi(self):
        up = self.client.create_metric_dict('up', (self.client._time_millis() - 2000))
        down = self.client.create_metric_dict('down')

        batch = []
        batch.append(up)
        batch.append(down)

        self.client.put(MetricType.Availability, 'test.avail.multi', batch)
        data = self.client.query_single_availability('test.avail.multi')

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], 'down')
        self.assertEqual(data[1]['value'], 'up')

    def test_add_multi(self):
        metric1 = self.client.create_metric_dict(float(1.45))
        metric1_2 = self.client.create_metric_dict(float(2.00), (self.client._time_millis() - 2000))

        metric_multi = self.client.create_data_dict('test.multi.numeric.1', [metric1, metric1_2])

        metric2 = self.client.create_metric_dict(float(1.55))
        metric2_multi = self.client.create_data_dict('test.multi.numeric.2', [metric2])

        self.client.put_multi(MetricType.Numeric, [metric_multi, metric2_multi])

        # Check that both were added correctly..
        metric1_data = self.client.query_single_numeric('test.multi.numeric.1')
        metric2_data = self.client.query_single_numeric('test.multi.numeric.2')

        self.assertEqual(2, len(metric1_data))
        self.assertEqual(1, len(metric2_data))

if __name__ == '__main__':
    unittest.main()

rhq-metrics-python-client
=========================

## Introduction

Python client to access Hawkular Metrics, an abstraction to invoke REST-methods on the server endpoint using urllib2. No external dependencies, works with Python 2.7 for now.

## Installation

To install, run ``python setup.py install``

## Usage

To use rhq-metrics-python-client in your own program, after installation import from rhqmetrics the class RHQMetricsClient and instantiate it. It accepts parameters hostname, port and batch_size (optional). After this, push dicts with keys id, timestamp and value with put or use assistant method create to send events.

Timestamps should be in the milliseconds after epoch (created by the create() method automatically if not supplied) and value should be a float.

Example to push and fetch data numeric metric:

```
>>> from rhqmetrics import *
>>> client = RHQMetricsClient(tenant_id='test')
>>> client.push('test.metric.1', 1.00)
>>> m = client.query_single_numeric('test.metric.1')
>>> print m['data'][0]['value']
1.0
>>>
```

See client_test.py for more detailed examples.

## Method documentation

Method documentation is available with ``pydoc rhqmetrics``

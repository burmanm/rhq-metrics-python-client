rhq-metrics-python-client
=========================

## Introduction

Python client to access RHQ Metrics, an abstraction to invoke REST-methods on the server endpoint using urllib2.

## Installation

To install, run ``python setup.py install``

## Usage

To use rhq-metrics-python-client in your own program, after installation import from rhqmetrics the class RHQMetricsClient and instantiate it. It accepts parameters hostname, port and batch_size (optional). After this, push dicts with keys id, timestamp and value with put or use assistant method create to send events.

Timestamps should be in the milliseconds after epoch (created by the create() method automatically if not supplied) and value should be a float.

Example:

```python
import rhqmetrics import RHQMetricsClient

def send_to_server(self):
  r = rhqmetrics.RHQMetricsClient('localhost', '8080')
  r.create(id, value)
```

Larger example is available on example.py

If you set batch_size to anything higher than 1, the client will not send events to the server until there's enough data to be sent. To force sending remaining items to the server, use flush(). To avoid having stale data for a long period, consider using a timer task to call flush() on certain intervals, as calling flush() will not do anything if there's no data to be sent.

Note: current version if not thread safe, so calling put() and flush() at the same time from different threads is not safe.

## Method documentation

Method documentatino is available with ``pydoc rhqmetrics``

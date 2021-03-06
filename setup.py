#!/usr/bin/env python

from distutils.core import setup

setup(name='rhq-metrics-python-client',
      version='0.3.1',
      description='Python client to communicate with Hawkular Metrics over HTTP',
      author='Michael Burman',
      author_email='miburman@redhat.com',
      url='http://github.com/burmanm/rhq-metrics-python-client',
      packages=['rhqmetrics']
      )

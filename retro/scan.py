# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position

"""
Generic function `scan` for performing an N-dimensional parameter scan of some
metric.
"""

from __future__ import absolute_import, division, print_function

__author__ = 'J.L. Lanfranchi'
__license__ = '''Copyright 2017 Justin L. Lanfranchi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.'''

__all__ = ['scan']

from collections import Sequence
from itertools import product
from os.path import abspath, dirname
import sys
import time

import numpy as np

if __name__ == '__main__' and __package__ is None:
    RETRO_DIR = dirname(dirname(abspath(__file__)))
    if RETRO_DIR not in sys.path:
        sys.path.append(RETRO_DIR)
from retro import FTYPE


def scan(hypo_params, scan_values, metric, metric_kw=None):
    """Scan a metric (e.g., neg_llh) for hypotheses with a set of parameter
    values.

    Note that `metric` is called via::

        metric(hypo_params, **metric_kw)

    and the actual values used as `hypo_params` are the _outer_ product of the
    values specified in `scan_values`.

    Parameters
    ----------
    scan_values : dict of floats or iterables
        Values used in the scan are the _outer_ product of the items in
        `scan_values`. Specify a single value for a dimension to disable
        scanning in that dimension.

    metric : callable
        Function used to compute e.g. a likelihood. Must take ``sources`` and
        ``event`` as first two arguments, where ``sources`` is (...) and
        ``event`` is the argument passed here. Function must return just one
        value (e.g., ``-llh``)

    metric_kw : mapping, optional
        Keyword arguments to pass to `get_neg_llh` function

    Returns
    -------
    metric_vals : shape (len(scan_values[0]), len(scan_values[1]), ...) array of FTYPE
        Metric values corresponding to each combination of scan values, i.e.,
        ``product(*scan_values)``.

    """
    if metric_kw is None:
        metric_kw = {}


    # Need iterable-of-iterables-of-floats. If we have just an iterable of
    # floats (e.g. for 1D scan), then make it the first element of a
    # single-element tuple.
    if np.isscalar(next(iter(scan_values))):
        scan_values = (scan_values,)

    scan_sequences = []
    shape = []
    for sv in scan_values:
        if not isinstance(sv, Sequence):
            if np.isscalar(sv):
                sv = [sv]
            else:
                sv = list(sv)
        scan_sequences.append(sv)
        shape.append(len(sv))

    total_points = np.product(shape)

    times = [time.time()]
    metric_vals = []
    report_after = 500
    for n, param_values in enumerate(product(*scan_sequences)):
        metric_val = metric(dict(zip(hypo_params, param_values)), **metric_kw)
        metric_vals.append(metric_val)
        if n > 0 and n % report_after == 0:
            times.append(time.time())
            avg = np.mean(np.diff(times[-3:])) / report_after
            remaining = avg * (total_points - n - 1)
            print('Elapsed: {} s, avg: {:.3f} ms/pt; remaining ~ {} s'
                  .format(int(np.round(times[-1] - times[0])),
                          avg * 1000,
                          int(np.round(remaining))))
            sys.stdout.flush()
    metric_vals = np.array(metric_vals, dtype=FTYPE).reshape(shape)

    return metric_vals

"""consensus-hunter tests — synthetic, deterministic.

All tests use pure-stdlib randomness with fixed seeds so output is
byte-identical across runs. The tests are also the executable
documentation: read them to understand the invariants."""

import sys
import os
import unittest

# Ensure tests/ can import lib/ without packaging machinery.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from lib import aggregate, calibrate, schema  # noqa: E402


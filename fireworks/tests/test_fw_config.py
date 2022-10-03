__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Shyue Ping Ong"
__email__ = "ongsp@ucsd.edu"
__date__ = "2/3/14"

import unittest

from fireworks.fw_config import config_to_dict


class ConfigTest(unittest.TestCase):
    def test_config(self):
        d = config_to_dict()
        self.assertNotIn("NEGATIVE_FWID_CTR", d)


if __name__ == "__main__":
    unittest.main()

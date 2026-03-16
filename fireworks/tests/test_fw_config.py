__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Shyue Ping Ong"
__email__ = "ongsp@ucsd.edu"
__date__ = "2/3/14"

import os
import unittest
from tempfile import mkdtemp

import pytest

from fireworks.fw_config import config_to_dict, override_user_settings
from fireworks.utilities.exceptions import FWConfigurationError


class ConfigTest(unittest.TestCase):
    def test_config(self) -> None:
        d = config_to_dict()
        assert "NEGATIVE_FWID_CTR" not in d


class FWConfigTest(unittest.TestCase):
    """Tests for the fw_config module."""

    def setUp(self):
        self.init_dir = os.getcwd()
        self.fw_config_dir = mkdtemp()
        os.chdir(self.fw_config_dir)
        self.fw_config = os.path.join(self.fw_config_dir, "FW_config.yaml")
        with open(self.fw_config, "w", encoding="utf-8"):
            pass

    def tearDown(self):
        os.chdir(self.init_dir)
        os.unlink(self.fw_config)
        os.rmdir(self.fw_config_dir)

    def test_override_user_settings_empty_yaml(self) -> None:
        """Test with empty fw_config file."""
        msg = "Invalid FW_config file, type must be dict but is <class 'NoneType'>"
        with pytest.raises(FWConfigurationError, match=msg):
            override_user_settings()

    def test_override_user_settings_invalid_key(self) -> None:
        """Test fw_config file with invalid key."""
        with open(self.fw_config, "a", encoding="utf-8") as fh:
            fh.write("blah: true")
        msg = "Invalid FW_config file has unknown parameter: blah"
        with pytest.raises(FWConfigurationError, match=msg):
            override_user_settings()

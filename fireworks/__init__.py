import os

__version__ = '0.88'
FW_INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# These imports allow a much simpler import of core Fireworks functionality.
# E.g., you can now do "from fireworks import FireWork", instead of from
# "fireworks.core.firework import FireWork".
from fireworks.core.firework import FireTaskBase, FireWork, Launch, Workflow,\
    FWAction
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.utilities.fw_utilities import explicit_serialize
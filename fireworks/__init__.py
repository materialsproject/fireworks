import os

__version__ = "1.9.8"
FW_INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ndarray size changed")

# These imports allow a much simpler import of core Fireworks functionality.
# E.g., you can now do "from fireworks import Firework", instead of from
# "fireworks.core.firework import Firework".
from fireworks.core.firework import (
    FiretaskBase,
    FireTaskBase,
    Firework,
    FWAction,
    Launch,
    Tracker,
    Workflow,
)
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.user_objects.firetasks.fileio_tasks import (
    ArchiveDirTask,
    CompressDirTask,
    FileDeleteTask,
    FileTransferTask,
    FileWriteTask,
)
from fireworks.user_objects.firetasks.script_task import PyTask, ScriptTask
from fireworks.user_objects.firetasks.templatewriter_task import (
    TemplateWriterTask,
)
from fireworks.utilities.fw_utilities import explicit_serialize

import os

__version__ = '1.7.6'
FW_INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# These imports allow a much simpler import of core Fireworks functionality.
# E.g., you can now do "from fireworks import Firework", instead of from
# "fireworks.core.firework import Firework".
from fireworks.core.firework import FiretaskBase, FireTaskBase, Firework, Launch, Workflow, \
    FWAction, Tracker
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.utilities.fw_utilities import explicit_serialize
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask
from fireworks.user_objects.firetasks.fileio_tasks import FileDeleteTask, FileTransferTask, \
    FileWriteTask, ArchiveDirTask, CompressDirTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask

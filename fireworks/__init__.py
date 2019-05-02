import os

__version__ = '1.8.7'
FW_INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# These imports allow a much simpler import of core Fireworks functionality.
# E.g., you can now do "from fireworks import Firework", instead of from
# "fireworks.core.firework import Firework".
from fireworks.core.firework import Firework, Tracker,\
								Firetask, FWAction, FiretaskBase, FireTaskBase,\
								Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import WFLock, LaunchPad
from fireworks.utilities.fw_utilities import explicit_serialize
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask
from fireworks.user_objects.firetasks.fileio_tasks import FileDeleteTask, FileTransferTask, \
    FileWriteTask, ArchiveDirTask, CompressDirTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask

import fireworks.fw_config

if fireworks.fw_config.DEFAULT_DATABASE_TYPE == "mongodb":
    from fireworks.core.mongo_launchpad import MongoLaunchPad as LaunchPad
else:
    pass

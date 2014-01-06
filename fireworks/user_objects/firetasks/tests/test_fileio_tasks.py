__author__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = '1/6/14'

import unittest
import os

from fireworks.user_objects.firetasks.fileio_tasks import FileWriterTask
from fireworks.utilities.fw_serializers import load_object_from_file


module_dir = os.path.abspath(os.path.dirname(__file__))


class FileWriterTest(unittest.TestCase):

    def test_run(self):
        t = load_object_from_file(os.path.join(module_dir, "writer.yaml"))
        t.run_task(t)
        for i in xrange(2):
            self.assertTrue(os.path.exists("myfile{}".format(i + 1)))
            os.remove("myfile{}".format(i + 1))

if __name__ == '__main__':
    unittest.main()

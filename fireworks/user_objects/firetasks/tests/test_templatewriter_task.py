# coding: utf-8

from __future__ import unicode_literals, division

"""
TODO: Modify unittest doc.
"""


__author__ = "Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Bharat Medasani"
__email__ = "mbkumar@gmail.com"
__date__ = "8/7/14"

import unittest
import os

from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask

class TemplateWriterTaskTest(unittest.TestCase):

    def test_task(self):
        with open('test_template.txt','w') as fp:
            fp.write("option1 = {{opt1}}\noption2 = {{opt2}}")
        t = TemplateWriterTask({
            'context':{'opt1':5.0,'opt2':'fast method'},
            'template_file':'test_template.txt',
            'output_file':'out_template.txt',
            'template_dir':'.'})
        t.run_task({})
        self.assertTrue(os.path.exists('out_template.txt'))
        with open('out_template.txt') as fp:
            for line in fp:
                if "option1" in line:
                    self.assertTrue("5.0" in line)
                if "option2" in line:
                    self.assertTrue("fast method" in line)
        os.remove('out_template.txt')
        if os.path.exists('test_template.txt'):
            os.remove('test_template.txt')


if __name__ == '__main__':
    unittest.main()

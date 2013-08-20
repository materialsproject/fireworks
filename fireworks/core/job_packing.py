__author__ = 'xiaohuiqu'

from multiprocessing.managers import BaseManager

class PackingManager(BaseManager):
    pass

PackingManager.register('LaunchPad')


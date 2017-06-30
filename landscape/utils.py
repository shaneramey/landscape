# -*- coding: utf-8 -*-
"""Various helper utilities"""

import subprocess

def namespace_exists(namespace):
    if subprocess.call(['kubectl', 'get', 'ns', namespace], shell=True):
        return True
    else:
        return False

#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
import os
import time
from distutils.version import LooseVersion
import epdb

HAS_DO = True
try:
    import digitalocean
    if LooseVersion(digitalocean.__version__) < LooseVersion('1.8'):
        HAS_DO = False
except ImportError:
    HAS_DO = False

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['droplet'], default='droplet'),
            state = dict(choices=['present', 'deleted'], default='present'),
            api_token = dict(no_log=True),
            name = dict(type='str'),
            region_id = dict(type='str'),
            image_id = dict(type='str'),
            size_id = dict(type='str'),
        ),
    )
    if not HAS_DO:
        module.fail_json(msg='python-digitalocean >= 1.8 required for this module')

    try:
        core(module)
    except:
        module.fail_json(msg=str(sys.exc_info()[0]))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
#    epdb.serve()
    main()
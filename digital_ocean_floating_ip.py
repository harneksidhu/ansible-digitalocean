#!/usr/bin/python
# -*- coding: utf-8 -*-
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


def core(module):
    def getkeyordie(k):
        v = module.params[k]
        if v is None:
            module.fail_json(msg='Unable to load %s' % k)
        return v

    try:
        api_token = module.params['api_token'] or os.environ['DO_API_TOKEN'] or os.environ['DO_API_KEY']
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    changed = True
    command = module.params['command']
    state = module.params['state']

    if command == 'assign':
        if state in ('present'):


        elif state in ('absent'):

    elif command == 'reserve':
        if state in ('present'):

        elif state in ('absent'):


def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['assign', 'reserve']),
            state = dict(choices=['present', 'absent'], default='present'),
            api_token = dict(aliases=['API_TOKEN'], no_log=True),
            name = dict(type='str'),
            id = dict(aliases=['droplet_id'], type='int'),
            region_id = dict(type='str'),
            ip = dict(type='str'),
            required_one_of = (
                ['id', 'name'],
            ),
        ),
    )
    if not HAS_DO:
        module.fail_json(msg='python-digitalocean >= 1.8 required for this module')

    try:
#        epdb.serve()
        # droplet = digitalocean.FloatingIP(token=module.params['api_token'],
        #                        region_slug=module.params['region_id'])
        # droplet.create()
        # module.exit_json(changed=True)
        core(module)
    except Exception, e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
#    epdb.serve()
    main()
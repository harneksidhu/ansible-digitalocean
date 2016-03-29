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


class DOManager(object):
    manager = None

    @classmethod
    def setup(cls, api_token):
        cls.manager = digitalocean.Manager(token=api_token)

    def reserve():
        return self.manager.get_floating_ip(ip)


def core(module):
    def getkeyordie(k):
        v = module.params[k]
        if v is None:
            module.fail_json(msg='Unable to load %s' % k)
        return v

    def getDropletFromIP(droplet_ip, api_token):
        manager = digitalocean.Manager(token=api_token)
        droplets = manager.get_all_droplets()
        for droplet in droplets:
            if droplet.ip_address == droplet_ip:
                return droplet
        module.fail_json(msg='Unable to find droplet with ip %s' % droplet_ip)

    def getDropletFromID(droplet_id, api_token):
        manager = digitalocean.Manager(token=api_token)
        manager.get_droplet(droplet_id=droplet_id)

    try:
        api_token = module.params['api_token'] or os.environ['DO_API_TOKEN'] or os.environ['DO_API_KEY']
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    command = module.params['command']
    state = module.params['state']

    if command == 'assign':
        if state in ('present'):
            droplet_ip = module.params['droplet_ip']
            droplet_id = module.params['droplet_id']

            droplet = None
            if droplet_ip != None:
                droplet = getDropletFromIP(droplet_ip, api_token)
            elif droplet_id != None:
                droplet = getDropletFromID(droplet_id, api_token)
            else:
                module.fail_json(msg='droplet_ip or droplet_id is required')



        elif state in ('absent'):
            floatingIP = digitalocean.FloatingIP(
                            token=api_token,
                            ip=getkeyordie('region_id'),
                         )
            floatingIP.unassign()

    elif command == 'reserve':
        if state in ('present'):
            floatingIP = digitalocean.FloatingIP(
                            token=api_token,
                            region_slug=getkeyordie('region_id'),
                         )
            data = floatingIP.reserve()
            module.exit_json(changed=True, floating_ip=data.ip)

        elif state in ('absent'):
            ip = getkeyordie('ip')
            manager=digitalocean.Manager(token=api_token)
            floating_ips = manager.get_all_floating_ips()
            for floating_ip in floating_ips:
                if ip == floating_ip.ip:
                    floating_ip.destroy()
                    module.exit_json(changed=True)
            module.exit_json(changed=False)
    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['assign', 'reserve']),
            state = dict(choices=['present', 'absent'], default='present'),
            api_token = dict(aliases=['API_TOKEN'], no_log=True),
            name = dict(type='str'),
            droplet_id = dict(type='int'),
            droplet_ip = dict(type='str'),
            region_id = dict(type='str'),
            floating_ip = dict(type='str'),
        ),
        required_together = (
            ['command', 'state']
        ),
       #  required_if = ([
       #          ('command','assign',['floating_ip']),
       #      ]
       # ),
    )
    if not HAS_DO:
        module.fail_json(msg='python-digitalocean >= 1.8 required for this module')

    try:
        core(module)
    except Exception, e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *

if __name__ == '__main__':
#    epdb.serve()
    main()
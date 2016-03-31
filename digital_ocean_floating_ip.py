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

    @classmethod
    def reserveFloatingIP(cls, region_slug):
        return digitalocean.FloatingIP(token=cls.manager.token, region_slug=region_slug)

    @classmethod
    def destroyFloatingIP(cls, ip):
        floatingIP = cls.getFloatingIP(ip)
        if floatingIP != None:
            floatingIP.destroy()
            return floatingIP

    @classmethod
    def unassignFloatingIP(cls, ip):
        floatingIP = cls.getFloatingIP(ip)
        if floatingIP != None:
            floatingIP.unassign()
            return floatingIP

    @classmethod
    def assignFloatingIP(cls, floating_ip, droplet_ip):
        droplet = cls.getDroplet(droplet_ip)
        floatingIP = cls.getFloatingIP(floating_ip)
        if droplet != None and floatingIP != None:
            floatingIP.assign(droplet.id)
            return floatingIP

       
    def getFloatingIP(self, ip):
        floating_ips = self.manager.get_all_floating_ips()
        for floating_ip in floating_ips:
            if ip == floating_ip.ip:
                return floating_ip

    def getDroplet(self, ip):
        droplets = self.manager.get_all_droplets()
        for droplet in droplets:
            if droplet.ip_address == droplet_ip:
                return droplet

    def getDroplet(self, droplet_ip, droplet_id):
        if droplet_id != None:




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

    epdb.serve()
    DOManager.setup(api_token)

    if command == 'assign':
        if state == 'present':
            dropletIP = getkeyordie('droplet_ip')
            floatingIP = getkeyordie('floating_ip')
            data = DOManager.assignFloatingIP(floatingIP, dropletIP)


        elif state == 'absent':
            ip = getkeyordie('floating_ip')
            floatingIP = DOManager.unassignFloatingIP(ip) 
            if floatingIP:
                module.exit_json(changed=True, floating_ip=floatingIP.ip)
            else:
                module.exit_json(changed=False)

    elif command == 'reserve':
        if state == 'present':
            regionID = getkeyordie('region_id')
            data = DOManager.reserveFloatingIP(regionID)
            module.exit_json(changed=True, floating_ip=data.ip)

        elif state == 'absent':
            ip = getkeyordie('floating_ip')
            floatingIP = DOManager.destroyFloatingIP(ip) 
            if floatingIP:
                module.exit_json(changed=True, floating_ip=floatingIP.ip)
            else:
                module.exit_json(changed=False)
    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['assign', 'reserve']),
            state = dict(choices=['present', 'absent'], default='present'),
            api_token = dict(aliases=['API_TOKEN'], no_log=True),
            name = dict(type='str'),
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
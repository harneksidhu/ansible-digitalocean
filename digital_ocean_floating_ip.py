#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
from distutils.version import LooseVersion
import epdb
import time

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
    def reserve_floating_ip(cls, region_slug):
        return digitalocean.FloatingIP(token=cls.manager.token, region_slug=region_slug).reserve()

    @classmethod
    def destroy_floating_ip(cls, ip):
        floating_ip = cls.get_floating_ip(ip)
        if floating_ip != None:
            floating_ip.destroy()
            return floating_ip

    @classmethod
    def unassign_floating_ip(cls, ip):
        floating_ip = cls.get_floating_ip(ip)
        if floating_ip != None and floating_ip.droplet != None:
            action = floating_ip.unassign()
            action_id = action['action']['id']
            if poll_action(action_id) == True:
                return floating_ip
            else:
                raise Exception('Unable to unassign Floating IP')

    @classmethod
    def assign_floating_ip(cls, floating_ip, droplet_ip):
        droplet = cls.get_droplet(droplet_ip)
        floating_ip = cls.get_floating_ip(floating_ip)
        if droplet != None and floating_ip != None:
            if floating_ip.droplet != None and floating_ip.droplet['networks']['v4'][0]['ip_address'] = droplet.ip_address:
                return None
            else:
                action = floating_ip.assign(droplet.id)
                action_id = action['action']['id']
                if poll_action(action_id) == True:
                    return floating_ip
                else:
                    raise Exception('Unable to assign Floating IP')
        elif droplet == None:
            raise Exception('Droplet is not found')
        elif floating_ip == None:
            raise Exception('Floating IP is not found')
       
    def get_floating_ip(self, ip):
        try:
            return digitalocean.FloatingIP.get_object(token=self.manager.token,ip=ip)
        except:
            return None

    def get_droplet(self, ip):
        droplets = self.manager.get_all_droplets()
        for droplet in droplets:
            if droplet.ip_address == ip:
                return droplet

    def poll_action(self,action_id):
        end_time = time.time() + 10
        while time.time() < end_time:
            time.sleep(2)
            action = digitalocean.Action.get_object(api_token=self.manager.token, action_id=action_id)
            if action == 'completed':
                return True
            elif action == 'errored':
                return False
        return False

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

    command = module.params['command']
    state = module.params['state']

    DOManager.setup(api_token)

    if command == 'assign':
        if state == 'present':
            dropletIP = getkeyordie('droplet_ip')
            floatingIP = getkeyordie('floating_ip')
            data = DOManager.assign_floating_ip(floatingIP, dropletIP)
            if data:
                module.exit_json(changed=True, floating_ip=data.ip)
            else:
                module.exit_json(changed=False)
        elif state == 'absent':
            ip = getkeyordie('floating_ip')
            data = DOManager.unassign_floating_ip(ip) 
            if data:
                module.exit_json(changed=True, floating_ip=data.ip)
            else:
                module.exit_json(changed=False)

    elif command == 'reserve':
        if state == 'present':
            regionID = getkeyordie('region_id')
            data = DOManager.reserve_floating_ip(regionID)
            module.exit_json(changed=True, floating_ip=data.ip)

        elif state == 'absent':
            ip = getkeyordie('floating_ip')
            data = DOManager.destroy_floating_ip(ip) 
            if data:
                module.exit_json(changed=True, floating_ip=data.ip)
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
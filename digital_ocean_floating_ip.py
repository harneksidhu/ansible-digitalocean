#!/usr/bin/python

# (c) 2016, Harnek Sidhu <h6sidhu@gmail.com>
#
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


DOCUMENTATION = '''
---
module: digital_ocean_floating_ip
short_description: Reserve/destroy or assign/unassign a floating ip in DigitalOcean
description:
     - Reserve/destroy a floating ip in DigitalOcean, or assign/unnasign a floating ip to a droplet. 
version_added: "2.1"
author: "Harnek Sidhu"
options:
  command:
    description:
     - Which operation do you want to perform.
    choices: ['assign', 'reserve']
    required: true
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
    required: true
  api_token:
    description:
     - DigitalOcean api token.
  droplet_ip:
    description:
     - The droplet ip you want to operate on.
  floating_ip:
    description:
     - The floating ip you want to operate on.
  region_id:
    description:
     - This is the slug of the region you would like your floating ip to be reserved in.
notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN. They both refer to the v2 token.
requirements:
  - "python >= 2.6"
  - "python-digitalocean >= 1.8"
'''


EXAMPLES = '''
# Reserve a new Floating IP
# Will return the floating ip address
- digital_ocean_floating_ip:
    state: present
    command: reserve
    api_token: XXX
    region_id: ams2
  register: ip
- debug: msg="IP is {{ ip.floating_ip }}"

# Destroy a Floating IP
# If floating ip exists, it will be destroyed and changed = True
# If floating ip does not exist, module will return and changed = False
- digital_ocean_floating_ip:
    state: absent
    command: reserve
    api_token: XXX
    floating_ip: "{{ floating_ip }}"

# Assign a Floating IP to a Droplet
# The floating ip will be assigned to the droplet and changed = True
# If floating ip is already assigned to the droplet, module will return and changed = False
- digital_ocean_floating_ip:
    state: present
    command: assign
    api_token: XXX
    floating_ip: "{{ floating_ip }}"
    droplet_ip: "{{ droplet_ip }}"

# Unassign a Floating IP from a Droplet
# If floating ip is assigned to a droplet, it will be unassigned and changed = True
# If floating ip is not assigned to a droplet, module will return and changed = False
- digital_ocean_floating_ip:
    state: absent
    command: assign
    api_token: XXX
    floating_ip: "{{ floating_ip }}"

'''
RETURN = '''
floating_ip:
    description: The floating ip that was used in the task 
    returned: changed
    type: string
    sample: "192.168.0.1"

'''

import os
import time
from distutils.version import LooseVersion
import time

HAS_DO = True
try:
    import digitalocean
    from digitalocean.baseapi import Error
    if LooseVersion(digitalocean.__version__) < LooseVersion('1.8'):
        HAS_DO = False
except ImportError:
    HAS_DO = False

class FloatingIPException(Exception):
    pass


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
            if cls.poll_action(action_id) == True:
                return floating_ip
            else:
                raise FloatingIPException('Unable to unassign Floating IP')

    @classmethod
    def assign_floating_ip(cls, floating_ip, droplet_ip):
        droplet = cls.get_droplet(droplet_ip)
        floating_ip = cls.get_floating_ip(floating_ip)
        if droplet != None and floating_ip != None:
            if floating_ip.droplet != None and floating_ip.droplet['networks']['v4'][0]['ip_address'] == droplet.ip_address:
                return None
            else:
                cls.unassign_floating_ip_from_droplet(droplet_ip)
                action = floating_ip.assign(droplet.id)
                action_id = action['action']['id']
                if cls.poll_action(action_id) == True:
                    return floating_ip
                else:
                    raise FloatingIPException('Unable to assign Floating IP')
        elif droplet == None:
            raise FloatingIPException('Droplet is not found')
        elif floating_ip == None:
            raise FloatingIPException('Floating IP is not found')
       
    @classmethod
    def get_floating_ip(cls, ip):
        floating_ips = cls.manager.get_all_floating_ips()
        for floating_ip in floating_ips:
            if floating_ip.ip == ip:
                return floating_ip
        return None

    @classmethod
    def get_droplet(cls, ip):
        droplets = cls.manager.get_all_droplets()
        for droplet in droplets:
            if droplet.ip_address == ip:
                return droplet

    @classmethod
    def poll_action(cls, action_id):
        end_time = time.time() + 10
        while time.time() < end_time:
            time.sleep(2)
            action = digitalocean.Action.get_object(api_token=cls.manager.token, action_id=action_id)
            if action.status == 'completed':
                return True
            elif action.status == 'errored':
                return False
        return False

    @classmethod
    def unassign_floating_ip_from_droplet(self, droplet_ip):
        floating_ips = self.manager.get_all_floating_ips()
        for floating_ip in floating_ips:
            if floating_ip.droplet != None and floating_ip.droplet['networks']['v4'][0]['ip_address'] == droplet_ip:
                return self.unassign_floating_ip(floating_ip.ip)

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
            floating_ip = getkeyordie('floating_ip')
            data = DOManager.unassign_floating_ip(floating_ip) 
            if data:
                module.exit_json(changed=True, floating_ip=data.ip)
            else:
                module.exit_json(changed=False)

    elif command == 'reserve':
        if state == 'present':
            region_id = getkeyordie('region_id')
            data = DOManager.reserve_floating_ip(region_id)
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
            droplet_ip = dict(type='str'),
            floating_ip = dict(type='str'),
            region_id = dict(type='str'),
        ),
        required_together = (
            ['command', 'state']
        ),
    )
    if not HAS_DO:
        module.fail_json(msg='python-digitalocean >= 1.8 required for this module')

    try:
        core(module)
    except FloatingIPException, e:
        module.fail_json(msg=str(e))
    except Error, e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
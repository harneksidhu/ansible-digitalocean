#!/usr/bin/python
# -*- coding: utf-8 -*-

# SSL Error: http://stackoverflow.com/questions/29134512/insecureplatformwarning-a-true-sslcontext-object-is-not-available-this-prevent
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
        required_together = (
            ['size_id', 'image_id', 'region_id'],
        ),
    )
    if not HAS_DO:
        module.fail_json(msg='python-digitalocean >= 1.8 required for this module')

    try:
#        epdb.serve()
        droplet = digitalocean.Droplet(token=module.params['api_token'],
                               name=module.params['name'],
                               region=module.params['region_id'],
                               image=module.params['image_id'],
                               size_slug=module.params['size_id'],
                               backups=False)
        droplet.create()
        module.exit_json(changed=True)
    except Exception, e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
#    epdb.serve()
    main()
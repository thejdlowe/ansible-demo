#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
import os
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
module: throttle

short_description: This is my test module

version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:

    action:
        description: The action to perform on the throttle configuration. Can be 'get', 'set', or 'delete'.
        required: false
        type: str
        default: 'get'
    
    value:
        description: The value to set for the throttle configuration. For 'set' action, it should be in the format 'service:requestPerSecond:burstSize'.
            For delete action, it should be the service name to delete.
        required: false
        type: str
        default: ''

    path:
        description: The path to the throttle configuration file.
        required: false
        type: str
        default: '/etc/myapp/config'
        notes: If the file does not exist, it will be created.

    force:
        description: Whether or not to ignore the hard limit of 10000 requests per second when setting a new throttle configuration. If true, the module
            will allow setting a requestPerSecond value greater than 10000, but will issue a warning.
            If false, the module will fail if requestPerSecond is greater than 10000.
        required: false
        type: bool
        default: false
    

author:
    - J.D. Lowe (@thejdlowe)
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
    action:
        description: The action that was performed.
        type: str
        returned: always
        sample: 'get'
    data:
        description: The current throttle configuration for all services, returned as a dictionary where the keys
            are service names and the values are dictionaries with 'requestPerSecond' and 'burstSize' keys.
        type: dict
    changed:
        description: Whether or not the throttle configuration was changed.
        type: bool
        returned: always
'''

def run_module():
    module_args = dict(
        action=dict(type='str', required=False, default='get', choices=['get', 'set', 'delete']),
        value=dict(type='str', required=False, default=''),
        path=dict(type='str', required=False, default='/etc/myapp/config'),
        force=dict(type='bool', required=False, default=False),
        overwrite=dict(type='bool', required=False, default=False)
    )

    ansible_message = "# This file is managed by Ansible. Do not edit it manually.\n"

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        action=module.params['action'],
        data = dict()
    )

    setUpdate = False

    maximum_request_per_second = 10000

    throttle_path = module.params['path']
    throttle_force = module.params['force']
    throttle_value = module.params['value']
    throttle_action = module.params['action']
    throttle_overwrite = module.params['overwrite']
    actionSplit = throttle_value.strip().split(':')
    actionService = actionSplit[0]
    actionBurstSize = None
    actionRequestPerSecond = None

    if throttle_action == 'set':
        if len(actionSplit) != 3:
            module.fail_json(msg="For 'set' action, value must be in the format 'service:requestPerSecond:burstSize'", **result)
        actionService, actionRequestPerSecond, actionBurstSize = actionSplit
        actionRequestPerSecond = int(actionRequestPerSecond)
        actionBurstSize = int(actionBurstSize)
        if actionRequestPerSecond <= 0 or actionBurstSize <= 0:
            module.fail_json(msg="requestPerSecond and burstSize must be positive integers", **result)
        if actionBurstSize > actionRequestPerSecond:
            module.fail_json(msg="burstSize cannot be greater than requestPerSecond", **result)
        if actionRequestPerSecond > maximum_request_per_second:
            if not throttle_force:
                module.fail_json(msg=f"requestPerSecond cannot be greater than {maximum_request_per_second}", **result)
            else:
                module.warn(f"requestPerSecond is greater than {maximum_request_per_second}, but 'force' is enabled, so proceeding anyway")
    
    if not os.path.exists(throttle_path):
        with open(throttle_path, 'w') as f:
            f.write(ansible_message)
    
    with open(throttle_path, 'r+') as f:
        lines = f.readlines()
    
    if ansible_message not in lines:
        lines.insert(0, ansible_message)
        result['changed'] = True
    
    
    for line in lines[:]:
        if not line.startswith("#"):
            lineSplit = line.strip().split(':')
            if len(lineSplit) == 3:
                # service : request per second : burst size
                lineService, lineRequestPerSecond, lineBurstSize = lineSplit
                lineRequestPerSecond = int(lineRequestPerSecond)
                lineBurstSize = int(lineBurstSize)
                result['data'][lineService] = {
                    'requestPerSecond': lineRequestPerSecond,
                    'burstSize': lineBurstSize
                }
                if actionService == lineService:
                    if throttle_action == 'delete':
                        lines.remove(line)
                        result['changed'] = True
                        del result['data'][lineService]
                    elif throttle_action == 'set':
                        newLine = f"{lineService}:{actionRequestPerSecond}:{actionBurstSize}\n"
                        if lines[lines.index(line)] != newLine:
                            lines[lines.index(line)] = newLine
                            result['changed'] = True
                            result['data'][lineService] = {
                                'requestPerSecond': actionRequestPerSecond,
                                'burstSize': actionBurstSize
                            }
                        else:
                            result['data'][lineService] = {
                                'requestPerSecond': lineRequestPerSecond,
                                'burstSize': lineBurstSize
                            }
                        setUpdate = True
                    else:
                         result['data'][lineService] = {
                            'requestPerSecond': lineRequestPerSecond,
                            'burstSize': lineBurstSize
                        }
            else:
                module.warn(f"Invalid line in throttle configuration file: {line}")
                    

    if result['changed'] == False:
        if throttle_action == 'set' and not setUpdate:
            lines.append(f"{throttle_value}\n")
            result['changed'] = True
            result['data'][actionService] = {
                'requestPerSecond': actionRequestPerSecond,
                'burstSize': actionBurstSize
            }

    if result['changed'] == True and module.check_mode == False:
        with open(throttle_path, 'w') as f:
            f.writelines("".join(lines))

    if module.check_mode:
        result["changed"] = False
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
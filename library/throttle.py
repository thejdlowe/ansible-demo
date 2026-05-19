#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        action=dict(type='str', required=False, default='get', choices=['get', 'set', 'delete']),
        value=dict(type='str', required=False, default=''),
        path=dict(type='str', required=False, default='/etc/myapp/config'),
        force=dict(type='bool', required=False, default=False)
    )

    ansible_message = "# This file is managed by Ansible. Do not edit it manually.\n"

    result = dict(
        changed=False,
        data = dict()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    throttle_path = module.params['path']
    throttle_force = module.params['force']
    throttle_value = module.params['value']
    throttle_action = module.params['action']
    actionSplit = throttle_value.strip().split(':')
    actionService = None
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
    
    with open(throttle_path, 'r') as f:
        lines = f.readlines()
    
    if ansible_message not in lines:
        lines.insert(0, ansible_message)
        result['changed'] = True
    
    
    for line in lines:
        if not line.startswith("#"):
            lineSplit = line.strip().split(':')
            if len(lineSplit) == 3:
                # service : request per second : burst size
                service, requestPerSecond, burstSize = lineSplit
                requestPerSecond = int(requestPerSecond)
                burstSize = int(burstSize)
                if actionService == service:
                    if throttle_action == 'delete':
                        lines.remove(line)
                        result['changed'] = True
                    elif throttle_action == 'set':
                        newLine = f"{service}:{actionRequestPerSecond}:{actionBurstSize}\n"
                        if lines[lines.index(line)] != newLine:
                            lines[lines.index(line)] = newLine
                            result['changed'] = True
                        result['data'][service] = {
                            'requestPerSecond': requestPerSecond,
                            'burstSize': burstSize
                        }
                if throttle_action != 'delete':
                    result['data'][service] = {
                        'requestPerSecond': requestPerSecond,
                        'burstSize': burstSize
                    }

    if result['changed'] == False:
        if throttle_action == 'set':
            lines.append(f"{throttle_value}\n")
            result['changed'] = True

    if result['changed'] == True:
        with open(throttle_path, 'w') as f:
            f.writelines("".join(lines))

    if module.check_mode:
        module.exit_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
#!/usr/bin/env python

from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):

    """
    This is an Ansible Action, that combines the following modules:

    1. template
    2. script

    After script execution, it checks the returncode for the action status:

    RC=0    -> ok
    RC=-1   -> changed
    other   -> failed

    Example:

    wd_script:
        src: scripttemplate.sh
        dest: ~/targetfile.sh

    """


    import ptvsd
    ptvsd.enable_attach(address = ('127.0.0.1', 3000))
    ptvsd.wait_for_attach()
    ptvsd.break_into_debugger()


    # https://www.ansible.com/blog/how-to-extend-ansible-through-plugins
    # https://docs.ansible.com/ansible/latest/modules/shell_module.html#shell-module

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)

        dest = self._task.args['dest']
        src = self._task.args['src']
    
        args_template = dict()
        args_template["dest"] = dest
        args_template["src"] = src

        res_template = self._execute_module(
            module_name='template', 
            module_args=args_template, 
            task_vars=task_vars, 
            tmp=tmp)

        return res_template

        # common_args = {}
        # common_args['name'] = self._task.args['name']

        # res = {}
        # res['create_server'] = self._execute_module(module_name='ls_server_module', module_args=common_args, task_vars=task_vars, tmp=tmp)
        # for vnic in vnic_list:
        #   module_args = common_args.copy()
        #   module_args['other_args'] = vnic['other_args']
        #   res['vnic_'+vnic['name']] = self._execute_module(module_name='vnic_ether_module', module_args=module_args, task_vars=task_vars, tmp=tmp)
        # return res
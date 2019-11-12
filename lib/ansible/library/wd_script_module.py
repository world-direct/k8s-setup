#!/usr/bin/env python

# This module executes a script, with the following calling-convention
#
#   RC=0    -> ok
#   RC=-1   -> changed
#   other   -> failed

from ansible.module_utils.basic import *
from tempfile import NamedTemporaryFile
import os

# ansible friendly log (only prints to stdout, if not redirected (by ansible?))
def log(str):
    if sys.stdout.isatty():
        print(str)

def main():

    fields = {
        "inline": {"required": False, "type": "str"},
        "file": {"required": False, "type": "str"},
    }

    log("Init complete")
    module = AnsibleModule(argument_spec=fields)

    try:

        inline = module.params["inline"]
        file = module.params["file"]

        tmpfile = None

        if inline:
            tmpfile = NamedTemporaryFile()
            tmpfile.write(inline)
            file = tmpfile.name

        os.chmod(file, stat.S_IEXEC)
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=True)

        if tmpfile:
            tmpfile.close()

        if rc == 0:
            module.exit_json(changed=False)


        module.exit_json(changed=has_changed)
    except ModuleFailed as failed:
        module.fail_json(msg=failed.message)
        return

if __name__ == '__main__':
    main()
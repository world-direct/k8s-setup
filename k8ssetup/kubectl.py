#!/usr/bin/env python

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)

def kubectl(args, input = None):

    logger.debug("kubectl args: %s" % args)
    if input:
        logger.debug("kubectl stdin: %s" % input)

    pkubectl = subprocess.run(
        args, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=input, text=True)
        
    if pkubectl.returncode != 0:
        logger.debug("kubectl stderr: %s" % pkubectl.stderr)
        raise ValueError("kubectl retruned %s" % pkubectl.returncode)

    logger.debug("kubectl stdout: %s" % pkubectl.stdout)
    logger.debug("kubectl stderr: %s" % pkubectl.stderr)

    return pkubectl.stdout
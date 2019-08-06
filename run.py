#!/usr/bin/env python3
import logging
import json
import os, os.path as op
import subprocess as sp
import sys
import zipfile
from collections import OrderedDict
import psutil

import flywheel
from utils import *
from custom_gear_utils import *


if __name__ == '__main__':
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    #get_Custom_Logger is defined in utils.py
    context.log = get_Custom_Logger('[flywheel:C-PAC]')

    # context.init_logging()
    context.log_config()

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    # This gear will use a "Custom_Dict" dictionary as a custom-user field 
    # on the gear context.
    context.Custom_Dict ={}

    context.Custom_Dict['environ'] = environ

    try: # To download and validate BIDS 
        # for debugging:
        if context.destination['id'] == 'aex':
            # give it the tome session
            context.destination['id']='5d2761383289d60037e8b180'
        # A routine to validate on a "shadow" structure is in development
        bids_dir = op.join(context.work_dir,'bids')
        # Download Bids Directory First
        #bids_dir = context.download_session_bids(
        #    target_dir = op.join(context.work_dir,'bids')
        #)

        # Validate bids directory here
        # NOTE: C-PAC runs its own bids validator
    except Exception as e:
        context.log.error('Cannot download and validate bids.',)
        context.log.error(e,)
        os.sys.exit(1)
    # There is no cleanup after this errors out or not.
    # We exit the program. Without validated bids, we 
    # cannot proceed.

    try: # To Build/Validate/Execute CPAC commands
        # Make session-labeled directory to store all output, logs, and crash
        # Stash in gear context for later use
        fw = context.client
        analysis = fw.get(context.destination['id'])
        session = fw.get(analysis.parents['session'])
        session_label = escape_shell_chars(session.label)
        # attach session_label to Custom_Dict
        context.Custom_Dict['session_label'] = session_label
        # Create session_label in work directory
        session_dir = op.join(context.work_dir, session_label)
        os.makedirs(session_dir,exist_ok=True)
        
        # Command dictionary specifying prefix and suffix
        # for command-line parameters
        context.Custom_Dict['commandD'] = {
                    'prefix' : ['/code/run.py'],
                    'suffix' : [bids_dir, session_dir, 'participant']
        }
        # The following three functions are defined in
        # custom_gear_utils.py

        # Build CPAC optional parameters with gear context
        Build_CPAC_Params(context)

        # Validate those parameters for conflicts
        Validate_CPAC_Params(context)

        # Execute those parameters with prefix and suffix in 
        # a command dictionary
        Execute_CPAC_Params(context)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.log.error(e,)
        context.log.error('Cannot execute CPAC commands.',)
        os.sys.exit(1)

    finally:
        # Regardless of exit status, compress files for output.
        Zip_Results(context)
#!/usr/bin/env python3
import json
import os, os.path as op
import subprocess as sp
import sys

import flywheel
from utils.Custom_Logger import get_Custom_Logger
from utils import bids, args, results

if __name__ == '__main__':
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    #get_Custom_Logger is defined in utils.py
    context.log = get_Custom_Logger('[flywheel:C-PAC]')

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
        context.Custom_Dict['bids_dir'] = op.join(context.work_dir,'bids')
        bids.download(context)
        bids.run_validation(context)
        # NOTE: C-PAC runs its own bids validator that does
        # not report until the end of cpac execution
    except Exception as e:
        context.log.error('Cannot download and validate bids.',)
        context.log.error(e,)
        if context.config['gear-abort-on-bids-error']
            os.sys.exit(1)
            # There is no cleanup after this errors out or not.
            # We exit the program. Without validated bids, we 
            # cannot proceed.

    try: # To Build/Validate/Execute CPAC commands
        # Make session-labeled directory to store all output, logs, and crash
        # Stash in gear context for later use
        args.make_session_directory(context)

        # Command dictionary specifying prefix and suffix
        # for command-line parameters
        context.Custom_Dict['commandD'] = {
                    'prefix' : ['/code/run.py'],
                    'suffix' : [bids_dir, session_dir, 'participant']
        }
        # The following three functions are defined in
        # custom_gear_utils.py

        # Specify context config "blacklist" to avoid incorporating commands
        # into command line arguments
        context.Custom_Dict['blacklist'] = ['gear-save-output-on-error',
                                            'gear-run-bids-validation',
                                            'gear-abort-on-bids-error']

        # Build CPAC optional parameters with gear context
        args.build(context)

        # Validate those parameters for conflicts
        args.validate(context)

        # Execute those parameters with prefix and suffix in 
        # a command dictionary
        args.execute(context)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.Custom_Dict['Exception']=e
        context.log.error(e,)
        context.log.error('Cannot execute CPAC commands.',)
        os.sys.exit(1)

    finally:
        # Save Zipped output on Error Conditions 
        # If we have an Exception and 'gear-save-output-on-error'
        # If we have no Exception at all 
        if context.config['gear-save-output-on-error'] or \
            'Exception' not in context.Custom_Dict.keys():
            results.Zip_Results(context)
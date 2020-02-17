#!/usr/bin/env python3
import json
import os
import logging
import sys

from gear_toolkit import gear_toolkit_context
from gear_toolkit import bids, zip_tools
from utils import args


log = logging.getLogger(__name__)


def main(context):

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    # This gear will use a "custom_dict" dictionary as a custom-user field
    # on the gear context.
    context.custom_dict = {}

    context.custom_dict['environ'] = environ

    try:
        # To download and validate BIDS
        context.download_session_bids(target_dir=context.work_dir/'bids')
        err_code, bids_output = bids.validate.call_validate_bids(
            context.work_dir/'bids',
            context.work_dir
        )
        if err_code:
            log.error('BIDS validation errors were found.')
            for err in bids_output['issues']['errors']:
                log.error('%s: %s', err['key'], err['reason'])

            raise RuntimeError('Could not validate BIDS.')

        # NOTE: C-PAC runs its own bids validator that does
        # not report until the end of cpac execution
    except Exception as e:
        log.error('Cannot download and validate bids.',)
        log.exception(e)
        if context.config['gear-abort-on-bids-error']:
            return 1
            # There is no cleanup after this errors out or not.
            # We exit the program. Without validated bids, we 
            # cannot proceed.

    try:
        # To Build/Validate/Execute CPAC commands
        # Make session-labeled directory to store all output, logs, and crash
        # Stash in gear context for later use
        session_dir = args.make_session_directory(context)

        # Command dictionary specifying prefix and suffix
        # for command-line parameters
        command_dict = {
                    'prefix': ['/code/run.py'],
                    'suffix':
                    [
                        context.work_dir/'bids',
                        context.work_dir/session_dir,
                        'participant'
                    ]
        }
        # The following three functions are defined in
        # custom_gear_utils.py

        # Specify context config "blacklist" to avoid incorporating commands
        # into command line arguments
        black_list = [
            'gear-save-output-on-error',
            'gear-run-bids-validation',
            'gear-abort-on-bids-error'
        ]

        # Build CPAC optional parameters with gear context
        params = args.build(context, black_list=black_list)

        # Validate those parameters for conflicts
        args.validate(params)

        # Execute those parameters with prefix and suffix in
        # a command dictionary
        args.execute(
            context,
            params,
            command_dict=command_dict,
            environ=environ
        )

        log.info("Commands successfully executed!")
        return 0

    except Exception as e:
        log.exception(e)
        log.error('Cannot execute CPAC commands.',)
        return 1

    finally:
        # Save Zipped output on Error Conditions
        # If we have an Exception and 'gear-save-output-on-error'
        # If we have no Exception at all
        if context.config['gear-save-output-on-error'] or not sys.exc_info():
            zip_tools.zip_output(
                context.work_dir,
                session_dir,
                context.output_dir/session_dir + '.zip'
            )
            # For results with a large number of files, provide a manifest.
            # Capture the stdout/stderr in a file handle or for logging.
            manifest = context.output_dir, \
                session_dir + '_output_manifest'
            bids.tree.tree_bids(context.work_dir/session_dir, manifest)


if __name__ == '__main__':
    with gear_toolkit_context.GearToolkitContext() as gear_context:
        gear_context.init_logging()
        exit_status = main(gear_context)

    log.info('exit_status is %s', exit_status)
    os.sys.exit(exit_status)

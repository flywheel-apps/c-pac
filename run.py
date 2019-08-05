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


def Build_CPAC_Params(context):
    # use Ordered Dictionary to keep the order created.
    # Default in Python 3.6 onward
    Params=OrderedDict()

    if context.get_input_path('pipeline_file'):
        Params['pipeline_file'] = context.get_input_path('pipeline_file')

    config = context.config
    for key in config.keys():
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                Params[key] = True
        else:
            if len(key) == 1:
                Params[key] = config[key]
            else:
                # if the key-value is zero, we skip and use the defaults
                if config[key] > 0:
                    Params[key] = config[key]

    return Params

def Validate_CPAC_Params(cpac_params,context):
    """
    Input: parameters built by Build_CPAC_Params
    Throws Exception on violation
    Logs Warning on what may cause problems
    """

    # Check that cpus are between 0 and max number of cpus
    if "n_cpus" in cpac_params.keys():
        if cpac_params["n_cpus"] < 0:
            context.log.Warning('You can\'t have a negative number of cpus. Assuming defaults.')
        elif cpac_params["n_cpus"] > psutil.cpu_count():
            raise Exception('You have requested more cpus than available on the host system.')

    # Check that memory is between the default (6 GB) and the max system memory
    if 'mem_gb' in cpac_params.keys():
        if (cpac_params['mem_gb'] < 0):
            context.log.Warning('You have selected a negative amount of memory. Assuming default of 6 GB.')
        elif (cpac_params['mem_gb'] < 6):
            context.log.Warning('You have requested less than the default (6 GB). This may cause a crash.')
        elif (cpac_params['mem_gb'] > psutil.virtual_memory().total/(1024**3)):
            raise Exception('You are trying to reserve more memory than the system has available.')
    elif 'mem_mb' in cpac_params.keys():
        if (cpac_params['mem_mb'] < 0):
            context.log.Warning('You have selected a negative amount of memory. Assuming default of 6 GB.')
        elif (cpac_params['mem_mb'] < 6*1024):
            context.log.Warning('You have requested less memory than the default (6 GB). This may cause a crash.')
        elif (cpac_params['mem_mb'] > psutil.virtual_memory()/(1024**2)):
            raise Exception('You are trying to reserve more memory than the system has available.')


def Build_Command_List(command, ParamList):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to
    be put into the command list as such ("-k value" or "--key=value")
    """
    for key in ParamList.keys():
        # Single character command-line parameters preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(ParamList[key])) != 0:
                command.append(str(ParamList[key]))
        # Multi-Character command-line parameters preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(ParamList[key]) == bool:
                if ParamList[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, without value include without value
                # (e.g. '--key'), else include value (e.g. '--key=value')
                if len(str(ParamList[key])) == 0:
                    command.append('--' + key)
                else:
                    command.append('--' + key + '=' + str(ParamList[key]))
    return command

def Zip_Results(context):
    # Cleanup, create manifest, create zipped results,
    # move all results to the output directory
    # This executes regardless of errors or exit status,
    os.chdir(context.work_dir)
    # If the output/result.anat path exists, zip regardless of exit status
    # Clean input_file_basename to lack esc chars and extension info

    # Grab Session label 
    fw = context.client
    analysis = fw.get(context.destination['id'])
    session = fw.get(analysis.parents['session'])
    session_dir = escape_shell_chars(session.label)
    dest_zip = op.join(context.output_dir,session_dir + '.zip')

    if op.exists(op.join(context.work_dir,session_dir)):
        context.log.info(
            'Zipping ' + session_dir + ' directory to ' + dest_zip + '.'
        )
        # For results with a large number of files, provide a manifest.
        # Capture the stdout/stderr in a file handle or for logging.
        manifest = op.join(
            context.output_dir, session_dir + '_output_manifest.txt'
        )
        command0 = ['tree', '-shD', '-D', session_dir]
        with open(manifest, 'w') as f:
            result0 = sp.run(command0, stdout = f)
        command1 = ['zip', '-r', dest_zip, session_dir]
        result1 = sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        context.log.info(
            'No results directory, ' + \
            op.join(context.work_dir,session_dir) + \
            ', to zip.')

if __name__ == '__main__':
    context = flywheel.GearContext()
    context.log = get_Custom_Logger('[flywheel:C-PAC]')

    # context.init_logging()
    context.log_config()

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    try:
        # for debugging:
        if context.destination['id'] == 'aex':
            # give it the tome session
            context.destination['id']='5d2761383289d60037e8b180'
        # Make session-level directory to store all output,logs, and crash
        fw = context.client
        analysis = fw.get(context.destination['id'])
        session = fw.get(analysis.parents['session'])
        session_dir = escape_shell_chars(session.label)
        session_dir = op.join(context.work_dir, session_dir)
        os.makedirs(session_dir, exist_ok=True)

        # Download Bids Directory First
        bids_dir = context.download_session_bids(
            target_dir = op.join(context.work_dir,'bids')
        )

        # Build CPAC optional parameters with gear context
        cpac_params = Build_CPAC_Params(context)

        # Validate those parameters for conflicts
        Validate_CPAC_Params(cpac_params,context)

        # Build command-line parameters
        command = ['/code/run.py']
        command = Build_Command_List(command, cpac_params)

        # Extend with positional arguments
        command.extend([bids_dir, session_dir, 'participant'])

        context.log.info('CPAC Command-Line: '+' '.join(command))

        # use subprocess to run the command and capture the output
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)

        context.log.info(result.returncode)
        context.log.info(result.stdout)

        if result.returncode != 0:
            context.log.error('The command:\n ' +
                              ' '.join(command) +
                              '\nfailed. See log for debugging.')
            context.log.error(result.stderr)
            os.sys.exit(result.returncode)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.log.error(e)
        context.log.error('Cannot execute C-PAC commands.')
        os.sys.exit(1)

    finally:
        # Regardless of exit status, compress files for output.
        Zip_Results(context)
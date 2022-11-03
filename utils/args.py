import os
import sys
from collections import OrderedDict
import psutil
import re

from gear_toolkit.command_line import build_command_list, exec_command


def make_session_directory(context):
    """
    This function acquires the session.label and uses it to store the output
    of the algorithm.  This will keep the working output of the algorithm
    separate from the bids input in work/bids.
    """
    fw = context.client
    analysis = fw.get(context.destination['id'])
    session = fw.get(analysis.parents['session'])
    # Make sure we have shell-safe characters in path
    session_label = re.sub('[^0-9a-zA-Z./]+', '_', session.label)

    os.makedirs(context.work_dir/session_label, exist_ok=True)
    return session_label


def build(context, black_list=None):
    # use Ordered Dictionary to keep the order created.
    # Default in Python 3.6 onward
    params = OrderedDict()

    if context.get_input_path('pipeline_file'):
        params['pipeline_file'] = context.get_input_path('pipeline_file')

    config = context.config
    for key in config.keys():
        if key not in black_list:
            # Use only those boolean values that are True
            if type(config[key]) == bool:
                if config[key]:
                    params[key] = True
            else:
                if len(key) == 1:
                    params[key] = config[key]
                else:
                    # if the key-value is zero, we skip and use the defaults
                    if config[key] > 0:
                        params[key] = config[key]

    return params


def validate(context):
    """
    Input: gear context with parameters in context.custom_dict['cpac_params']
    Attempts to correct any violations
    Logs warning on what may cause problems
    """
    cpac_params = context.custom_dict['cpac_params']
    # Check that cpus are between 0 and max number of cpus
    if "n_cpus" in cpac_params.keys():
        if cpac_params["n_cpus"] < 0:
            context.log.warning(
                'You can\'t have a negative number of cpus. \
                Assuming Max CPUs, %f.', psutil.cpu_count()
            )
            cpac_params["n_cpus"] = psutil.cpu_count()
        elif cpac_params["n_cpus"] > psutil.cpu_count():
            context.log.warning(
                'You have requested more cpus than available \
                on the host system. Assuming Max CPUs, %f.',
                psutil.cpu_count()
            )
            cpac_params["n_cpus"] = psutil.cpu_count()

    # Check that memory is between the default (6 GB) and the max system memory
    # 'mem_gb' takes precedence
    if 'mem_gb' in cpac_params.keys():
        if (cpac_params['mem_gb'] < 0):
            context.log.warning(
                'You have selected a negative amount of memory.\
                Assuming System Max of %f GB.', 
                psutil.virtual_memory().total/(1024**3)
            )
            cpac_params['mem_gb'] = psutil.virtual_memory().total/(1024**3)
        elif (cpac_params['mem_gb'] < 6):
            context.log.warning(
                'You have requested less than the default (6 GB). \
                This may cause a crash.'
            )
        elif (cpac_params['mem_gb'] > psutil.virtual_memory().total/(1024**3)):
            context.log.warning(
                'You are trying to reserve more memory than the \
                system has available. \
                Setting to 90 percent of System maximum. %f GB.',
                psutil.virtual_memory().total*0.9/(1024**3)
            )
            cpac_params['mem_gb'] = psutil.virtual_memory().total*0.9/(1024**3)
    elif 'mem_mb' in cpac_params.keys():
        if (cpac_params['mem_mb'] < 0):
            context.log.warning(
                'You have selected a negative amount of memory. \
                Assuming System Max of %f MB.',
                psutil.virtual_memory().total/(1024**2)
            )
            cpac_params['mem_gb'] = psutil.virtual_memory().total/(1024**2)
        elif (cpac_params['mem_mb'] < 6*1024):
            context.log.warning(
                'You have requested less than the default (6 GB). \
                This may cause a crash.'
            )
        elif (cpac_params['mem_mb'] > psutil.virtual_memory()/(1024**2)):
            context.log.warning(
                'You are trying to reserve more memory than the system has \
                available. Setting to 90 percent of System maximum. %f GB.',
                psutil.virtual_memory().total*0.9/(1024**3)
            )
            cpac_params['mem_mb'] = psutil.virtual_memory().total*0.9/(1024**2)


def execute(context, params, command_dict=None, dry_run=False, environ=None):
    # Build command-line parameters
    command = build_command_list(command_dict['prefix'], params)

    # Extend with positional arguments
    command.extend(command_dict['suffix'])

    context.log.info('CPAC Command-Line: '+' '.join(command))
    # The dry_run variable does not execute command
    exec_command(command, dry_run=dry_run, environ=environ)

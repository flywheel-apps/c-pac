import os, os.path as op
import subprocess as sp
import sys
from collections import OrderedDict
import psutil
import re

import flywheel

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
    # attach session_label to custom_dict
    context.custom_dict['session_label'] = session_label
    # Create session_label in work directory
    session_dir = op.join(context.work_dir, session_label)
    context.custom_dict['session_dir']=session_dir
    os.makedirs(session_dir,exist_ok=True)

def build(context):
    # use Ordered Dictionary to keep the order created.
    # Default in Python 3.6 onward
    Params=OrderedDict()

    if context.get_input_path('pipeline_file'):
        Params['pipeline_file'] = context.get_input_path('pipeline_file')

    # This "black_list" list will skip keys if present in context.custom_dict
    black_list = []
    if 'black_list' in context.custom_dict.keys():
        black_list = context.custom_dict['black_list']

    config = context.config
    for key in config.keys():
        if key not in black_list:
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

    context.custom_dict['cpac_params'] = Params

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
            context.log.warning('You can\'t have a negative number of cpus. Assuming Max CPUs, %f.',psutil.cpu_count())
            cpac_params["n_cpus"] = psutil.cpu_count()
        elif cpac_params["n_cpus"] > psutil.cpu_count():
            context.log.warning('You have requested more cpus than available on the host system. Assuming Max CPUs, %f.', psutil.cpu_count())
            cpac_params["n_cpus"] = psutil.cpu_count()

    # Check that memory is between the default (6 GB) and the max system memory
    # 'mem_gb' takes precedence
    if 'mem_gb' in cpac_params.keys():
        if (cpac_params['mem_gb'] < 0):
            context.log.warning('You have selected a negative amount of memory. ' + \
                'Assuming System Max of %f GB.', \
                psutil.virtual_memory().total/(1024**3))
            cpac_params['mem_gb'] = psutil.virtual_memory().total/(1024**3)
        elif (cpac_params['mem_gb'] < 6):
            context.log.warning('You have requested less than the default (6 GB). This may cause a crash.')
        elif (cpac_params['mem_gb'] > psutil.virtual_memory().total/(1024**3)):
            context.log.warning('You are trying to reserve more memory than the system has available. '+ \
                                'Setting to 90 percent of System maximum. %f GB.', 
                                psutil.virtual_memory().total*0.9/(1024**3))
            cpac_params['mem_gb'] = psutil.virtual_memory().total*0.9/(1024**3)
    elif 'mem_mb' in cpac_params.keys():
        if (cpac_params['mem_mb'] < 0):
            context.log.warning('You have selected a negative amount of memory. ' + \
                'Assuming System Max of %f MB.', \
                psutil.virtual_memory().total/(1024**2))
            cpac_params['mem_gb'] = psutil.virtual_memory().total/(1024**2)
        elif (cpac_params['mem_mb'] < 6*1024):
            context.log.warning('You have requested less than the default (6 GB). This may cause a crash.')
        elif (cpac_params['mem_mb'] > psutil.virtual_memory()/(1024**2)):
            context.log.warning('You are trying to reserve more memory than the system has available. '+ \
                                'Setting to 90 percent of System maximum. %f GB.',
                                psutil.virtual_memory().total*0.9/(1024**3))
            cpac_params['mem_mb'] = psutil.virtual_memory().total*0.9/(1024**2)


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

def execute(context, dry_run=False):
        # Get Params
        cpac_params = context.custom_dict['cpac_params']
        commandD = context.custom_dict['commandD']
        environ = context.custom_dict['environ']

        # Build command-line parameters
        command = Build_Command_List(commandD['prefix'], cpac_params)

        # Extend with positional arguments
        command.extend(commandD['suffix'])

        context.log.info('CPAC Command-Line: '+' '.join(command))
        # The dry_run variable does not execute command
        if not dry_run:
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

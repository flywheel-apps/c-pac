import os, os.path as op
import subprocess as sp
import sys
from collections import OrderedDict
import psutil

import flywheel

def Build_Params(context):
    # use Ordered Dictionary to keep the order created.
    # Default in Python 3.6 onward
    Params=OrderedDict()

    if context.get_input_path('pipeline_file'):
        Params['pipeline_file'] = context.get_input_path('pipeline_file')

    # This "black_list" list will skip keys if present in context.Custom_Dict
    black_list = []
    if 'black_list' in context.Custom_Dict.keys():
        black_list = context.Custom_Dict['black_list']

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

    context.Custom_Dict['cpac_params'] = Params

def Validate_Params(context):
    """
    Input: gear context with parameters in context.Custom_Dict['cpac_params']
    Attempts to correct any violations
    Logs warning on what may cause problems
    """
    cpac_params = context.Custom_Dict['cpac_params']
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

def Execute_Params(context, dry_run=True):
        # Get Params
        cpac_params = context.Custom_Dict['cpac_params']
        commandD = context.Custom_Dict['commandD']
        environ = context.Custom_Dict['environ']

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

def Zip_Results(context):
    # Cleanup, create manifest, create zipped results,
    # move all results to the output directory
    # This executes regardless of errors or exit status,
    os.chdir(context.work_dir)
    # If the output/result.anat path exists, zip regardless of exit status
    # Clean input_file_basename to lack esc chars and extension info

    # Grab Session label
    session_label = context.Custom_Dict['session_label']
    dest_zip = op.join(context.output_dir,session_label + '.zip')

    if op.exists(op.join(context.work_dir,session_label)):
        context.log.info(
            'Zipping ' + session_label + ' directory to ' + dest_zip + '.'
        )
        # For results with a large number of files, provide a manifest.
        # Capture the stdout/stderr in a file handle or for logging.
        manifest = op.join(
            context.output_dir, session_label + '_output_manifest.txt'
        )
        command0 = ['tree', '-shD', '-D', session_label]
        with open(manifest, 'w') as f:
            result0 = sp.run(command0, stdout = f)
        command1 = ['zip', '-r', dest_zip, session_label]
        result1 = sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        context.log.info(
            'No results directory, ' + \
            op.join(context.work_dir,session_label) + \
            ', to zip.'
        )
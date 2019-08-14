#!/usr/bin/env python3

import os, os.path as op
import subprocess as sp
import json
import pprint



def download(context):
    """ Download all files from the session in BIDS format
        bids_dir will point to the local BIDS folder
        This creates a simiple dataset_description.json if
        one did not get downloaded.
    """

    # the usual BIDS path:
    bids_dir = context.Custom_Dict['bids_dir']

    # If BIDS was already downloaded, don't do it again
    # (this saves time when developing locally)
    if not op.isdir(bids_dir):

        bids_dir = context.download_session_bids(target_dir=bids_dir)
        # Use the following command instead (after core is updated with a fix
        # for it) because it will return the existing dataset_description.json
        # file and does not download scans that don't need to be considered.
        # bids_dir = context.download_project_bids(folders=['anat', 'func'])

        # make sure dataset_description.json exists
        # Is there a way to download the dataset_description.json file from the 
        # platform instead of creating a generic stub?
        required_file = bids_dir + '/dataset_description.json'
        if not op.exists(required_file):
            context.log.info(' Creating missing {}.'.format(required_file))
            the_stuff = {
                "Acknowledgements": "",
                "Authors": [],
                "BIDSVersion": "1.2.0",
                "DatasetDOI": "",
                "Funding": "",
                "HowToAcknowledge": "",
                "License": "",
                "Name": "tome",
                "ReferencesAndLinks": [],
                "template": "project"
            }
            with open(required_file, 'w') as outfile:
                json.dump(the_stuff, outfile)
        else:
            context.log.info('{} exists.'.format(required_file))

        context.log.info(' BIDS was downloaded into {}'.format(bids_dir))

    else:
        context.log.info(' Using existing BIDS path {}'.format(bids_dir))

    return bids_dir


def run_validation(context):
    """ Run BIDS Validator on bids_dir
        Install BIDS Validator into container with: 
            RUN npm install -g bids-validator
        This prints a summary of files that are valid,
        and then lists errors and warnings.
        Then it exits if gear-abort-on-bids-error is set and
        if there are any errors.
        The config MUST contain both of these:
            gear-run-bids-validation
            gear-abort-on-bids-error
    """

    config = context.config
    bids_dir = context.Custom_Dict['bids_dir']
    environ = context.Custom_Dict['environ']
    if 'gear-run-bids-validation' not in config.keys():
        raise Exception("'gear-run-bids-validation' not in gear configuration.")
    elif config['gear-run-bids-validation']:

        command = ['bids-validator', '--verbose', '--json', bids_dir]
        context.log.info(' Command:' + ' '.join(command))
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)
        context.log.info(' {} return code: '.format(command) + str(result.returncode))
        bids_output = json.loads(result.stdout)

        # show summary of valid BIDS stuff
        context.log.info(' bids-validator results:\n\nValid BIDS files summary:\n' +
                 pprint.pformat(bids_output['summary'], indent=8) + '\n')

        num_bids_errors = len(bids_output['issues']['errors'])

        # show all errors
        for err in bids_output['issues']['errors']:
            err_msg = err['reason'] + '\n'
            for ff in err['files']:
                if ff["file"]:
                    err_msg += '       {}\n'.format(ff["file"]["relativePath"])
            context.log.error(' ' + err_msg)

        # show all warnings
        for warn in bids_output['issues']['warnings']:
            warn_msg = warn['reason'] + '\n'
            for ff in warn['files']:
                if ff["file"]:
                    warn_msg += '       {}\n'.format(ff["file"]["relativePath"])
            context.log.warning(' ' + warn_msg)
        if 'gear-abort-on-bids-error' not in config.keys():
            raise Exception("'gear-abort-on-bids-error' not in config!")
        elif config['gear-abort-on-bids-error'] and num_bids_errors > 0:
            raise Exception(' {} BIDS validation errors '.format(num_bids_errors) +
                         'were detected: NOT running command.')


def tree(bids_dir, environ):

    command = ['tree', bids_dir]
    context.log.info(' Command:' + ' '.join(command))
    result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                    universal_newlines=True, env=environ)
    context.log.info('  {command[0]} return code: ' + str(result.returncode))

    html1 = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n' + \
            '<html>\n' + \
            '  <head>\n' + \
            '    <meta http-equiv="content-type" content="text/html; charset=UTF-8">\n' + \
            '    <title>Tree_work_bids</title>\n' + \
            '  </head>\n' + \
            '  <body>\n' + \
            '    Output of <tt><b>tree work/bids</b></tt><br>\n' + \
            '    <blockquote><tt>work/bids/<br>\n'

    html2 = '      </tt><br>\n' + \
            '    </blockquote>\n' + \
            '  </body>\n' + \
            '</html>\n'

    # put all of that text into the actual file
    with open("output/bids_tree.html", "w") as text_file:
        text_file.write(html1)
        for line in result.stdout.split('\n'):
            text_file.write(line+'<br>\n')
        text_file.write(html2)

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'

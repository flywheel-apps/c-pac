#!/usr/bin/env python3
import logging
import json
import os
import subprocess
import sys
import zipfile

import flywheel


log = logging.getLogger('flywheel:C-PAC')


if __name__ == '__main__':
    with flywheel.GearContext() as context:
        context.init_logging()
        context.log_config()

        # Find the pipeline file path
        pipeline_file_path = context.get_input_path('pipeline_file')

        # Download bids first
        bids_dir = context.download_session_bids()

        # Load environment
        with open('/cpac_environ.json', 'r') as f:
            environ = json.load(f)

        # Launch cpac
        if pipeline_file_path:
            cmd = ['/code/run.py', '--pipeline_file', pipeline_file_path, bids_dir, context.work_dir, 'participant']
        else:
            cmd = ['/code/run.py', bids_dir, context.work_dir, 'participant']

        log.info('calling C-PAC: %s', cmd)
        subprocess.check_call(cmd, env=environ)

        int_output_path = os.path.join(context.work_dir, 'output')
        out_path = os.path.join(context.output_dir, 'results.zip')

        log.info('Zipping int_dir to: %s', out_path)
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(int_output_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    relpath = os.path.relpath(filepath, int_output_path)
                    log.info('Adding %s...', relpath)
                    zf.write(filepath, relpath)

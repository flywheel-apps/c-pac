#!/usr/bin/env python3
import logging
import json
import os
import subprocess
import sys
import zipfile

import flywheel
from flywheel_bids.export_bids import download_bids_dir


log = logging.getLogger('bids-test')
INT_DIR = '/v0/flywheel/int_dir'
BIDS_DIR = '/v0/flywheel/bids'
OUT_DIR = '/v0/flywheel/output'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    log.info('PATH: %s', os.environ['PATH'])

    invocation  = json.loads(open('config.json').read())
    config      = invocation['config']
    inputs      = invocation['inputs']
    destination = invocation['destination']

    log.info('Inputs: %s', inputs)
    pipeline_file = inputs.get('pipeline_file')

    # Create FW client
    fw = flywheel.Client(inputs['api-key']['key'])

    # For local testing
    if destination['id'] == 'aex':
        destination = {'type': 'analysis', 'id': '5c82871cbcd3b900285c0496'}

    session = destination
    if destination['type'] == 'analysis':
        analysis = fw.get(destination['id'])
        session = analysis.parent

    log.info('Using source container: %s', session)

    # Land session in BIDS format
    for path in (INT_DIR, BIDS_DIR, OUT_DIR):
        if not os.path.exists(path):
            os.makedirs(path)

    # Download bids first
    download_bids_dir(fw, session['id'], session['type'], BIDS_DIR)

    # Launch cpac
    environ = os.environ.copy()
    environ['PATH'] = ':'.join(['/usr/local/miniconda/bin', '/opt/ICA-AROMA', '/usr/lib/fsl/5.0', 
        '/opt/afni', '/opt/c3d/bin', '/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin'])
    environ['C3DPATH'] = '/opt/c3d/'
    environ['FSLDIR'] = '/usr/share/fsl/5.0' 
    environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
    environ['FSLMULTIFILEQUIT'] = 'TRUE'
    environ['POSSUMDIR'] = '/usr/share/fsl/5.0'
    environ['LD_LIBRARY_PATH'] = '/usr/lib/fsl/5.0:{}'.format(environ.get('LD_LIBRARY_PATH', ''))
    environ['FSLTCLSH'] = '/usr/bin/tclsh'
    environ['FSLWISH'] = '/usr/bin/wish'
    cmd = ['/code/run.py', BIDS_DIR, INT_DIR, 'participant']

    if pipeline_file:
        pipeline_file_path = pipeline_file['location']['path']
        cmd.insert(1, '--pipeline_file')
        cmd.insert(2, pipeline_file_path)

    log.info('calling C-PAC: %s', cmd)
    subprocess.check_call(cmd, env=environ)

    int_output_path = os.path.join(INT_DIR, 'output')
    out_path = os.path.join(OUT_DIR, 'results.zip')
    log.info('Zipping int_dir to: %s', out_path)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(int_output_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                log.info('Adding %s...', filepath)
                zf.write(filepath)

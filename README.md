[![Docker Pulls](https://img.shields.io/docker/pulls/flywheel/c-pac.svg)](https://hub.docker.com/r/flywheel/c-pac/)
[![Docker Stars](https://img.shields.io/docker/stars/flywheel/c-pac.svg)](https://hub.docker.com/r/flywheel/c-pac/)

# flywheel/c-pac
## Configurable Pipeline for the Analysis of Connectomes (C-PAC).
A configurable, open-source, Nipype-based, automated processing pipeline for resting state fMRI data. Designed for use by both novice users and experts, C-PAC brings the power, flexibility and elegance of Nipype to users in a plug-and-play fashion; no programming required.

## Website
The C-PAC website is located here: http://fcp-indi.github.com/

## Usage Notes
This gear downloads the BIDS directory structure from the associated flywheel session and processes it according to the selected parameters and the prefered pipeline configuration (default or the optional pipeline_file input).

The parameters that can be configured through the gear interface are:
* anat_only
* n_cpus
* mem_mb
* mem_gb
* save_working_dir

These are a subset of the parameters that can be specified in [running the C-PAC pipeline](http://fcp-indi.github.io/docs/user/running.html) from the command-line.

For a supplied pipeline file, it is recommended to use a C-PAC configuration GUI to reduce the potential for errors (http://fcp-indi.github.io/docs/user/new_gui.html).

The size of the zipped gear output will depend on the C-PAC pipeline settings. For example, the zipped output of the defaultpipeline can exceed 4 GB. However, using the --anat-only flag will reduce this to under 70 MB.

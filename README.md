# The C-PAC gear is now hosted on [GitLab](https://gitlab.com/flywheel-io/flywheel-apps/cpac)

[![Docker Pulls](https://img.shields.io/docker/pulls/flywheel/c-pac.svg)](https://hub.docker.com/r/flywheel/c-pac/)
[![Docker Stars](https://img.shields.io/docker/stars/flywheel/c-pac.svg)](https://hub.docker.com/r/flywheel/c-pac/)

# flywheel/c-pac
## Configurable Pipeline for the Analysis of Connectomes (C-PAC).
A configurable, open-source, Nipype-based, automated processing pipeline for resting state fMRI data. Designed for use by both novice users and experts, C-PAC brings the power, flexibility and elegance of Nipype to users in a plug-and-play fashion; no programming required.

## Website
The C-PAC website is located here: http://fcp-indi.github.com/

## Usage Notes
This gear downloads the [BIDS directory structure](https://bids.neuroimaging.io/) from the associated flywheel session and processes it according to the selected parameters and the prefered pipeline configuration (default or the optional pipeline_file input).

The parameters that can be configured through the gear interface are:

* anat_only - Only run anatomical preprocessing.
* n_cpus - Number of execution resources available for the pipeline(==0: Use default).
* mem_mb - Amount of RAM available to the pipeline in megabytes. Included for compatibility with BIDS-Apps standard, but mem_gb is preferred (<=0: Use default of 6 GB).
* mem_gb - Amount of RAM available to the pipeline in megabytes. If this is specified along with mem_mb, this flag will take precedence.d (==0: Use default of 6 GB).
* save_working_dir - Save the contents of the working directory.

These are a subset of the parameters that can be specified in [running the C-PAC pipeline](http://fcp-indi.github.io/docs/user/running.html) from the command-line.

Extra parameters for troubleshooting and data-management:

* gear-save-output-on-error - Save the contents of the working directory to output on failure (can be large).
* gear-run-bids-validation - Run bids-validator on a the gear bids directory.
* gear-abort-on-bids-error - If bids-validator returns an error, abort gear execution.

For a supplied pipeline file, it is recommended to use a [C-PAC configuration GUI](http://fcp-indi.github.io/docs/user/new_gui.html) to reduce the potential for errors.

The size of the zipped gear output will depend on the C-PAC pipeline settings. For example, the zipped output of the defaultpipeline can exceed 4 GB. However, using the --anat-only flag will reduce this to under 70 MB.

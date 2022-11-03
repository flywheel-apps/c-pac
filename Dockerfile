# This Dockerfile constructs a docker image to run C-PAC
#
# Example build:
#   docker build --no-cache --tag flywheel/c-pac `pwd`
#

# Start with the bids/cpac
FROM fcpindi/c-pac:release-v1.6.0

# Note the Maintainer
LABEL MAINTAINER "Flywheel <support@flywheel.io>"

# Install packages
RUN apt-get update && \
	apt-get install -y --allow-unauthenticated \
	zip \
	python3-pip \
	tree && \
	rm -rf /var/lib/apt/lists/*

# Install gear python dependencies
RUN pip3 install --upgrade pip && \
	pip3.5 install \
	flywheel_sdk==10.7.0 \
	flywheel_bids \
    flywheel-gear-toolkit \
	bids-validator \
	psutil && \
    rm -rf /root/.cache/pip


# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# Copy and configure run script and metadata code
# Copy executable/manifest to Gear
COPY run.py ${FLYWHEEL}/run.py
COPY utils ${FLYWHEEL}/utils
COPY manifest.json ${FLYWHEEL}/manifest.json

# Save docker environ
RUN python -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Configure entrypoint
RUN chmod a+x /flywheel/v0/run.py
ENTRYPOINT ["/flywheel/v0/run.py"]

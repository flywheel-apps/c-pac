# This Dockerfile constructs a docker image to run C-PAC
#
# Example build:
#   docker build --no-cache --tag flywheel/c-pac `pwd`
#

# Start with the bids/cpac
FROM fcpindi/c-pac:release-v1.4.1

# Note the Maintainer
MAINTAINER Michael Perry <michaelperry@flywheel.io>

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
	flywheel_sdk==8.2.0 \
	flywheel_bids \
	bids-validator \
	psutil && \
    rm -rf /root/.cache/pip


# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# Copy and configure run script and metadata code
COPY run.py \
      manifest.json \
      ${FLYWHEEL}/

# Save docker environ
RUN python -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Configure entrypoint
RUN chmod a+x /flywheel/v0/run.py
ENTRYPOINT ["/flywheel/v0/run.py"]

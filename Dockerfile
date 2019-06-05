# This Dockerfile constructs a docker image to run C-PAC
#
# Example build:
#   docker build --no-cache --tag flywheel/c-pac `pwd`
#

# Start with the bids/cpac
FROM fcpindi/c-pac:release-v1.4.3

# Note the Maintainer
MAINTAINER Michael Perry <michaelperry@flywheel.io>

# Save docker environ
RUN python -c 'import os, json; f = open("/cpac_environ.json", "w"); json.dump(dict(os.environ), f)'

# Install packages
RUN apt-get update && apt-get install -y zip python3-pip

# Install flywheel_bids
RUN pip3 install flywheel_sdk==8.2.0 flywheel_bids

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}

# Copy and configure run script and metadata code
COPY run.py \
      manifest.json \
      ${FLYWHEEL}/

ENTRYPOINT ["bash"]

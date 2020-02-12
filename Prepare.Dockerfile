FROM python:3.8-slim
# Using Slim (debian) rather than Alpine because it contains wheels for opencv-python

WORKDIR /app

RUN mkdir -p /app/honeycomb_tools

COPY setup.py /app
COPY package.json /app
COPY honeycomb_tools/README.md /app/honeycomb_tools

RUN persistBuildDeps='libpq-dev libglib2.0-0 libsm6 libxext6 libxrender-dev' && \
    tmpBuildDeps='gcc' && \
    apt-get update && \
    apt-get install -y $persistBuildDeps $tmpBuildDeps && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -e . --no-cache-dir --compile && \
    apt-get purge -y --auto-remove $tmpBuildDeps

COPY scripts/ /app
COPY honeycomb_tools/*.py /app/honeycomb_tools/

CMD sh /app/prepare-geoms.sh

#
# Docker image to run tests on specific Python versions.
#
ARG TAG=3.7.3-slim-buster
FROM python:${TAG}

# Set locale and timezone
RUN DEBIAN_FRONTEND=noninteractive apt-get update &&\
    apt-get install -y locales tzdata &&\
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen &&\
    dpkg-reconfigure --frontend=noninteractive locales &&\
    update-locale LANG=fr_FR.UTF-8
ENV LANG=fr_FR.UTF-8 LC_ALL=fr_FR.UTF-8 TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime &&\
    echo $TZ > /etc/timezone

# Prepare environment
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Import code
COPY zut ./zut
COPY tests ./tests

# Define default action
CMD [ "python", "-m", "unittest" ]

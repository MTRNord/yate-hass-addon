FROM ghcr.io/hassio-addons/debian-base:7.8.3
SHELL [ "/bin/bash", "-euxo", "pipefail", "-c" ]

LABEL \
  io.hass.name="Yate Server" \
  io.hass.description="Yet Another Telephony Exchange" \
  io.hass.version="0.2.9" \
  io.hass.type="addon" \
  io.hass.arch="amd64"

RUN export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y --no-install-recommends --no-install-suggests \
        git \
        autoconf \
        make \
        gcc \
        g++ \
        libspeex1 \
        libspeexdsp1 \
        libgsm1 \
        libgsm1-dev \
        libspeex-dev \
        libspeexdsp-dev \
        libssl-dev \
        libssl3 \
        zlib1g \
        zlib1g-dev \
        default-libmysqlclient-dev
        
WORKDIR /
RUN git clone https://github.com/yatevoip/yate.git
WORKDIR /yate
RUN ./autogen.sh
RUN ./configure
RUN make

WORKDIR /
COPY docker/s6-overlay /etc/s6-overlay

FROM ghcr.io/hassio-addons/debian-base:7.8.3
SHELL [ "/bin/bash", "-euxo", "pipefail", "-c" ]

LABEL \
  io.hass.version="VERSION" \
  io.hass.type="addon" \
  io.hass.arch="armhf|aarch64|i386|amd64"

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
        default-libmysqlclient-dev \
        supervisor
        
WORKDIR /
RUN git clone https://github.com/yatevoip/yate.git
WORKDIR /yate
RUN ./autogen.sh
RUN ./configure
RUN make

WORKDIR /
COPY docker/supervisord.conf /etc/supervisord.conf
COPY docker/startup.sh /usr/local/bin/startup.sh

CMD ["/usr/local/bin/startup.sh"]
HEALTHCHECK CMD [ "supervisorctl", "status" ]

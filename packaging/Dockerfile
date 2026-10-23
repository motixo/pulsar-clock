FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential pkg-config python3 tzdata \
    libfontconfig1-dev libfreetype6-dev libxkbcommon-dev libwayland-dev \
    libinput-dev libudev-dev libegl1-mesa-dev libdbus-1-dev \
    && rm -rf /var/lib/apt/lists/*
ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup.sh \
    && sh /tmp/rustup.sh -y --profile minimal --default-toolchain 1.93 \
    && rm /tmp/rustup.sh
ENV PATH=/opt/cargo/bin:$PATH
RUN useradd --create-home --uid 1000 builder
USER builder
ENV CARGO_HOME=/build/cargo CARGO_TARGET_DIR=/build/target CARGO_BUILD_JOBS=6
WORKDIR /source

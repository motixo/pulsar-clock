Prebuilt COSMIC Clock for Linux x86_64, based on COSMIC `epoch-1.9.0`.

- Bold clock text, seconds, 12/24-hour time, custom separators, and HEX colors.
- The default date/time separator is a bullet with surrounding spaces: ` • `.
- Ready-made binary built on Ubuntu 22.04; requires glibc 2.35 or newer and the shared libraries used by COSMIC.
- Download `cosmic-clock-linux-x86_64.tar.gz`, extract it, and run `./install.sh`. Python 3.9+ is needed for installation; Rust and a compiler are optional.
- `./install.sh` from a Git checkout downloads and verifies the binary release by default.
- `./install.sh --from-source` remains available for building locally.
- `./uninstall.sh` restores the stock clock; `--purge` also removes custom settings and cache.

`SHA256SUMS` contains checksums for both downloads. The matching patched source and build tools are in `cosmic-clock-v0.1.0-source.tar.gz`.

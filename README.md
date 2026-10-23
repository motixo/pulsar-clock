# Pulsar Clock

Extra clock preferences for the COSMIC desktop: bold text, seconds, 12/24-hour time, a custom date/time separator, and HEX text colors.

![Clock preferences on a COSMIC desktop](assets/screenshot.png)

A separate per-user applet keeps your customization across system package updates.

## Features

- Bold clock and date text.
- Show or hide seconds.
- Switch between 12-hour and 24-hour time.
- Choose a date/time separator. The default is ` • `, with a space on each side.
- Set the text color with a 3-digit or 6-digit HEX code, with or without `#`.
- Apply and save preferences immediately from the clock's own menu.

Turning off **Custom text color** restores the theme color. Incomplete or invalid HEX input keeps the last valid color applied. The separator applies to horizontal panels; vertical panels keep their stacked layout and support bold text and custom colors.

## Easy install: ready-made binary

The prebuilt release targets **Linux x86_64**, **glibc 2.35 or newer**, and **COSMIC 1.9.0**. Python 3.9+ and the runtime libraries used by COSMIC are needed. Rust, Cargo, and a C compiler are optional.

Download the archive from [Releases](https://github.com/motixo/pulsar-clock/releases/latest), or run:

```sh
curl -fLO https://github.com/motixo/pulsar-clock/releases/latest/download/pulsar-clock-linux-x86_64.tar.gz
tar -xzf pulsar-clock-linux-x86_64.tar.gz
cd pulsar-clock
./install.sh
```

The archive contains the compiled clock, installer, and uninstaller. Installation verifies the binary checksum and checks that the executable can run before changing the installed clock. Run it as your normal desktop user, without `sudo`.

Click the panel clock, then **Clock preferences…**. If your panel did not already contain a clock, add **Pulsar Clock** through the panel's applet settings.

The first installation copies your existing stock clock preferences and uses the bullet separator by default. Later installations preserve your custom preferences. Use `./install.sh --no-activate` to install without changing the current panel applets.

`SHA256SUMS` is included with each release for verifying the downloaded archives. The patched source used to build the binary is published alongside it.

## Build it yourself

The patch is based on upstream [`epoch-1.9.0`](https://github.com/pop-os/cosmic-applets/tree/epoch-1.9.0) and has been tested on Arch Linux with `cosmic-applets` 1.9.0. The prebuilt binary uses an Ubuntu 22.04 build environment.

On Arch, install the build tools:

```sh
sudo pacman -S --needed git rust base-devel python
```

Then build and install:

```sh
git clone https://github.com/motixo/pulsar-clock.git
cd pulsar-clock
./install.sh --from-source
```

This detects the installed Arch package version, downloads the matching upstream source, checks and applies the patch, runs the clock tests, and builds the applet using Cargo.lock.

On other distributions, install Git, Python 3.9+, Cargo/Rust, a C compiler, pkg-config, and the development libraries for Wayland, libxkbcommon, libinput, fontconfig, FreeType, and D-Bus. Select the upstream version explicitly:

```sh
./install.sh --from-source --ref epoch-1.9.0
```

Build dependencies and the Rust toolchain must satisfy the selected upstream release. Other upstream versions have not been tested. Internet access is needed to fetch source and Cargo dependencies.

### Source build options

```sh
./install.sh --from-source --ref epoch-1.9.0 --build-only
./install.sh --from-source --ref epoch-1.9.0 --no-activate
```

- `--ref TAG`: select an upstream tag or branch instead of Arch version detection.
- `--build-only`: build and test without installing.
- `--no-activate`: install without changing the current panel applets.

Set `CARGO_BUILD_JOBS` to change the default of six parallel jobs, or an absolute `CARGO_TARGET_DIR` to reuse a build directory.

An existing `format_strftime` override takes precedence over the normal format controls. **Use normal date/time formatting** in the clock preferences clears that override.

## Update

From a Git checkout:

```sh
git pull --ff-only
./install.sh
```

Or download and install the latest binary archive again. Existing preferences are preserved. The installer leaves the active clock running; the new executable takes effect on the next login or panel reload.

A future incompatible COSMIC panel API may require an updated release or an adapted source patch. Failed downloads, checksums, runtime checks, patch checks, and builds leave the installed executable in place.

## Uninstall

```sh
./uninstall.sh
```

This restores the stock clock in the panel and removes the custom executable and desktop entry. Custom preferences and caches are kept for a later reinstall. To remove those too:

```sh
./uninstall.sh --purge
```

Panel backups are retained under `~/.local/state/pulsar-clock/backups/`. When the panel is not running, the restored selection is used on the next login.

To switch back temporarily while keeping the custom applet installed, run `python3 scripts/clock-control.py restore`. Use `python3 scripts/clock-control.py activate` to switch back to Pulsar Clock, or `python3 scripts/clock-control.py status` to inspect the current selection and process.

## Installed files

| Purpose | Default location |
| --- | --- |
| Executable | `~/.local/bin/pulsar-clock` |
| Desktop entry | `~/.local/share/applications/io.github.motixo.PulsarClock.desktop` |
| Preferences | `~/.config/cosmic/io.github.motixo.PulsarClock/v1/` |
| Source and build cache | `~/.cache/pulsar-clock/` |
| Panel backups | `~/.local/state/pulsar-clock/backups/` |

Configuration, data, cache, and state paths respect their corresponding XDG environment variables. System package files stay unchanged.

## Development and release builds

```sh
python3 -m unittest discover -s tests -v
bash -n install.sh build-from-source.sh uninstall.sh scripts/build-release.sh
```

Installer tests run in temporary directories and cover install/uninstall behavior, preserving settings and processes, checksum validation, runtime compatibility, and safe reading of binary archives. The source patch includes clock formatting and color tests.

To create binary and source release archives using Docker:

```sh
./scripts/build-release.sh ./dist
```

The **Build binary release** GitHub Actions workflow performs the same build and publishes the version from `release.json`. Update the version before publishing a new release.

## License and upstream

[GPL-3.0-only](LICENSE). Based on [System76's cosmic-applets](https://github.com/pop-os/cosmic-applets). See [NOTICE](NOTICE) for the tested base commit and attribution.

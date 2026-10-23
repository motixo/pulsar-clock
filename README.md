# COSMIC Clock

Extra clock preferences for the COSMIC desktop: bold text, seconds, 12/24-hour time, a custom date/time separator, and HEX text colors.

![Clock preferences on a COSMIC desktop](assets/screenshot.png)

[راهنمای فارسی](README.fa.md)

This patch installs a separate applet in your home directory. Your customization stays in place when the system's `cosmic-applets` package is updated.

## Features

- Bold clock and date text.
- Show or hide seconds.
- Switch between 12-hour and 24-hour time.
- Choose the date/time separator, including spaces and Unicode characters.
- Set the text color with a 3-digit or 6-digit HEX code, with or without `#`.
- Apply and save preferences immediately from the clock's own menu.

Turning off **Custom text color** restores the theme's text color. Incomplete or invalid HEX input keeps the last valid color applied.

The separator applies to horizontal panels. Vertical panels keep their stacked layout and support bold text and custom colors.

## Install

Tested on **Arch Linux with `cosmic-applets` 1.9.0**. The patch is based on upstream [`epoch-1.9.0`](https://github.com/pop-os/cosmic-applets/tree/epoch-1.9.0).

On Arch, install the build tools:

```sh
sudo pacman -S --needed git rust base-devel
```

Then, as your normal desktop user:

```sh
git clone https://github.com/motixo/cosmic-clock.git
cd cosmic-clock
./install.sh
```

The installer detects the installed Arch package version, downloads the matching upstream source, checks and applies the patch, runs the clock tests, and builds the applet. It copies your original clock preferences on the first installation and switches existing stock clock entries to **Custom Clock**.

Click the panel clock, then **Clock preferences…**. If your panel did not already contain a clock, add **Custom Clock** through the panel's applet settings.

On other distributions, install Git, Python 3.9 or newer, Cargo/Rust, a C compiler, `pkg-config`, and the development libraries for Wayland, libxkbcommon, libinput, fontconfig, FreeType, and D-Bus. Pass the matching upstream reference explicitly:

```sh
./install.sh --ref epoch-1.9.0
```

Other distributions and upstream versions have not been tested here. Build dependencies and the Rust toolchain must satisfy the selected upstream release. Internet access is needed to download the source and Cargo dependencies.

### Installer options

```sh
./install.sh --ref epoch-1.9.0 --build-only
./install.sh --ref epoch-1.9.0 --no-activate
```

- `--ref TAG`: select an upstream tag or branch instead of Arch version detection.
- `--build-only`: build and test without installing.
- `--no-activate`: install without changing the current panel applets.

Use `CARGO_BUILD_JOBS` to change the default of six parallel jobs, or an absolute `CARGO_TARGET_DIR` to reuse a build directory.

If you have an existing `format_strftime` override, **Use normal date/time formatting** in the clock preferences clears it so the regular format controls can take effect.

## Update

```sh
git pull --ff-only
./install.sh
```

Existing preferences are preserved. A rebuild leaves the running clock alive; the new executable takes effect on the next login or panel reload.

The patch is checked before installation. If a future COSMIC release changes the relevant source or panel API, the patch may need to be adapted. A failed patch check or build leaves the installed executable in place.

## Uninstall

```sh
./uninstall.sh
```

This restores the stock clock in the panel and removes the custom executable and desktop entry. Custom preferences and the build cache are kept for a later reinstall.

To remove those too:

```sh
./uninstall.sh --purge
```

Panel configuration backups are retained under `~/.local/state/cosmic-clock-custom/backups/`. If the panel is not running, its restored clock selection is used on the next login.

To switch back temporarily while keeping the custom applet installed:

```sh
python3 scripts/clock-control.py restore
python3 scripts/clock-control.py activate
```

Run one command for the direction you want. Check the current selection and running processes with:

```sh
python3 scripts/clock-control.py status
```

## Installed files

| Purpose | Default location |
| --- | --- |
| Executable | `~/.local/bin/cosmic-clock-custom` |
| Desktop entry | `~/.local/share/applications/io.github.motixo.CosmicClock.desktop` |
| Preferences | `~/.config/cosmic/io.github.motixo.CosmicClock/v1/` |
| Source and build cache | `~/.cache/cosmic-clock-custom/` |
| Panel backups | `~/.local/state/cosmic-clock-custom/backups/` |

The configuration, data, cache, and state paths respect their corresponding XDG environment variables. System package files are left unchanged.

## Development and checks

```sh
python3 -m unittest discover -s tests -v
bash -n install.sh uninstall.sh
```

The six installer tests use temporary directories and do not change your desktop. They cover first installation, activation, preservation of existing preferences and running processes, uninstallation, and purging.

The patch also adds clock tests for formatting, HEX validation, theme fallback, and 12/24-hour boundaries. `install.sh` runs these before building. GitHub Actions checks the scripts, installer tests, and whether the patch applies to the supported base release.

## License and upstream

[GPL-3.0-only](LICENSE). Based on [System76's cosmic-applets](https://github.com/pop-os/cosmic-applets). See [NOTICE](NOTICE) for the tested base commit and attribution.

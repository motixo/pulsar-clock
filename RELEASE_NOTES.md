Separate custom text colors for dark and light panel themes.

- Two HEX fields in Clock preferences: Dark theme HEX color and Light theme HEX color.
- The clock follows the active panel theme automatically, including panel-specific appearance overrides.
- Existing single-color preferences keep the same color in both modes until changed.
- Switching Custom text colors off restores theme colors and preserves both saved choices.
- Incomplete or invalid edits keep the last valid color for that mode.

The Linux x86_64 binary targets COSMIC 1.9.0 and glibc 2.35 or newer.
Extract pulsar-clock-linux-x86_64.tar.gz and run ./install.sh.
The matching patched source is included as pulsar-clock-v0.2.0-source.tar.gz.
SHA256SUMS covers both archives.

# Underwood

A minimalist word processor for the terminal, designed for creative writing: novels, short stories, essays, and screenplays.Debian

## Command line installer (multidistro)

curl -fsSL https://raw.githubusercontent.com/SilvestreParbut/Underwood/main/underwood_2.6.7/install.sh | sudo bash

## Repository Structure

Each `underwood_X.Y.Z/` folder contains the complete Debian packaging tree for that version:

- `DEBIAN/` — installation metadata (`control`, `postinst`)
- `usr/` — files to be installed on the system (`/usr/bin`, `/usr/share`)

## Building the `.deb` Package

From the root of the repository:

dpkg-deb --build --root-owner-group underwood_X.Y.Z underwood_X.Y.Z_all.deb

Replace `X.Y.Z` with the version you wish to package.

## Installation

sudo apt install ./underwood_X.Y.Z_all.deb

## Dependencies

Python 3.8+, xterm, DejaVu fonts, hunspell (with ES and EN dictionaries), xclip.

## License

(see the LICENSE file)

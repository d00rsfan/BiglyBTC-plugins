# BiglyBTC-plugins

Release catalogue and compatibility metadata for BiglyBTC native plugins.

Each plugin is built and checked in its own repository. The
[azlocprov workflow](https://github.com/d00rsfan/BiglyBTC-plugin-azlocprov/actions/workflows/linux.yml)
builds the Ubuntu 26.04 amd64 update archive and a catalogue entry with the
exact source revision and asset SHA-256. The zip is a GitHub Actions download
containing the update archive.

The catalogue workflow checks the assembler on pushes to `master`.
Manual dispatch selects a successful azlocprov `master` push by run ID and
full commit. The assembled catalogue requires a new sequence greater than the
currently published sequence. It is an unsigned artifact for offline signing.
Publish the asset at its versioned release URL before publishing the matching
catalogue bytes and detached Ed25519 signature.

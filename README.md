# BiglyBTC-plugins

Package index and signed update catalogue for BiglyBTC native plugins.

The Ubuntu 26.04 amd64 builds retain versioned artifacts with a source
revision and SHA-256. The version uses the component version and the
workflow run number.

| Component | Build output |
| --- | --- |
| [azlocprov](https://github.com/d00rsfan/BiglyBTC-plugin-azlocprov/actions) | SDK module and signed-update catalogue input |
| [SpeedScheduler](https://github.com/d00rsfan/BiglyBTC-plugin-SpeedScheduler/actions) | SDK module for host integration |
| [azmsgsync](https://github.com/d00rsfan/BiglyBTC-plugin-azmsgsync/actions) | Envelope and STS static libraries and headers |
| [aznettor](https://github.com/d00rsfan/BiglyBTC-plugin-aznettor/actions) | SAFECOOKIE static library and header |
| [azrating](https://github.com/d00rsfan/BiglyBTC-plugin-azrating/actions) | Rating static library, headers and its pinned BiglyBTCCore dependency |
| [mlDHT](https://github.com/d00rsfan/BiglyBTC-plugin-mlDHT/actions) | DHT binding policy and identity static libraries and headers |
| [xmwebui](https://github.com/d00rsfan/BiglyBTC-plugin-xmwebui/actions) | RPC contract, identity and loopback HTTP static libraries and headers |

Static libraries are linked by the host at build time. Their archives
include the original-source provenance and license. The SpeedScheduler
archive includes the module for testing and integration with the SDK.
BiglyBTC currently bundles its own approved scheduler module.

## Signed update catalogue

The catalogue workflow checks the assembler on pushes to `master`.
Manual dispatch selects a successful azlocprov `master` push by run ID and
full commit. The assembled catalogue requires a sequence greater than the
currently published sequence. It is an unsigned artifact for offline signing.
Publish the asset at its versioned release URL before publishing the matching
catalogue bytes and detached Ed25519 signature.

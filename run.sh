#!/bin/sh
# Launch the real snork Rust server on $PORT. The arena pre-builds (cargo, see
# battlesnake.py _build_submissions); build here only if the binary is missing.
[ -x target/release/server ] || cargo build --release --bin server
exec target/release/server --host "0.0.0.0:${PORT:-8000}"

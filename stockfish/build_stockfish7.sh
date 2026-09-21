#!/usr/bin/env bash
# Builds Stockfish 7 (pre-NNUE, classical evaluation) from official source.
#
# Sentinel's Regan-style statistical layer is only comparable to Kenneth
# Regan's published calibration tables when analysis runs on the same
# evaluation function he calibrated against. Stockfish switched from a
# classical hand-crafted evaluation to NNUE (neural network evaluation)
# starting around Stockfish 12 (2020), which changed centipawn-loss
# distributions enough to break that calibration. Do not swap in a newer
# Stockfish for the Regan-comparability path without new correspondence
# constants from Regan.
#
# Usage: ./build_stockfish7.sh
# Output: ./bin/stockfish-7

set -euo pipefail
cd "$(dirname "$0")"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

git clone --depth 1 --branch sf_7 https://github.com/official-stockfish/Stockfish.git "$WORKDIR/Stockfish"
cd "$WORKDIR/Stockfish/src"

if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
  # No arm64 target existed in the 2016-era Makefile; Stockfish 7 has no
  # NEON port. Build the x86-64 target and let Rosetta 2 run it.
  arch -x86_64 make build ARCH=x86-64-modern COMP=clang
else
  make build ARCH=x86-64-modern COMP=clang
fi

mkdir -p "$(dirname "$0")/bin"
cp stockfish "$(dirname "$0")/bin/stockfish-7"
chmod +x "$(dirname "$0")/bin/stockfish-7"
echo "Built: $(dirname "$0")/bin/stockfish-7"
"$(dirname "$0")/bin/stockfish-7" --help >/dev/null 2>&1 || true
echo "uci" | "$(dirname "$0")/bin/stockfish-7" | head -2

#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$PROJECT_ROOT/scripts/check_board.py" --strict
# Use JetPack's installed CUDA/TensorRT and stock compiler for this legacy project.
test -x /usr/local/cuda/bin/nvcc
sudo apt-get update
sudo apt-get install -y build-essential git cmake wget ca-certificates libglew-dev glew-utils \
 gstreamer1.0-libav gstreamer1.0-nice libgstreamer1.0-dev libgstrtspserver-1.0-dev \
 libglib2.0-dev libsoup2.4-dev libjson-glib-dev qtbase5-dev avahi-utils \
 libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
 libgstreamer-plugins-bad1.0-dev libpython3-dev python3-numpy
cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/scripts/checkout_source.sh"
mkdir -p .vendor
if [[ ! -e .vendor/jetson-inference && -f sources/jetson-inference.tar.gz ]]; then
  sha256sum -c sources/jetson-inference.tar.gz.sha256
  tar -xzf sources/jetson-inference.tar.gz -C .vendor
fi
if [[ ! -e .vendor/jetson-inference || -d .vendor/jetson-inference/.git ]]; then
  checkout jetson-inference https://github.com/dusty-nv/jetson-inference.git 45da40a8f3c180191b269f57f736caaa025b8a69
  # Also retry an interrupted submodule download on subsequent runs.
  git -C .vendor/jetson-inference submodule update --init --recursive --depth 1
fi
# Disable upstream auto-installers, which otherwise attempt unpinned pip upgrades.
CMAKE_BIN="$PROJECT_ROOT/.tools/cmake/bin/cmake"
[[ -x "$CMAKE_BIN" ]] || CMAKE_BIN="$(command -v cmake)"
mkdir -p .vendor/jetson-inference/build
cd .vendor/jetson-inference/build
"$CMAKE_BIN" .. \
 -DBUILD_DEPS=NO -DBUILD_INTERACTIVE=NO -DBUILD_EXPERIMENTAL=NO
"$CMAKE_BIN" --build . -- -j"${JOBS:-2}"
sudo "$CMAKE_BIN" --build . --target install
sudo ldconfig
/usr/bin/python3 -c 'import jetson_inference, jetson_utils; print("Vision bindings imported")'

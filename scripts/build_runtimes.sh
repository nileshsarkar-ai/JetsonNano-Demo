#!/usr/bin/env bash
# CPU-only runtimes for the original Nano. Run after install_system.sh.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOBS="${JOBS:-2}"
python3 "$PROJECT_ROOT/scripts/check_board.py" --strict
command -v gcc-8 >/dev/null
command -v g++-8 >/dev/null
mkdir -p "$PROJECT_ROOT/.vendor" "$PROJECT_ROOT/.tools"

checkout() {
  local name="$1" url="$2" revision="$3"
  local dest="$PROJECT_ROOT/.vendor/$name"
  if [[ -e "$dest" ]]; then
    [[ "$(git -C "$dest" rev-parse HEAD)" == "$revision" ]] || { echo "Wrong revision in $dest" >&2; exit 1; }
    [[ -z "$(git -C "$dest" status --porcelain --untracked-files=no)" ]] || { echo "Modified source in $dest" >&2; exit 1; }
  else
    git init -q "$dest"
    git -C "$dest" remote add origin "$url"
    git -C "$dest" fetch --depth 1 origin "$revision"
    git -C "$dest" checkout --detach FETCH_HEAD
  fi
}

# Stock Ubuntu 18.04 CMake is too old for this pinned llama.cpp.
# Build a private CMake only when no suitable version is present.
CMAKE_BIN="$PROJECT_ROOT/.tools/cmake/bin/cmake"
if [[ ! -x "$CMAKE_BIN" ]]; then
  if command -v cmake >/dev/null && python3 -c 'import subprocess; v=subprocess.check_output(["cmake","--version"]).decode().split()[2]; raise SystemExit(tuple(map(int,v.split(".")[:2])) < (3,14))'; then
    CMAKE_BIN="$(command -v cmake)"
  else
    checkout cmake-source https://github.com/Kitware/CMake.git 0bfd4f1ed68180d3912386fb53d559b2a9e84b1b
    (cd "$PROJECT_ROOT/.vendor/cmake-source"
     ./bootstrap --prefix="$PROJECT_ROOT/.tools/cmake" --parallel="$JOBS" -- -DCMAKE_USE_OPENSSL=OFF
     make -j"$JOBS"
     make install)
  fi
fi
checkout llama.cpp https://github.com/ggml-org/llama.cpp.git 23106f94ea2bc3da929afb7330655fd5515d08dc
checkout whisper.cpp https://github.com/ggml-org/whisper.cpp.git 7395c70a748753e3800b63e3422a2b558a097c80
checkout llama2.c https://github.com/karpathy/llama2.c.git 350e04fe35433e6d2941dce5a1f53308f87058eb

"$CMAKE_BIN" -S "$PROJECT_ROOT/.vendor/llama.cpp" -B "$PROJECT_ROOT/.vendor/llama.cpp/build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc-8 -DCMAKE_CXX_COMPILER=g++-8 \
  -DCMAKE_CXX_STANDARD_LIBRARIES=-lstdc++fs \
  -DGGML_CUDA=OFF -DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH=armv8-a \
  -DGGML_OPENMP=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=ON
"$CMAKE_BIN" --build "$PROJECT_ROOT/.vendor/llama.cpp/build" --target llama-server llama-cli llama-bench llama-quantize -- -j"$JOBS"

"$CMAKE_BIN" -S "$PROJECT_ROOT/.vendor/whisper.cpp" -B "$PROJECT_ROOT/.vendor/whisper.cpp/build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc-8 -DCMAKE_CXX_COMPILER=g++-8 \
  -DWHISPER_CUDA=OFF -DWHISPER_BUILD_TESTS=OFF -DBUILD_SHARED_LIBS=OFF
"$CMAKE_BIN" --build "$PROJECT_ROOT/.vendor/whisper.cpp/build" --target main -- -j"$JOBS"
gcc-8 -O3 -fopenmp "$PROJECT_ROOT/.vendor/llama2.c/run.c" -lm -o "$PROJECT_ROOT/.vendor/llama2.c/run"
echo "CPU runtimes built. No CUDA or Python installation was replaced."

#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ANDROID_DIR="${SCRIPT_DIR}/../android"

echo "Building and installing Saarathi debug APK on connected Android device..."
cd "${ANDROID_DIR}"

if [ -f "./gradlew" ]; then
    ./gradlew installDebug
else
    gradle installDebug
fi

echo "Launching Saarathi MainActivity..."
adb shell am start -n com.saarathi.app/.MainActivity
echo "Saarathi successfully launched on device!"

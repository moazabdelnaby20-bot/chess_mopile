[app]

title = Chess Heroes
package.name = chessheroes
package.domain = org.example
source.dir = .
source.include_exts = py,ttf,txt
version = 0.1.0
requirements = python3,kivy,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0

# Use a stable Android target for Python-for-Android. The prior combination
# (API 35 + NDK r28c) triggered CPython build failures with preadv/pwritev,
# which are not correctly exposed by that toolchain combination.
android.api = 31
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1

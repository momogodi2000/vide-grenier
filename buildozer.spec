[app]
title = Vidé-Grenier Kamer
package.name = vgk
package.domain = com.videgrenier.kamer
source.dir = E:\project\vide-grenier\vide\kivy_app
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js
version = 1.0.0

requirements = python3,kivy,requests,urllib3

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 28
android.minapi = 21
android.ndk = 23b
android.sdk = 28
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1

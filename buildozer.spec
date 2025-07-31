[app]

# (str) Title of your application
title = Vidé-Grenier Kamer

# (str) Package name
package.name = vgk

# (str) Package domain (needed for android/ios packaging)
package.domain = com.videgrenierkamer

# (str) Source code where the main.py live
source.dir = kivy_app

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.2.1,requests,urllib3,certifi,charset-normalizer,idna,plyer

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WAKE_LOCK,VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be shown the license when first running
# buildozer.
android.accept_sdk_license = True

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk or aar).
android.release_artifact = aab

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# iOS specific
#

# (str) Path to your iOS developer identity
#ios.codesign.identity = iPhone Developer: <lastname> <firstname> (<hexstring>)

# (str) The display name of the application (can be changed during packaging)
#ios.display_name = My First Application

# (str) The name of your application's main folder (e.g. 'MyApp')
#ios.app_name = MyApp

# (str) Path to the Kivy icon
#ios.icon.filename = %(source.dir)s/data/icon.png

# (str) Path to the iOS static libs that will be used in the project
#ios.static_libs = %(source.dir)s/libs

# (list) iOS application plist files to merge
#ios.info_plist = %(source.dir)s/Info.plist

# (list) iOS additional plist files to merge
#ios.extra_plist = %(source.dir)s/extra.plist

# (list) iOS external frameworks to add
#ios.frameworks = AudioToolbox, ImageIO, SystemConfiguration

# (list) iOS weak frameworks to add
#ios.weak_frameworks = Contacts, Social, iAd

# (list) iOS libraries to add
#ios.libraries = iconv, sqlite3

# (list) iOS plugins to add
#ios.plugins = MyPlugin

# (list) iOS prebuild plugins to add
#ios.prebuilt_plugins = MyPlugin

# (list) iOS additional entitlements to add
#ios.entitlements = MyApp.entitlements

#
# Apple TV specific
#

# (str) Path to the icon
#tvos.icon.filename = %(source.dir)s/data/icon.png

# (str) Path to the top level app directory
#tvos.app_dir = %(source.dir)s

# (str) Application name
#tvos.app_name = %(app.title)s

# (str) Application version
#tvos.version = %(app.version)s

# (str) Application bundle identifier
#tvos.bundle_identifier = %(app.package.domain)s.%(app.package.name)s

# (str) Path to the entitlements file
#tvos.entitlements = %(source.dir)s/entitlements.plist

# (str) Path to the Info.plist file
#tvos.info_plist = %(source.dir)s/Info.plist

# (str) Path to the main file
#tvos.main_file = %(source.dir)s/main.py

# (str) Path to the provisioning profile
#tvos.provisioning_profile = %(source.dir)s/profile.mobileprovision

# (str) Team identifier
#tvos.team_identifier = <team_identifier>

# (str) TVOS Deploy Target
#tvos.deployment_target = 9.1

# (bool) Indicate if the application should be fullscreen or not
#tvos.fullscreen = 1

# (bool) Indicate that the application should support background playback
#tvos.background_modes = audio

#
# tvOS specific
#

# (str) Path to the icon
#tvos.icon.filename = %(source.dir)s/data/icon.png

# (str) Path to the top level app directory
#tvos.app_dir = %(source.dir)s

# (str) Application name
#tvos.app_name = %(app.title)s

# (str) Application version
#tvos.version = %(app.version)s

# (str) Application bundle identifier
#tvos.bundle_identifier = %(app.package.domain)s.%(app.package.name)s

# (str) Path to the entitlements file
#tvos.entitlements = %(source.dir)s/entitlements.plist

# (str) Path to the Info.plist file
#tvos.info_plist = %(source.dir)s/Info.plist

# (str) Path to the main file
#tvos.main_file = %(source.dir)s/main.py

# (str) Path to the provisioning profile
#tvos.provisioning_profile = %(source.dir)s/profile.mobileprovision

# (str) Team identifier
#tvos.team_identifier = <team_identifier>

# (str) TVOS Deploy Target
#tvos.deployment_target = 9.1

# (bool) Indicate if the application should be fullscreen or not
#tvos.fullscreen = 1

# (bool) Indicate that the application should support background playback
#tvos.background_modes = audio

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#[app]
#source.exclude_patterns = license,data/audio/*.wav,data/images/original/*
#
#    This can be translated into:
#
#[app:source.exclude_patterns]
#license
#data/audio/*.wav
#data/images/original/*
#

#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the HD content.
#
#[app@demo]
#title = My Application (demo)
#
#[app:source.exclude_patterns@demo]
#images/hd/*
#
#    Then, invoke the command line with the "demo" profile:
#
#buildozer --profile demo android debug

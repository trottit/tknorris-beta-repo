#!/bin/sh

#rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/1Channel/ ~/eclipseworkspace/tknorris-beta-repo/plugin.video.1channel
#rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/salts/ ~/eclipseworkspace/tknorris-beta-repo/plugin.video.salts
#rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/plugin.video.trakt_list_manager/ ~/eclipseworkspace/tknorris-beta-repo/plugin.video.trakt_list_manager
#rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/1channel.themepaks/ ~/eclipseworkspace/tknorris-beta-repo/script.1channel.themepak
rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/script.trakt/ ~/eclipseworkspace/tknorris-beta-repo/script.trakt
rsync --delete -av --exclude=".*" --exclude="*.pyc" ~/eclipseworkspace/script.module.trakt/ ~/eclipseworkspace/tknorris-beta-repo/script.module.trakt
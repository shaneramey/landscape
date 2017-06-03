#! /usr/bin/env bash

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

gcloud container clusters create $GIT_BRANCH
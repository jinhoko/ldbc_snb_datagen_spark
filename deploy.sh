#!/bin/bash

set -e # exit with nonzero exit code if anything fails

# clear and re-create the directory
rm -rf deployed || exit 0
mkdir deployed

# create md5sum files
cd substitution_parameters
md5sum interactive* > md5-interactive.chk
md5sum bi* > md5-bi.chk

# copy dir
cp -r substitution_parameters deployed/

# go to the directory and create a *new* Git repo
cd deployed
git init

# inside this git repo we'll pretend to be a new user
git config user.name "FTSRG BME"
git config user.email "ftsrg.bme@gmail.com"

# The first and only commit to this new Git repo contains all the
# files present with the commit message "Deploy to GitHub Pages".
git add .
git commit -m "Deploy to GitHub Pages"

# Force push from the current repo's master branch to the remote
# repo's gh-pages branch. (All previous history on the gh-pages branch
# will be lost, since we are overwriting it.) We redirect any output to
# /dev/null to hide any sensitive credential data that might otherwise be exposed.
git push --force --quiet "https://${GH_TOKEN}@${GH_REF}" master:gh-pages > /dev/null 2>&1

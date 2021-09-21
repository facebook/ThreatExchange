#!/bin/sh

if [[ $# -ne 2 ]] ; then
  echo "Usage: git-split.sh original copy"
  exit 0
fi

git mv $1 $2
git commit -n -m "Split history $1 to $2"
REV=`git rev-parse HEAD`
git reset --hard HEAD^
git mv $1 temp
git commit -n -m "Split history $1 to $2"
git merge $REV
git commit -a -n -m "Split history $1 to $2"
git mv temp $1
git commit -n -m "Split history $1 to $2"

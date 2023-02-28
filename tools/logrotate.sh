#!/bin/bash
# Weekly rotate for logs, add any number of logs needed
logs=("info.log" "error.log" "test.log")

dir="$(dirname "$0")/../log/"
destdir="$(dirname "$0")/../log/"
dow=$(date +%u)
today=$(date +%y%m%d)

for log in ${logs[@]}; do
  logname="$dir""$log"
  archive="$destdir""$log"_"$today"
  if [ $dow -eq "7" ]; then
      if test -f "$logname"; then
        mv $logname $archive
      fi
  fi
done
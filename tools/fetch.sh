#!/bin/bash
dir="$(dirname "$0")"

python3 $dir/price.py -t1
if [ $? == 1 ]
  then
  python3 $dir/nord.py -t1
fi

python3 $dir/price.py -t2
if [ $? == 1 ]
  then
  python3 $dir/nord.py -t2
fi

python3 $dir/fmi_parser.py
bash $dir/logrotate.sh
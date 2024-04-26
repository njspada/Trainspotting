#!/bin/bash

# first restart nvargus-daemon.service
systemctl restart nvargus-daemon.service

# then clear cache
if [ "$1" == 'page' ];then
        echo "Clearing page cache."
        echo 1 > /proc/sys/vm/drop_caches
else
        echo "Clearing all* cache."
        echo 3 > /proc/sys/vm/drop_caches
fi
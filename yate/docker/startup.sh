#!/bin/sh
rm -r /yate/conf.d
ln -s /config /yate/conf.d

/usr/bin/supervisord
#!/bin/sh
rm -r /yate/conf.d
ln -s /config /yate/conf.d

# Replace HASSIO_MYSQL_*
# if /config/mysqldb.conf exists.
if [ -f /config/mysqldb.conf ]; then
    sed -i "s/HASSIO_MYSQL_HOST/$(bashio::services mysql "host")/g" /config/mysqldb.conf
    sed -i "s/HASSIO_MYSQL_PORT/$(bashio::services mysql "port")/g" /config/mysqldb.conf
    sed -i "s/HASSIO_MYSQL_USER/$(bashio::config "mysql_user")/g" /config/mysqldb.conf
    sed -i "s/HASSIO_MYSQL_PASSWORD/$(bashio::config "mysql_password")/g" /config/mysqldb.conf
    sed -i "s/HASSIO_MYSQL_DB/$(bashio::config "mysql_db")/g" /config/mysqldb.conf
fi

/usr/bin/supervisord
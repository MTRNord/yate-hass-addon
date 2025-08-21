#!/usr/bin/env bashio
rm -r /yate/conf.d
ln -s /config /yate/conf.d

# Replace MySQL configuration values
# if /config/mysqldb.conf exists.
if [ -f /config/mysqldb.conf ]; then
    sed -i "s/^host=.*/host=$(bashio::services mysql "host")/g" /config/mysqldb.conf
    sed -i "s/^port=.*/port=$(bashio::services mysql "port")/g" /config/mysqldb.conf
    sed -i "s/^user=.*/user=$(bashio::config "mysql_user")/g" /config/mysqldb.conf
    sed -i "s/^password=.*/password=$(bashio::config "mysql_password")/g" /config/mysqldb.conf
    sed -i "s/^database=.*/database=$(bashio::config "mysql_db")/g" /config/mysqldb.conf
fi

/usr/bin/supervisord
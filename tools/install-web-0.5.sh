#!/bin/sh


# Just For RedHat/CentOS

if [ ! -f /etc/redhat-release ]; then
    echo "Just support RedHat/CentOS distribution now."
    exit 1
fi

# arch must be x86_64
if [ $(arch) != "x86_64" ]; then
    echo "Your arch is $(arch), but I need x86_64 !"
    exit 1
fi

# Need root

if [ $UID -ne 0 ]; then
    echo "Need root to run install"
    exit 1
fi


# default DB for luoyun web
DBNAME=luoyun
DBUSER=luoyun
DBPASS=luoyun

LUOYUNTOP=/opt/LuoYun
MANAGEWEB=${LUOYUNTOP}/web/manage.py

function myexit()
{
    [ -n "$1" ] && echo "$1"
    exit 1
}

function create_db()
{
    if ! service postgresql status &> /dev/null ; then
        if ! service postgresql start &> /dev/null ; then
            echo "Preparing DB. It may take upto a few minutes. Please wait..."
            service postgresql initdb || myexit "  => [EE] postgresql initdb failed !"
            # Update auth of postgres for local user
            sed -i '/^local.*all.*all.*ident/s@ident@trust@' /var/lib/pgsql/data/pg_hba.conf
            sed -i '/^host *all *all *127.0.0.1\/32 *ident/s@ident@trust@' /var/lib/pgsql/data/pg_hba.conf
            service postgresql start || myexit "  => [EE] postgresql start failed !"
            sleep 5
        fi
    fi

    echo "Create DB User"
    if ! su - postgres -c "psql -c '\dg'" | grep ${DBUSER} > /dev/null 2>&1; then
        if su - postgres -c "createuser -P ${DBUSER}"; then
            echo "  => [DD] create user ${DBUSER} succeed"
        else
            myexit "  => [EE] create user ${DBUSER} failed !"
        fi
    else
        echo "  => [WW] user ${DBUSER} exist already !"
    fi

    echo "Create DB ${DBNAME}"
    if ! su - postgres -c 'psql -l' | grep ${DBNAME} > /dev/null 2>&1; then
        if su - postgres -c "createdb ${DBNAME} -O ${DBUSER}"; then
            echo "  => [DD] create ${DBNAME} succeed"
        else
            myexit "  => [EE] create DB ${DBNAME} failed !"
        fi
    else
        echo "  => [WW] ${DBNAME} exist already !"
    fi

    python $MANAGEWEB || myexit "  => [EE] init luoyun DB failed !"
}

create_db


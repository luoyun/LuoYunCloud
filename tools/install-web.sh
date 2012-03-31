#!/bin/sh


if [ $UID -ne 0 ]; then
    echo "Need root to run install"
    exit 1
fi

# Just For RedHat/CentOS

if [ ! -f /etc/redhat-release ]; then
    echo "Just support redhat distribution now."
    exit 1
fi


# default DB for luoyun web
DBNAME=luoyun
DBUSER=luoyun
DBPASS=luoyun

SCHEMA_SQL=schema.sql


# RPM_LIST
RPM_LIST="postgresql-server python-psycopg2"
# prepare requires
function prepare_env()
{
    NOT_EXIST_RPMS=""
    for RPM in $RPM_LIST; do
        if ! rpm -q ${RPM} > /dev/null 2>&1; then
            echo "  => ${RPM} not found"
            NOT_EXIST_RPMS="${NOT_EXIST_RPMS} ${RPM}"
        fi
    done

    # try install
    if [ -n "$NOT_EXIST_RPMS" ]; then
        if ! yum install $NOT_EXIST_RPMS; then
            exit 1
        fi
    fi


    if ! service postgresql status; then
        if ! service postgresql start; then
            service postgresql initdb
            service postgresql start
        fi
    fi

}

function create_db()
{

    echo "Create DB User"
    if ! su - postgres -c "psql -c '\dg'" | grep ${DBUSER} > /dev/null 2>&1; then
        
        if su - postgres -c "createuser -P ${DBUSER}"; then
            echo "  => [DD] create user ${DBUSER} succeed"
        else
            echo "  => [EE] create user ${DBUSER} failed !"
            exit 1
        fi

    else

        echo "  => [WW] user ${DBUSER} exist already !"

    fi

    echo "Create DB ${DBNAME}"
    if su - postgres -c 'psql -l' | grep ${DBNAME} > /dev/null 2>&1; then
        echo "  => [WW] ${DBNAME} exist already !"
    else
        if su - postgres -c "createdb ${DBNAME} -O ${DBUSER}"; then
            echo "  => [DD] create ${DBNAME} succeed"
        fi
    fi

    # Update auth of postgres for local user
    sed -i '/^local.*all.*all.*ident/s@ident@trust@' /var/lib/pgsql/data/pg_hba.conf

    service postgresql restart

    if [ ! -f $SCHEMA_SQL ]; then
        echo "$SCHEMA_SQL not exist !"
        exit 1
    fi

    if su postgres -c "psql -d ${DBNAME} -U ${DBUSER} -f ${SCHEMA_SQL}"; then
        echo "Use ${SCHEMA_SQL} init ${DBNAME} succeed ."
    else
        echo "Use ${SCHEMA_SQL} init ${DBNAME} failed !"
    fi
    
}


function common_install()
{
    prepare_env
    create_db
}

function install_rhel5()
{
    echo "Install LuoYun web console on redhat 5 series"
    common_install
}


function install_rhel6()
{
    echo "Install LuoYun web console on redhat 6 series"
    common_install
}


# For 5
if cat /etc/redhat-release | grep 5 > /dev/null 2>&1; then
    install_rhel5
    exit 0
fi


# For 6
if cat /etc/redhat-release | grep 6 > /dev/null 2>&1; then
    install_rhel6
    exit 0
fi


# Could not come here
echo "Just support redhat/centos 5 or 6 series"
exit 2

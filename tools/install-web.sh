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

LUOYUNTOP=/opt/LuoYun/
TOPDIR=${PWD}
SCHEMA_SQL="${TOPDIR}/web/tool/schema.sql"

DISTRIBUTION=


unalias cp > /dev/null 2>&1


# RPM_LIST
RPM_LIST="postgresql-server python-psycopg2 python-imaging"
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
        return
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

    TMP_SCHEMA=/tmp/schema.sql
    cp ${SCHEMA_SQL} $TMP_SCHEMA
    chmod 777 $TMP_SCHEMA
    if su postgres -c "psql -d ${DBNAME} -U ${DBUSER} -f $TMP_SCHEMA"; then
        echo "Use ${SCHEMA_SQL} init ${DBNAME} succeed ."
    else
        echo "Use ${SCHEMA_SQL} init ${DBNAME} failed !"
    fi
    
}

function install_nginx()
{
    [ -d $LUOYUNTOP/bin/ ] || mkdir $LUOYUNTOP/bin/

    # TODO: for x86_64 now
    cp $TOPDIR/nginx/nginx-x86_64-RHEL6 $LUOYUNTOP/bin/nginx

    [ -f /etc/nginx ] || cp -rf $TOPDIR/nginx/etc/nginx /etc/

    [ -d /var/log/nginx/ ] || mkdir /var/log/nginx/
    [ -d /var/spool/nginx/ ] || mkdir /var/spool/nginx/

    WEB_USER=http
    WEB_GROUP=http

    if id $WEB_USER > /dev/null 2>&1 ; then
        echo "  => $WEB_USER account exist."
    else
        echo "  => create $WEB_USER account."
        getent group $WEB_GROUP >/dev/null || groupadd -g 51 -r $WEB_GROUP
        getent passwd $WEB_USER >/dev/null || \
            useradd -r -u 51 -g $WEB_GROUP -s /sbin/nologin \
            -d /var/www -c "Http" $WEB_USER
    fi
}

function install_web()
{
    [ -d $LUOYUNTOP/web ] || cp -rf $TOPDIR/web $LUOYUNTOP/web

    chown -R ${WEB_USER}.${WEB_GROUP} /opt/LuoYun/web/static
}


function install_lyclc()
{
    echo "Install lyclc"

    if [[ "X$DISTRIBUTION" != "XRHEL5" && "X$DISTRIBUTION" != "XRHEL6" ]]; then
        echo "  => unsupported distribution: $DISTRIBUTION !"
        exit 1
    fi

    mkdir -pv ${LUOYUNTOP}/data/{appliance,upload}/ \
        ${LUOYUNTOP}/platform/bin/ \
        ${LUOYUNTOP}/platform/node_data/{appliances,instances} \
        ${LUOYUNTOP}/platform/etc/luoyun-cloud/ \
        ${LUOYUNTOP}/logs
        

    CLCDIR="${TOPDIR}/lyclc/${DISTRIBUTION}"

    cp ${CLCDIR}/etc/init.d/lyclcd /etc/init.d/
    cp ${CLCDIR}/opt/LuoYun/platform/etc/luoyun-cloud/lyclc.conf ${LUOYUNTOP}/platform/etc/luoyun-cloud/
    cp ${CLCDIR}/opt/LuoYun/platform/bin/lyclc ${LUOYUNTOP}/platform/bin/

    chkconfig --add lyclcd
    chkconfig --level 2345 lyclcd on
}


function common_install()
{
    prepare_env
    create_db
    install_nginx
    install_lyclc
    install_web
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
    DISTRIBUTION="RHEL5"
    install_rhel5
    exit 0
fi


# For 6
if cat /etc/redhat-release | grep 6 > /dev/null 2>&1; then
    DISTRIBUTION="RHEL6"
    install_rhel6
    exit 0
fi


# Could not come here
echo "Just support redhat/centos 5 or 6 series"
exit 2

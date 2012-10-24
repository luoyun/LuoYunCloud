#!/bin/bash


LUOYUN=/opt/LuoYun/

TEXTDOMAINDIR=${LUOYUN}locale
TEXTDOMAIN=luoyun-shtool

export LUOYUN TEXTDOMAINDIR TEXTDOMAIN


shopt -s extglob


# Some print function

plain () {
    local mesg=$1; shift
    printf "${BOLD}    ${mesg}${ALL_OFF}\n" "$@" >&2
}

msg () {
    local mesg=$1; shift
    printf "${GREEN}==>${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}

msg2 () {
    local mesg=$1; shift
    printf "${BLUE}  ->${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}

warning () {
    local mesg=$1; shift
    printf "${YELLOW}==> $(gettext "WARNING:")${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}

error () {
    local mesg=$1; shift
    printf "${RED}==> $(gettext "ERROR:")${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}


# default DB for luoyun web
DBNAME=luoyun
DBUSER=luoyun
DBPASS=luoyun


startdb () {

    msg "$(gettext "Starting database")"

    if service postgresql status > /dev/null 2>&1; then
	msg2 "$(gettext "database is starting already")"
    else
	if ! service postgresql start &>/dev/null ; then
            service postgresql initdb
	    service postgresql start
	fi
    fi

}


initdb () {

    msg "$(gettext "Create database user")" "${DBUSER}"
    if su - postgres -c "psql -c '\dg'" | grep ${DBUSER} > /dev/null 2>&1; then
	msg2 "$(gettext "user exist")"
    else
	echo -n "    create user \"${DBUSER}\" :"
	su - postgres -c "createuser -SRD ${DBUSER}" && success || failure
	echo
    fi

    msg "$(gettext "Create database ")" "${DBNAME}"
    if su - postgres -c 'psql -l' | grep ${DBNAME} > /dev/null 2>&1; then
	msg2 "$(gettext "database exist")"
	return
    else
	echo -n "    create database \"${DBNAME}\" :"
	su - postgres -c "createdb ${DBNAME} -O ${DBUSER}" && success || failure
	echo
    fi

    # Update auth of postgres for local user
    sed -i '/^local.*all.*all.*ident/s@ident@trust@' /var/lib/pgsql/data/pg_hba.conf
    sed -i '/^host.*127.0.0.1.*ident/s@ident@trust@' /var/lib/pgsql/data/pg_hba.conf

    service postgresql restart
}

syncdb () {
    echo -n "Sync LuoYunCloud database schema : "
    python /opt/LuoYun/web/manage.py > /dev/null 2>&1 && success || failure
    echo
}


get_os () {
    if [ -f /etc/redhat-release ]; then
	echo "redhat"
    elif [ -f /etc/debian_version ]; then
	echo "debian"
    else
	echo "unknown"
    fi
}

do_redhat () {

    # source function library
    . /etc/rc.d/init.d/functions

    startdb
    initdb
    syncdb
}

in_opt_array() {
    local needle=$1; shift

    local opt
    for opt in "$@"; do
        if [[ $opt = "$needle" ]]; then
            echo 'y' # Enabled
            return
        elif [[ $opt = "!$needle" ]]; then
            echo 'n' # Disabled
            return
        fi
    done

    echo '?' # Not Found
}
check_buildenv() {
    in_opt_array "$1" ${BUILDENV[@]}
}

# start main()
# check if messages are to be printed using color
unset ALL_OFF BOLD BLUE GREEN RED YELLOW
if [[ -t 2 && ! $USE_COLOR = "n" ]]; then
        # prefer terminal safe colored and bold text when tput is supported
    if tput setaf 0 &>/dev/null; then
        ALL_OFF="$(tput sgr0)"
        BOLD="$(tput bold)"
        BLUE="${BOLD}$(tput setaf 4)"
        GREEN="${BOLD}$(tput setaf 2)"
        RED="${BOLD}$(tput setaf 1)"
        YELLOW="${BOLD}$(tput setaf 3)"
    else
        ALL_OFF="\e[1;0m"
        BOLD="\e[1;1m"
        BLUE="${BOLD}\e[1;34m"
        GREEN="${BOLD}\e[1;32m"
        RED="${BOLD}\e[1;31m"
        YELLOW="${BOLD}\e[1;33m"
    fi
fi
readonly ALL_OFF BOLD BLUE GREEN RED YELLOW


OS=$( get_os )

case $OS in
    debian)
	error "$(gettext "Have not support Debian/Ubuntu distribution now.")"
	;;
    redhat)
	do_redhat
	;;
    *)
	error "$(gettext "Unsupported OS")"
	;;
esac



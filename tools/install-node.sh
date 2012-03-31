#!/bin/sh


# Just For RedHat/CentOS

if [ ! -f /etc/redhat-release ]; then
    echo "Just support RedHat/CentOS distribution now."
    exit 1
fi

# KVM support
if !egrep 'vmx|svm' /proc/cpuinfo  > /dev/null 2>&1 ; then
    echo "No virtualization support !"
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


LUOYUNTOP=/opt/LuoYun/
TOPDIR=${PWD}

DISTRIBUTION=

unalias cp > /dev/null 2>&1

# RPM_LIST
RPM_LIST="qemu-kvm bridge-utils libvirt"
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

}


function load_kvm()
{

    INTEL_KVM="kvm-intel"
    AMD_KVM="kvm-amd"

    if grep vmx /proc/cpuinfo  > /dev/null 2>&1; then
        modprobe kvm $INTEL_KVM
    else
        modprobe kvm $AMD_KVM
    fi
}


function setup_br0()
{
    echo "Setup br0 NIC"
    if ifconfig br0 > /dev/null 2>&1; then
        echo "  => br0 is already working !"
        return
    fi

    for nic in $(ifconfig -a | grep ^[a-z] | awk '{print $1}'); do
        ip=$(ifconfig $nic | grep Mask | awk -F: '{print $2}' | awk '{print $1}')
        if [ -n "$ip" ]; then
            netmask=$(ifconfig $nic | grep Mask | awk -F: '{print $4}' | awk '{print $1}')
            break
        fi
    done

    if [ -z "$ip" ]; then
        echo "  => not found you ip address. please setup your bridge network manually."
        return
    else
        echo "  => found your ip: $ip"
    fi

    route=$(route -n | grep UG | awk '{print $2}')

    BR_FILE="/etc/sysconfig/network-scripts/ifcfg-br0"
    NIC_FILE="/etc/sysconfig/network-scripts/ifcfg-$nic"

    cp ${BR_FILE}{,.bak} > /dev/null 2>&1
    cp ${NIC_FILE}{,.bak}

    cat > $BR_FILE <<EOF
DEVICE="br0"
ONBOOT=yes
TYPE=Bridge
BOOTPROTO=none
IPADDR=$ip
NETMASK=$netmask
GATEWAY=$route
DELAY=0
EOF

    cat > $NIC_FILE <<EOF
DEVICE=$nic
ONBOOT=yes
BRIDGE=br0
EOF

    
}


function install_lynode()
{
    echo "Install lynode"

    if [[ "X$DISTRIBUTION" != "XRHEL5" && "X$DISTRIBUTION" != "XRHEL6" ]]; then
        echo "  => unsupported distribution: $DISTRIBUTION !"
        exit 1
    fi

    mkdir -pv ${LUOYUNTOP}/platform/bin/ \
        ${LUOYUNTOP}/platform/node_data/{appliances,instances} \
        ${LUOYUNTOP}/platform/etc/luoyun-cloud/ \
        ${LUOYUNTOP}/logs
        

    NODEDIR="${TOPDIR}/lynode/${DISTRIBUTION}"

    cp ${NODEDIR}/etc/init.d/lynoded /etc/init.d/
    cp ${NODEDIR}/opt/LuoYun/platform/etc/luoyun-cloud/lynode.conf ${LUOYUNTOP}/platform/etc/luoyun-cloud/
    cp ${NODEDIR}/opt/LuoYun/platform/bin/lynode ${LUOYUNTOP}/platform/bin/

    chkconfig --add lynoded
    chkconfig --level 2345 lynoded on
}


function common_install()
{
    prepare_env
    load_kvm
    install_lynode
    setup_br0
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

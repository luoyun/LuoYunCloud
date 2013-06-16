#ifndef __LY_INCLUDE_COMPUTE_HANDLER_H
#define __LY_INCLUDE_COMPUTE_HANDLER_H

#include "../util/lypacket.h"

#define LUOYUN_APPLIANCE_URI_MAX 256
#define LUOYUN_APPLIANCE_URI_TEMPLATE "http://%s/dl/appliance/appliance_%s"
#define LUOYUN_APPLIANCE_FILE "app.img.gz"
#define LUOYUN_INSTANCE_DISK_FILE "os.img"
#define LUOYUN_INSTANCE_CONF_FILE "floppy.img"
#define LUOYUN_INSTANCE_STORAGE1_FILE "disk1.img"
#define LUOYUN_INSTANCE_STORAGE2_FILE "disk2.img"
#define LUOYUN_INSTANCE_STORAGE3_FILE "disk3.img"
#define LUOYUN_INSTANCE_KVM_DISK1_NAME "hda"
#define LUOYUN_INSTANCE_KVM_DISK2_NAME "hdb"
#define LUOYUN_INSTANCE_KVM_DISK3_NAME "hdc"
#define LUOYUN_INSTANCE_KVM_DISK4_NAME "hdd"
#define LUOYUN_INSTANCE_XEN_DISK1_NAME "sda1"
#define LUOYUN_INSTANCE_XEN_DISK2_NAME "sdb"
#define LUOYUN_INSTANCE_XEN_DISK3_NAME "sdc"
#define LUOYUN_INSTANCE_XEN_DISK4_NAME "sdd"
#define LUOYUN_INSTANCE_NET_DEFAULT "br0"
#define LUOYUN_INSTANCE_MEM_DEFAULT 256000 /* in kB */
#define LUOYUN_INSTANCE_CPU_DEFAULT 1

/* process/dispatch instance control requests */
int ly_handler_instance_control(NodeCtrlInstance * ci);
int ly_handler_busy(void);

/* build node register request, caller needs to free the returned string */
/*extern char * ly_node_xml_register_node(int * size); */
/* build node response, caller needs to free the returned string */
/*extern char * ly_node_xml_reply_result(int request_id, int ok, int *size);*/


#define LIBVIRT_XML_MAX     20480

#define LIBVIRT_XML_TMPL_XEN_DISK \
        "<disk type=\'file\'>"\
            "<source file=\'%s\'/>"\
            "<target dev=\'%s\'/>"\
        "</disk>"

#define LIBVIRT_XML_TMPL_XEN_NET_BRIDGE \
        "<interface type='bridge'>"\
            "<source bridge=\'%s\'/>"\
            "<mac address=\'%s\'/>"\
            "<script path='/etc/xen/scripts/vif-bridge'/>"\
        "</interface>"

#define LIBVIRT_XML_TMPL_XEN_NET_NAT \
        "<interface type='network'>"\
            "<source network='default'/>"\
            "<mac address=\'%s\'/>"\
        "</interface>"

#define LIBVIRT_XML_TMPL_XEN_PARA \
"<domain type='xen' id=\'%d\'>"\
    "<name>%s</name>"\
    "<os>"\
        "<type>linux</type>"\
        "<kernel>%s/kernel</kernel>"\
        "<initrd>%s/initrd</initrd>"\
        "<root>/dev/sda1</root>"\
        "<cmdline> ro</cmdline>"\
    "</os>"\
    "<memory>%d</memory>"\
    "<vcpu>%d</vcpu>"\
    "<devices>"\
    "<disk type='file' device='floppy'>"\
      "<driver name='qemu' type='raw' cache='none'/>"\
      "<source file=\'%s\'/>"\
      "<target dev='fda' bus='fdc'/>"\
      "<address type='drive' controller='0' bus='0' unit='0'/>"\
    "</disk>"\
"%s"\
"%s"\
    "</devices>"\
    "<serial type='pty'>"\
      "<target port='0'/>"\
    "</serial>"\
    "<console type='pty'>"\
      "<target port='0'/>"\
    "</console>"\
"</domain>"


#define LIBVIRT_XML_TMPL_XEN_FULL ""

#define LIBVIRT_XML_TMPL_KVM_DISK \
    "<disk type='file' device='disk'>"\
      "<driver name='qemu' type='raw' io='threads'/>"\
      "<source file=\'%s\'/>"\
      "<target dev=\'%s\' bus='ide'/>"\
    "</disk>"

#define LIBVIRT_XML_TMPL_KVM_NET_BRIDGE \
    "<interface type='bridge'>"\
      "<source bridge=\'%s\'/>"\
      "<mac address=\'%s\'/>"\
    "</interface>"\

#define LIBVIRT_XML_TMPL_KVM_NET_NAT \
    "<interface type='network'>"\
      "<source network='default'/>"\
      "<mac address=\'%s\'/>"\
    "</interface>"

#define LIBVIRT_XML_TMPL_KVM \
"<domain type='kvm' id=\'%d\'>"\
  "<name>%s</name>"\
  "<os>"\
    "<type arch='x86_64' machine='pc'>hvm</type>"\
    "<boot dev='hd'/>"\
  "</os>"\
  "<memory>%d</memory>"\
  "<vcpu>%d</vcpu>"\
  "<features>"\
    "<acpi/>"\
    "<apic/>"\
    "<pae/>"\
  "</features>"\
  "<clock offset='utc'/>"\
  "<on_poweroff>destroy</on_poweroff>"\
  "<on_reboot>restart</on_reboot>"\
  "<on_crash>restart</on_crash>"\
  "<devices>"\
    "<emulator>/usr/libexec/qemu-kvm</emulator>"\
    "<disk type='file' device='floppy'>"\
      "<driver name='qemu' type='raw' />"\
      "<source file=\'%s\'/>"\
      "<target dev='fda' bus='fdc'/>"\
      "<address type='drive' controller='0' bus='0' unit='0'/>"\
    "</disk>"\
"%s"\
    "<controller type='ide' index='0'>"\
      "<address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>"\
    "</controller>"\
"%s"\
    "<serial type='pty'>"\
      "<target port='0'/>"\
    "</serial>"\
    "<console type='pty'>"\
      "<target type='serial' port='0'/>"\
    "</console>"\
    "<input type='mouse' bus='ps2'/>"\
    "<graphics type='vnc' port='-1' autoport='yes'/>"\
    "<video>"\
      "<model type='cirrus' vram='9216' heads='1'/>"\
      "<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>"\
    "</video>"\
    "<memballoon model='virtio'>"\
      "<address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>"\
    "</memballoon>"\
  "</devices>"\
"</domain>"

#endif

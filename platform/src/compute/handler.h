#ifndef __LY_INCLUDE_COMPUTE_HANDLER_H
#define __LY_INCLUDE_COMPUTE_HANDLER_H

#include "../util/lypacket.h"

#define LUOYUN_APPLIANCE_URI_MAX 256
#define LUOYUN_APPLIANCE_URI_TEMPLATE "http://%s/dl/appliance/appliance_%s"
#define LUOYUN_INSTANCE_DISK_FILE "os.img"
#define LUOYUN_INSTANCE_MEM_DEFAULT 256000 /* in kB */
#define LUOYUN_INSTANCE_CPU_DEFAULT 1

/* process/dispatch instance control requests */
int ly_handler_instance_control(NodeCtrlInstance * ci);
int ly_handler_busy(void);

/* build node register request, caller needs to free the returned string */
/*extern char * ly_node_xml_register_node(int * size); */
/* build node response, caller needs to free the returned string */
/*extern char * ly_node_xml_reply_result(int request_id, int ok, int *size);*/


#define LIBVIRT_XML_MAX     2048

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
        "<disk type=\'file\'>"\
            "<source file=\'%s\'/>"\
            "<target dev='sda1'/>"\
        "</disk>"\
        "<interface type='bridge'>"\
            "<source bridge='br0'/>"\
            "<mac address=\'%s\'/>"\
            "<script path='/etc/xen/scripts/vif-bridge'/>"\
        "</interface>"\
    "</devices>"\
    "<serial type='pty'>"\
      "<target port='0'/>"\
    "</serial>"\
    "<console type='pty'>"\
      "<target port='0'/>"\
    "</console>"\
"</domain>"


#define LIBVIRT_XML_TMPL_XEN_FULL ""

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
    "<disk type='file' device='disk'>"\
      "<driver name='qemu' type='raw' cache='none' io='threads'/>"\
      "<source file=\'%s\'/>"\
      "<target dev='hda' bus='ide'/>"\
      "<address type='drive' controller='0' bus='0' unit='0'/>"\
    "</disk>"\
    "<controller type='ide' index='0'>"\
      "<address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>"\
    "</controller>"\
    "<interface type='bridge'>"\
      "<mac address=\'%s\'/>"\
      "<source bridge='br0'/>"\
      "<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>"\
    "</interface>"\
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

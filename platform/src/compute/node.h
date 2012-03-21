#ifndef __LY_INCLUDE_COMPUTE_NODE_H
#define __LY_INCLUDE_COMPUTE_NODE_H

NodeInfo * ly_node_info_init(void);
int ly_node_info_update(void);
int ly_node_busy(void);

void ly_node_send_report(int type, char * msg);
void ly_node_send_report_resource(void);

#endif

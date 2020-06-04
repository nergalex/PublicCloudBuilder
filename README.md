# Pre-requisites
## Ansible Tower
### virtualenv
Create a virtualenv, please follow [Tower admin guide](https://docs.ansible.com/ansible-tower/latest/html/administration/tipsandtricks.html#preparing-a-new-custom-virtualenv)
Install ansible >= 2.9
```bash
$ sudo yum groupinstall -y "development tools"
$ sudo virtualenv /var/lib/awx/venv/my_env
$ sudo /var/lib/awx/venv/my_env/bin/pip install python-memcached psutil
$ sudo /var/lib/awx/venv/my_env/bin/pip install -U ansible
```

Ensure that your virtualenv have the rights 755, else:
```bash
$ chmod 755 -R /var/lib/awx/venv/my_env
```

### F5 f5devcentral.f5ansible
This collection includes the most recently released ansible modules for BIG-IP and BIG-IQ from F5Networks. This collection packages and distributes playbooks, roles, modules, and plugins.
source: <https://galaxy.ansible.com/f5networks/f5_modules>
```bash
$ sudo ansible-galaxy collection install f5networks.f5_modules -p /usr/share/ansible/collections
```

### Azure azure_preview_modules
This role is the most complete and includes all the latest Azure modules. The update and bug fix are done in a more timely manner than official Ansible release.
If you use Ansible for Azure resource provisioning purpose, you're strongly encouraged to install this role.
Please follow install guide https://github.com/Azure/azure_preview_modules
```bash
$ sudo ansible-galaxy install azure.azure_preview_modules
$ sudo /var/lib/awx/venv/my_env/bin/pip install -U -r /etc/ansible/roles/azure.azure_preview_modules/files/requirements-azure.txt
$ sudo /var/lib/awx/venv/my_env/bin/pip show azure-mgmt-compute
```

If `azure-mgmt-compute` < `10.0.0` then use last update from azure_preview_modules repo and not from Galaxy.
`/etc/ansible/roles/` is an example of an Tower installation where `roles` are located.
```bash
$ sudo cd /etc/ansible/roles/
$ sudo git clone https://github.com/Azure/azure_preview_modules.git
$ sudo /var/lib/awx/venv/my_env/bin/pip install -r /etc/ansible/roles/azure.azure_preview_modules/files/requirements-azure.txt
$ sudo vi /etc/ansible/roles/azure.azure_preview_modules/defaults/main.yml
skip_azure_sdk: false
```


### Custom module for azure_preview_modules
Copy modules below to `/etc/ansible/roles/azure.azure_preview_modules/library/`
* `azure_rm_networkinterface_vmss_info.py`
* `azure_rm_virtualmachinescaleset_2NIC.py`
* `azure_rm_virtualmachinescalesetinstance_info.py`

### VMSS credential 
Create custom credential `cred_NGINX` to manage access to VMs in VMSS

| CREDENTIAL TYPE | USERNAME      | SSH PRIVATE KEY     | SIGNED SSH CERTIFICATE         | PRIVILEGE ESCALATION METHOD    |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| `Machine` | `my_VM_admin_user` | `my_VM_admin_user_key` | `my_VM_admin_user_CRT` | `sudo` |

### Repo for NGINX App Protect
Copy to a Web repository
* ```app-protect-20.zip```
* ```installAppProtect.sh```

# Engineering
## Code
* Deployment is based on `workflow template`. Example: `workflow template`=`wf-create_create_edge_security_inbound` ;
* A `workflow template` includes multiple `job template`. Example: `job template`=`poc-azure_create_hub_edge_security_inbound`
* A `job template` have an associated `playbook`. Example: `playbook`=`playbooks/poc-azure.yaml`
* A `playbook` launch a `play` in a `role`. Example: `role`=`poc-azure`
```yaml
- hosts: localhost
  gather_facts: no
  roles:
    - role: poc-azure
```
* A `play` is an `extra variable` named `activity` and set in each `job template`. Example: `create_hub_edge_security_inbound`
* The specified `play` (or `activity`) is launched by the `main.yaml` task located in the role `tasks/main.yaml`
```yaml
- name: Run specified activity
  include_tasks: "{{ activity }}.yaml"
  when: activity is defined
```
* The specified `play` contains `tasks` to execute. Example: play=`create_hub_edge_security_inbound.yaml`

## Autoscale


# Deployment
## Azure - network components
Create and launch a workflow template `wf-create_create_edge_security_inbound` that include those Job templates in this order:
In `poc-azure_create_hub_edge_security_inbound`, remove `virtual_network_gateway` task and routes to `virtual_network_gateway` if a vNet peering is used to interconnect your cross-management vNet.

| Job template  | playbook      | activity      | inventory     | limit         | credential   |
| ------------- | ------------- | ------------- | ------------- | ------------- |------------- |
| `poc-azure_create_hub_edge_security_inbound`  | `playbooks/poc-azure.yaml`    | `create_hub_edge_security_inbound`    | `my_project`  | `localhost` | `my_azure_credential` |
| `poc-azure_create-vm-nginx_unit`              | `playbooks/poc-azure.yaml`    | `create-vm-nginx_unit`                | `my_project`  | `localhost` | `my_azure_credential` |
| `poc-nginx_onboarding_system_vm`              | `playbooks/poc-nginx_vm.yaml` | `onboarding_system`                   | `localhost`   | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_unit`             | `playbooks/poc-azure.yaml`    | `onboarding_nginx_unit`               | `localhost`   | `localhost` | `cred_NGINX` |

## NGINX south | NGINX ADC
Create and launch a workflow template `wf-create_vmss_nginx_app_protect` that include those Job templates in this order:

| Job name      | objective     | playbook      | activity      | inventory     | limit         | credential    |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| `poc-azure_create-vmss-nginx-2NIC_1LB`                | Create VMSS                                       | `playbooks/poc-azure.yaml`        | `create-vmss-nginx-2NIC_1LB`                 | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_set-vmss-master_vm`                        | Set a Master VM                                   | `playbooks/poc-azure.yaml`        | `set-vmss-master_vm`                         | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_create-vmss-extension-nginx_app_protect`   | Set script to install NGINX App Protect           | `playbooks/poc-azure.yaml`        | `create-vmss-extension-nginx_app_protect`    | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_get-vmss-facts`                            | Get VM IPs from VMSS                              | `playbooks/poc-azure.yaml`        | `get-vmss-facts`                             | `my_project` | `localhost` | `my_azure_credential` |
| `poc-nginx_onboarding_system`                         | Configure system variable                         | `playbooks/poc-azure.yaml`        | `onboarding_system`                          | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_app_protect`              | Configure NGINX App Protect                       | `playbooks/poc-azure.yaml`        | `onboarding_nginx_app_protect`               | `localhost` | `localhost` | `cred_NGINX` |
| `poc-azure_create-vmss-autoscale`                     | Create an autoscale policy                        | `playbooks/poc-azure.yaml`        | `create-vmss-autoscale`                      | `my_project` | `localhost` | `my_vmss_credential` |
| `poc-nginx_onboarding_nginx_sync_step1_master`        | *Configure Master VM as a Master NGINX            | `playbooks/poc-nginx_master.yaml` | `onboarding_nginx_sync_step1_master`         | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_sync_step2_slaves`        | *Configure Slaves VM as a Slave NGINX             | `playbooks/poc-nginx_slaves.yaml` | `onboarding_nginx_sync_step2_slaves`         | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_sync_step3_master`        | *Execute the copy from Master VM to Slave NGINX   | `playbooks/poc-nginx_master.yaml` | `onboarding_nginx_sync_step3_master`         | `localhost` | `localhost` | `cred_NGINX` |

| Extra variable| Description | Example of value      |
| ------------- | ------------- | ------------- |
| `extra_app_protect_monitor_ip`          | Kibana for NGINX App Protect | `10.0.0.20` |
| `extra_app_protect_repo`                | repo that stores NGINX App Protect install scripts | `http://10.0.0.19` |
| `extra_availability_zone`               | availability zones | `[1, 2]` |
| `extra_dataplane_subnet_address_mask`   | eth1 subnet | `24` |
| `extra_elb_management_name`             | External LB for outbound connection during install| `outbound-management-vmss-nginx-external` |
| `extra_gw_dataplane`                    | eth1 GW | `10.100.1.1` |
| `extra_gw_management`                   | eth0 GW | `10.100.0.1` |
| `extra_key_data`                        | admin CRT | `-----BEGIN  CERTIFICATE-----XXXXXXX-----END CERTIFICATE-----` |
| `extra_lb_dataplane_name`               | LB name for dataplane traffic | `external` |
| `extra_lb_dataplane_type`               | LB type for dataplane traffic | `elb` |
| `extra_location`                        | region | `eastus2` |
| `extra_offer`                           | OS | `CentOS` |
| `extra_publisher`                       | OS distrib | `OpenLogic` |
| `extra_sku`                             | OS distrib version | `7.4` |
| `extra_vm_size`                         | VM type | `Standard_DS3_v2` |
| `extra_vmss_capacity`                   | initial vmss_capacity | `2` |
| `extra_vmss_name`                       | logical vmss_name | `nginxwaf` |
| `nginx_rpm_version`                     | Nginx+ version to install | `20` |
| `extra_platform_name`                   | logical platform_name | `TotalInbound` |
| `extra_platform_tags`                   | logical platform_tags | `environment=DMO platform=TotalInbound project=CloudBuilderf5` |
| `extra_project_name`                    | logical project_name | `CloudBuilderf5` |
| `extra_route_prefix_on_premise`         | cross management subnet | `10.0.0.0/24` |
| `extra_subnet_dataplane_name`           | logical name for eth1 subnet | `nginx` |
| `extra_template_nginx_conf`             | jinja2 template for nginx.conf| `nginx_app_protect.conf` |
| `extra_template_route`                  | jinja2 template for persistent route | `system_route_persistent-default_via_dataplane.conf` |
| `extra_app_protect_monitor_ip`          | IP address of Kibana server | `10.0.0.20` |
| `extra_nginx_key`                       | NGINX+ private key | `-----BEGIN  PRIVATE KEY-----XXXXXXX-----END PRIVATE KEY-----` |
| `extra_nginx_crt`                       | NGINX+ certificate | `-----BEGIN  CERTIFICATE-----XXXXXXX-----END CERTIFICATE-----` |
| `extra_webhook_email`                   | NGINX+ certificate | `al.dacosta@f5.com` |
| `extra_webhook_vm_name`                 | NGINX+ certificate | `autoscale-f5` |

## BIG-IP Advanced WAF
Create and launch a workflow template `wf-create_vmss_device-group_awaf` that include those Job templates in this order:

| Job name      | objective     | playbook      | activity      | inventory     | limit         | credential    |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| `poc-azure_create-vmss-bigip`                 |  | `` | `playbooks/poc-azure.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_set-vmss-master_vm`                |  | `` | `playbooks/poc-azure.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_get-vmss-facts`                    |  | `` | `playbooks/poc-azure.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-f5_do_vmss_device-group`                 |  | `` | `playbooks/poc-f5.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-f5-as3_vmss_device-group_create_log_profile`  | `` |  | `playbooks/poc-f5.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-f5-bigiq_vmss_device-group_discover`     |  | `` | `playbooks/poc-f5.yaml` | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_create-vmss-autoscale`             |  | `` | `playbooks/poc-azure.yaml` | `my_project` | `localhost` | `my_azure_credential` |

| Extra variable        | Description | Example of value      |
| -------------         | ------------- | ------------- |
| `extra_admin_user`      | admin user name on BIG-IP| `admin` |
| `extra_admin_password`  | admin user password on BIG-IP| `Ch4ngeMe!` |
| `extra_port_mgt`        | management port on BIG-IP| `443` |
| `extra_key_data`        | admin CRT | `-----BEGIN  CERTIFICATE-----XXXXXXX-----END CERTIFICATE-----` |
| `extra_offer`           | offer | `f5-big-ip-byol` |
| `extra_sku`             | OS distrib version | `7.4` |
| `extra_vm_size`         | VM type | `Standard_DS4_v2` |
| `extra_device_modules`  | List of modules to discover by BIG-IQ | `ltm,asm,security_shared` |
| `extra_as3_template`         |  | `as3_security_logging.jinja2` |
| `extra_availability_zone`         | availability zones | `[1, 2]` |
| `extra_bigiq_admin_password`         |  | `Ch4ngeMe!` |
| `extra_bigiq_admin_user`         |  | `admin` |
| `extra_bigiq_device_discovery_state`       |  | `present` |
| `extra_bigiq_ip_mgt`       |  | `10.0.0.27` |
| `extra_bigiq_port_mgt`       |  | `443` |
| `extra_dataplane_subnet_address_mask`       | eth1 subnet | `24` |
| `extra_dcd_ip`       |  | `10.0.0.28` |
| `extra_dcd_port`       |  | `8514` |
| `extra_dcd_servers`       |  | `[{''address'': ''10.0.0.28'', ''port'': ''8514''}]` |
| `extra_elb_management_name`       | External LB for outbound connection during install | `outbound-management-vmss-awaf` |
| `extra_gw_dataplane`       | eth1 GW | `10.100.2.1` |
| `extra_gw_management`       | eth0 GW | `10.100.0.1` |
| `extra_lb_dataplane_name`       | LB name for dataplane traffic | `external` |
| `extra_lb_dataplane_type`       | LB type for dataplane traffic | `ilb` |
| `extra_licensing`       |  | `BIGIQ` |
| `extra_location`       | Azure region | `eastus2` |
| `extra_platform_name` | logical platform_name | TotalInbound |
| `extra_platform_tags` | logical platform_tags | environment=DMO platform=TotalInbound project=CloudBuilderf5 |
| `extra_project_name` | logical project_name | CloudBuilderf5 |
| `extra_route_prefix_on_premise` | cross management subnet | 10.0.0.0/24 |
| `extra_subnet_dataplane_name`       | logical name for eth1 subnet | `external` |
| `extra_template_do`       |  | `do-vmss-standalone-2nic-awaf-BIGIQ.json` |
| `extra_upstream_lb_vip`       |  | `10.100.3.10` |
| `extra_vmss_capacity`       | initial vmss_capacity | `2` |
| `extra_vmss_name`       | logical vmss_name | `awaf` |
| `extra_webhook_email`                   | NGINX+ certificate | `al.dacosta@f5.com` |
| `extra_webhook_vm_name`                 | NGINX+ certificate | `autoscale-f5` |

## NGINX south | NGINX ADC
Create and launch a workflow template `wf-create_vmss_nginx_adc` that include those Job templates in this order:

| Job name      | objective     | playbook      | activity      | inventory     | limit         | credential    |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| `poc-azure_create-vmss-nginx-2NIC_2LB`                | Create VMSS                                       | `playbooks/poc-azure.yaml`        | `create-vmss-nginx-2NIC_2LB`                 | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_set-vmss-master_vm`                        | Set a Master VM                                   | `playbooks/poc-azure.yaml`        | `set-vmss-master_vm`                         | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_create-vmss-extension-nginx_from_repo`     | Set script to install NGINX App Protect           | `playbooks/poc-azure.yaml`        | `create-vmss-extension-nginx_from_repo`    | `my_project` | `localhost` | `my_azure_credential` |
| `poc-azure_get-vmss-facts`                            | Get VM IPs from VMSS                              | `playbooks/poc-azure.yaml`        | `get-vmss-facts`                             | `my_project` | `localhost` | `my_azure_credential` |
| `poc-nginx_onboarding_system`                         | Configure system variable                         | `playbooks/poc-azure.yaml`        | `onboarding_system`                          | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_adc`                      | Configure NGINX App Protect                       | `playbooks/poc-azure.yaml`        | `nginx_onboarding_nginx_adc`               | `localhost` | `localhost` | `cred_NGINX` |
| `poc-azure_create-vmss-autoscale`                     | Create an autoscale policy                        | `playbooks/poc-azure.yaml`        | `create-vmss-autoscale`                      | `my_project` | `localhost` | `my_vmss_credential` |
| `poc-nginx_onboarding_nginx_sync_step1_master`        | *Configure Master VM as a Master NGINX            | `playbooks/poc-nginx_master.yaml` | `onboarding_nginx_sync_step1_master`         | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_sync_step2_slaves`        | *Configure Slaves VM as a Slave NGINX             | `playbooks/poc-nginx_slaves.yaml` | `onboarding_nginx_sync_step2_slaves`         | `localhost` | `localhost` | `cred_NGINX` |
| `poc-nginx_onboarding_nginx_sync_step3_master`        | *Execute the copy from Master VM to Slave NGINX   | `playbooks/poc-nginx_master.yaml` | `onboarding_nginx_sync_step3_master`         | `localhost` | `localhost` | `cred_NGINX` |

| Extra variable| Description   | Example of value      |
| ------------- | ------------- | -------------         |
| `extra_app_protect_monitor_ip`          | Kibana for NGINX App Protect | `10.0.0.20` |
| `extra_app_protect_repo`                | repo that stores NGINX App Protect install scripts | `http://10.0.0.19` |
| `extra_availability_zone`               | availability zones | `[1, 2]` |
| `extra_dataplane_subnet_address_mask`   | eth1 subnet | `24` |
| `extra_elb_management_name`             | External LB for outbound connection during install| `outbound-management-vmss-nginx-internal` |
| `extra_gw_dataplane`                    | eth1 GW | `10.100.4.1` |
| `extra_gw_management`                   | eth0 GW | `10.100.0.1` |
| `extra_key_data`                        | admin CRT | `-----BEGIN  CERTIFICATE-----XXXXXXX-----END CERTIFICATE-----` |
| `extra_lb_dataplane_name`               | LB name for dataplane traffic | `internal` |
| `extra_lb_dataplane_type`               | LB type for dataplane traffic | `ilb` |
| `extra_location`                        | region | `eastus2` |
| `extra_nginx_key`                       | NGINX+ private key | `-----BEGIN  PRIVATE KEY-----XXXXXXX-----END PRIVATE KEY-----` |
| `extra_nginx_crt`                       | NGINX+ certificate | `-----BEGIN  CERTIFICATE-----XXXXXXX-----END CERTIFICATE-----` |
| `extra_offer`                           | OS | `CentOS` |
| `extra_publisher`                       | OS distrib | `OpenLogic` |
| `extra_sku`                             | OS distrib version | `7.4` |
| `extra_vm_size`                         | VM type | `Standard_DS3_v2` |
| `extra_vmss_capacity`                   | initial vmss_capacity | `2` |
| `extra_vmss_name`                       | logical vmss_name | `nginxapigw` |
| `nginx_rpm_version`                     | Nginx+ version to install | `20` |
| `extra_platform_name`                   | logical platform_name | `TotalInbound` |
| `extra_platform_tags`                   | logical platform_tags | `environment=DMO platform=TotalInbound project=CloudBuilderf5` |
| `extra_project_name`                    | logical project_name | `CloudBuilderf5` |
| `extra_route_prefix_on_premise`         | cross management subnet | `10.0.0.0/24` |
| `extra_subnet_dataplane_name`           | logical name for eth1 subnet | `internal` |
| `extra_template_nginx_conf`             | jinja2 template for nginx.conf| `nginx_adc.conf` |
| `extra_template_route`                  | jinja2 template for persistent route | `system_route_persistent-default_via_mgmtplane.conf` |
| `extra_app_protect_monitor_ip`          | IP address of Kibana server | `10.0.0.20` |
| `extra_vip_address_list_nginx_second_line`          | routed subnet for VIP | `[10.100.11.0/24]` |
| `extra_webhook_email`                   | NGINX+ certificate | `al.dacosta@f5.com` |
| `extra_webhook_vm_name`                 | NGINX+ certificate | `autoscale-f5` |








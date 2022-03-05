#!/bin/python3 -u
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import glob
import json
import os
import subprocess
import urllib.request
from datetime import datetime

def report_duration(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func(*args, *kwargs)
        duration = datetime.now() - start_time
        print(f"Function {func.__name__}() duration: {duration}")
    return wrapper

def set_region():
    meta_url = 'http://169.254.169.254/latest/meta-data/placement/availability-zone'
    with urllib.request.urlopen(meta_url) as f:
        az = f.read().decode()
    os.environ['AWS_DEFAULT_REGION'] = az[:-1]

def get_instance_id():
    meta_url = 'http://169.254.169.254/latest/meta-data/instance-id'
    with urllib.request(meta_url) as f:
        return f.read.decode()

def get_vpc_id(instance_id):
    cmd = ['aws','ec2','describe-instances',
            '--instance-id',instance_id,
            '--query','Reservations[0].Instances[0].VpcId',
            '--output','text',
            ]
    return subprocess.check_output(cmd).decode.strip()

def get_s3_endpoint_url(vpc_id):
    region = os.environ['AWS_DEFAULT_REGION']
    cmd = ['aws','ec2','describe-vpc-endpoints',
            '--filters',
            f'Name=service-name,Values=com.amazonaws.{region}.s3',
            f'Name=vpc-id,Values={vpc_id}',
            '--query','VpcEndpoints[0].DnsEntries[0].DnsName',
            '--output','text',
            ]
    fqdn = subprocess.check_output(cmd).decode().strip().split('.',1)[1]
    return f'https://bucket.{fqdn}'

def get_parameter(name):
    cmd = ['aws', 'ssm', 'get-parameter',
            '--name', name,
            '--query', 'Parameter.Value',
            '--output', 'text',
            '--with-decryption',
            ]
    return subprocess.check_output(cmd)

def set_parameter(name,value):
    cmd = ['aws','ssm','put-parameter',
            '--name', name,
            '--value', value,
            '--overwrite'
            ]
    return subprocess.check_output(cmd)

def write_json_to_file(filepath, content):
    with open(filepath, 'w') as fh:
        fh.write(json.dumps(content, indent=2))
        fh.write('\n')

def write_mapping_to_file(filepath,mapping,use_quote=False):
    with open(filepath,'w') as fh:
        for k,v in mapping.items():
            q = '"' if use_quote else ''
            fh.write(f'{k}={q}{v}{q}\n')

def download_from_s3(bucket, key, local_filepath, endpoint_url=None):
    s3_uri = f's3://{bucket}/{key}'
    print(f"Downloading from s3://{bucket}/{key} to {local_filepath}")
    cmd = ['aws','s3','cp',s3_uri,local_filepath]
    if endpoint_url:
        cmd.extend(['--endpoint-url',endpoint_url])
    subprocess.check_call(cmd)

def install_rpm(rpm_filename):
    subprocess.call(['yum', 'install', '-y', rpm_filename])

def extract_confluent(filepath, dirpath):
    cmd = ['tar','-zxf',filepath,'-C',dirpath,'--strip-component','1']
    subprocess.check_call(cmd)

def get_msk_cluster_node(msk_cluster):
    print(f'get MSK cluster broker_id')
    broker_id_list = []
    for k in msk_cluster:
        broker_id_list.append(k['broker_id'])
    return broker_id_list

def get_msk_cluster_doamin(msk_cluster):
    print(f"get MSK cluster domain")
    endpoint = msk_cluster[0]['endpoints'][0]
    return '.'.join(endpoint.split('.')[1:]).strip().strip('"') # remove newline and double quote char

def config_kafka(brokers_domain_name,node_id,kafka_bin_path,client_properties_path):
    print(f"config_kafka {node_id}")
    bootstrap_port=9094
    replication_port=9093
    replication_secure_port=9095

    broker_server=f'b-{node_id}.{brokers_domain_name}'
    bootstrap_server=f'{broker_server}:{bootstrap_port}'
    internal_server=f'b-{node_id}-internal.{brokers_domain_name}'
    listener_port=9000+node_id
    
    client_secure=f'{broker_server}:{listener_port}'
    replication=f'{internal_server}:{replication_port}'
    replication_secure=f'{internal_server}:{replication_secure_port}'

    cmd = [f'{kafka_bin_path}/kafka-configs.sh',
            '--bootstrap-server', bootstrap_server,
            '--entity-type','brokers',
            '--entity-name',str(node_id),
            '--alter',
            '--command-config',client_properties_path,
            '--add-config',
            f'advertised.listeners=[CLIENT_SECURE://{client_secure},REPLICATION://{replication},REPLICATION_SECURE://{replication_secure}]',
            ]
    return subprocess.check_output(cmd)

def export_log(bucket,key,endpoint_url):
    s3_uri = f's3://{bucket}/{key}'
    cmd = ['aws','s3','cp','/var/log/cloud-init-output.log',s3_uri,'--sse','aws:kms']
    if endpoint_url:
        cmd.extend(['--endpoint-url',endpoint_url])
    subprocess.check_call(cmd)

def update_brokers(config_node_list,cluster,msk_cluster_nodes,msk_cluster_domain,confluent_binpath,kafka_properties_filepath):
    print(f"Checking each node stauts in cluster {cluster}")
    configured_node = config_node_list[cluster]['broker_listeners_configured']
    for n in msk_cluster_nodes:
        if n not in configured_node:
            print(f'node:{n} execute kafka config update')
            print(config_kafka(msk_cluster_domain,n,confluent_binpath,kafka_properties_filepath))
            config_node_list[cluster]['broker_listeners_configured'].append(n)
        else:
            print(f"node:{n} do nothing")
    return config_node_list
    

def config_MSK_Cluster(cluster_list,confluent_binpath,kafka_properties_filepath,config_node_list):
    # get the create MSK cluster list form SSM
    # check the broker status in each cluster
    for cluster in cluster_list.keys():
        msk_cluster_domain = get_msk_cluster_doamin(cluster_list[cluster])
        msk_cluster_nodes = get_msk_cluster_node(cluster_list[cluster])
        # compare the configured list
        if cluster in config_node_list.keys():
            print(f"Cluster {cluster} was configured.")
        # if no configuration yet, execute kafka-configs.sh
        else:
            print(f"Cluster {cluster} is new cluster.")
            config_node_list[cluster] = {"broker_listeners_configured":[]}
        update_brokers(config_node_list,cluster,msk_cluster_nodes,msk_cluster_domain,confluent_binpath,kafka_properties_filepath)
    print(config_node_list)
    return config_node_list

@report_duration
def main():
    set_region()

    settings_parameter_name = '/msk/cluster/node/settings'
    cluster_list_parameter_name = '/msk/cluster/list'
    config_node_parameter_name = '/msk/cluster/node/config/list'

    settings_filepath = '/root/settings'
    confluent_dirpath = '/opt/confluent'
    confluent_binpath = f'{confluent_dirpath}/bin'
    kafka_properties_filepath = '/root/kafka.properties'
    
    settings = json.loads(get_parameter(settings_parameter_name)) # load the parameter
    cluster_list = json.loads(get_parameter(cluster_list_parameter_name)) # use aws cli to get the MSK cluster list
    config_node_list = json.loads(get_parameter(config_node_parameter_name)) # use aws cli to get the node list 
    binaries_bucket = settings['binaries_s3_bucket']
    log_bucket = settings['log_s3_bucket']
    confluent_package_filename = settings['confluent_package_filename']
    confluent_package_filepath = f'/root/{confluent_package_filename}'
    java_version_name = settings['java_version_name']
    s3_endpoint_type = settings['s3_endpoint_type']
    kafka_properties = settings['kafka_properties']

    write_json_to_file(settings_filepath,settings)
    write_mapping_to_file(kafka_properties_filepath,kafka_properties)

    endpoint_url = None
    if s3_endpoint_type == 'interface':
        instance_id  = get_instance_id()
        vpc_id       = get_vpc_id(instance_id)
        endpoint_url = get_s3_endpoint_url(vpc_id)

    install_rpm(java_version_name) # install Java
    download_from_s3(binaries_bucket,confluent_package_filename,confluent_package_filepath,endpoint_url) # download kafka binary in S3
    os.makedirs(confluent_dirpath,exist_ok=True)
    extract_confluent(confluent_package_filepath,confluent_dirpath) # unzip kafka binary
    config_node_list = config_MSK_Cluster(cluster_list,confluent_binpath,kafka_properties_filepath,config_node_list)
    set_parameter(config_node_parameter_name,json.dumps(config_node_list)) # update the configured list
    # export the log result to s3 for verification 
    export_log(log_bucket,f'user_data_{datetime.now().strftime("%Y%m%d%H%M")}.log',endpoint_url)
    # shutdown EC2 after complete execute
    os.system('systemctl poweroff') 

if __name__ == "__main__":
    main()
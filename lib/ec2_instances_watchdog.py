'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import boto3
from datetime import datetime, timezone

region = 'us-east-1'
ec2 = boto3.client('ec2', region_name=region)

def is_instance_running(instance):
    if (instance['State']['Name'] == 'running'):
        return True
    else:
        return False

def can_instance_be_terminated(instance):
    for t in instance['Tags']:
        if t['Key'] == 'NoTerminate':
            return False
    return True

def instance_uptime_in_hours(instance):
    now = datetime.now(timezone.utc)
    launch_time = instance['LaunchTime']
    duration = now - launch_time
    duration_in_s = duration.total_seconds()
    duration_in_h = divmod(duration_in_s, 3600)[0]
    print('instance "{0}" has an uptime of {1} seconds'.format(instance['InstanceId'], duration_in_s))
    return duration_in_h

def lambda_handler(event, context):
    response = ec2.describe_instances()
    instances_to_terminate = []

    for r in response['Reservations']:
      for i in r['Instances']:
        if is_instance_running(i) and can_instance_be_terminated(i):
            if instance_uptime_in_hours(i) >= 5:
                instances_to_terminate.append(i['InstanceId'])
                print('terminating instance "{0}" ...'.format(i['InstanceId']))

    if len(instances_to_terminate) > 0:
        ec2.terminate_instances(InstanceIds=instances_to_terminate)

from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config, make_api_call

logger = logging.getLogger(__name__)

class ComputeServices:
    def __init__(self, session):
        self.session = session

    def get_ec2_instances(self, region: str) -> List[Dict]:
        """Get detailed information about EC2 instances in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            instance_list = []
            paginator = ec2.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_list.append({
                            'InstanceId': instance['InstanceId'],
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'LaunchTime': instance['LaunchTime'].isoformat(),
                            'Tags': instance.get('Tags', [])
                        })
            return instance_list
        except ClientError as e:
            logger.error(f"Error getting EC2 instances in {region}: {e}")
            return []

    def get_lambda_functions(self, region: str) -> List[Dict]:
        """Get information about Lambda functions in a region."""
        lambda_client = self.session.client('lambda', region_name=region)
        try:
            functions = lambda_client.list_functions()
            return [{
                'FunctionName': function['FunctionName'],
                'Runtime': function['Runtime'],
                'Memory': function['MemorySize'],
                'Timeout': function['Timeout']
            } for function in functions['Functions']]
        except ClientError as e:
            logger.error(f"Error getting Lambda functions in {region}: {e}")
            return []

    def get_ecs_info(self, region: str) -> List[Dict]:
        """Get information about ECS clusters and services in a region."""
        ecs = self.session.client('ecs', region_name=region, config=boto3_config)
        try:
            clusters = ecs.list_clusters()
            cluster_info = []
            
            for cluster_arn in clusters['clusterArns']:
                try:
                    # Get cluster details
                    cluster = ecs.describe_clusters(clusters=[cluster_arn])['clusters'][0]
                    
                    # Get services in the cluster
                    services = ecs.list_services(cluster=cluster_arn)
                    service_count = len(services.get('serviceArns', []))
                    
                    # Get task count
                    tasks = ecs.list_tasks(cluster=cluster_arn)
                    task_count = len(tasks.get('taskArns', []))
                    
                    cluster_info.append({
                        'ClusterName': cluster['clusterName'],
                        'ClusterArn': cluster['clusterArn'],
                        'Status': cluster['status'],
                        'ServiceCount': service_count,
                        'TaskCount': task_count,
                        'ActiveServices': service_count,
                        'RunningTasks': cluster['runningTasksCount'],
                        'PendingTasks': cluster['pendingTasksCount'],
                        'ContainerInstances': cluster['registeredContainerInstancesCount']
                    })
                except ClientError:
                    continue
            
            return cluster_info
        except ClientError as e:
            logger.error(f"Error getting ECS information in {region}: {e}")
            return [] 
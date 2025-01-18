from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config

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
                        name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                        instance_list.append({
                            'InstanceId': instance['InstanceId'],
                            'Name': name,
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'LaunchTime': instance['LaunchTime'].isoformat(),
                            'Platform': instance.get('Platform', 'Linux/UNIX'),
                            'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                            'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                            'VpcId': instance.get('VpcId', 'N/A'),
                            'SubnetId': instance.get('SubnetId', 'N/A'),
                            'Tags': instance.get('Tags', [])
                        })
            return instance_list
        except ClientError as e:
            logger.error(f"Error getting EC2 instances in {region}: {e}")
            return []

    def get_auto_scaling_groups(self, region: str) -> List[Dict]:
        """Get information about Auto Scaling groups in a region."""
        asg = self.session.client('autoscaling', region_name=region, config=boto3_config)
        try:
            groups = asg.describe_auto_scaling_groups()
            return [{
                'AutoScalingGroupName': group['AutoScalingGroupName'],
                'DesiredCapacity': group['DesiredCapacity'],
                'MinSize': group['MinSize'],
                'MaxSize': group['MaxSize'],
                'InstanceCount': len(group['Instances']),
                'AvailabilityZones': group['AvailabilityZones'],
                'HealthCheckType': group['HealthCheckType'],
                'LaunchTemplate': group.get('LaunchTemplate', {}).get('LaunchTemplateName', 'N/A'),
                'Status': 'Active' if len(group['Instances']) > 0 else 'Inactive'
            } for group in groups['AutoScalingGroups']]
        except ClientError as e:
            logger.error(f"Error getting Auto Scaling groups in {region}: {e}")
            return []

    def get_launch_templates(self, region: str) -> List[Dict]:
        """Get information about Launch Templates in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            templates = ec2.describe_launch_templates()
            template_info = []
            for template in templates['LaunchTemplates']:
                try:
                    # Get the default version details
                    version = ec2.describe_launch_template_versions(
                        LaunchTemplateId=template['LaunchTemplateId'],
                        Versions=['$Default']
                    )['LaunchTemplateVersions'][0]
                    
                    template_info.append({
                        'LaunchTemplateName': template['LaunchTemplateName'],
                        'LaunchTemplateId': template['LaunchTemplateId'],
                        'DefaultVersion': template['DefaultVersionNumber'],
                        'LatestVersion': template['LatestVersionNumber'],
                        'CreateTime': template['CreateTime'].isoformat(),
                        'InstanceType': version['LaunchTemplateData'].get('InstanceType', 'N/A'),
                        'ImageId': version['LaunchTemplateData'].get('ImageId', 'N/A')
                    })
                except ClientError:
                    continue
            return template_info
        except ClientError as e:
            logger.error(f"Error getting Launch Templates in {region}: {e}")
            return []

    def get_ecs_info(self, region: str) -> Dict[str, List[Dict]]:
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
                    services = []
                    paginator = ecs.get_paginator('list_services')
                    for page in paginator.paginate(cluster=cluster_arn):
                        if page['serviceArns']:
                            service_details = ecs.describe_services(
                                cluster=cluster_arn,
                                services=page['serviceArns']
                            )['services']
                            services.extend([{
                                'ServiceName': service['serviceName'],
                                'Status': service['status'],
                                'DesiredCount': service['desiredCount'],
                                'RunningCount': service['runningCount'],
                                'TaskDefinition': service['taskDefinition']
                            } for service in service_details])
                    
                    cluster_info.append({
                        'ClusterName': cluster['clusterName'],
                        'ClusterArn': cluster['clusterArn'],
                        'Status': cluster['status'],
                        'ActiveServices': len(services),
                        'RunningTasks': cluster['runningTasksCount'],
                        'PendingTasks': cluster['pendingTasksCount'],
                        'ContainerInstances': cluster['registeredContainerInstancesCount'],
                        'Services': services
                    })
                except ClientError:
                    continue
            
            return cluster_info
        except ClientError as e:
            logger.error(f"Error getting ECS information in {region}: {e}")
            return []

    def get_eks_clusters(self, region: str) -> List[Dict]:
        """Get information about EKS clusters in a region."""
        eks = self.session.client('eks', region_name=region, config=boto3_config)
        try:
            clusters = eks.list_clusters()
            cluster_info = []
            for cluster_name in clusters['clusters']:
                try:
                    cluster = eks.describe_cluster(name=cluster_name)['cluster']
                    cluster_info.append({
                        'Name': cluster['name'],
                        'Status': cluster['status'],
                        'Version': cluster['version'],
                        'Endpoint': cluster['endpoint'],
                        'PlatformVersion': cluster['platformVersion'],
                        'VpcId': cluster['resourcesVpcConfig']['vpcId'],
                        'SecurityGroups': cluster['resourcesVpcConfig'].get('clusterSecurityGroupId', 'N/A'),
                        'Subnets': cluster['resourcesVpcConfig']['subnetIds']
                    })
                except ClientError:
                    continue
            return cluster_info
        except ClientError as e:
            logger.error(f"Error getting EKS clusters in {region}: {e}")
            return []

    def get_lambda_functions(self, region: str) -> List[Dict]:
        """Get information about Lambda functions in a region."""
        lambda_client = self.session.client('lambda', region_name=region, config=boto3_config)
        try:
            functions = []
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    functions.append({
                        'FunctionName': function['FunctionName'],
                        'Runtime': function['Runtime'],
                        'Memory': function['MemorySize'],
                        'Timeout': function['Timeout'],
                        'LastModified': function['LastModified'],
                        'Handler': function['Handler'],
                        'Role': function['Role'],
                        'Environment': function.get('Environment', {}).get('Variables', {}),
                        'VpcConfig': function.get('VpcConfig', {})
                    })
            return functions
        except ClientError as e:
            logger.error(f"Error getting Lambda functions in {region}: {e}")
            return []

    def get_ecr_repositories(self, region: str) -> List[Dict]:
        """Get information about ECR repositories in a region."""
        ecr = self.session.client('ecr', region_name=region, config=boto3_config)
        try:
            repos = ecr.describe_repositories()
            repo_info = []
            for repo in repos['repositories']:
                try:
                    # Get image details for each repository
                    images = ecr.describe_images(
                        repositoryName=repo['repositoryName'],
                        maxResults=100
                    )
                    
                    repo_info.append({
                        'RepositoryName': repo['repositoryName'],
                        'RepositoryUri': repo['repositoryUri'],
                        'CreatedAt': repo['createdAt'].isoformat(),
                        'ImageCount': len(images.get('imageDetails', [])),
                        'ImageTagMutability': repo['imageTagMutability'],
                        'EncryptionType': repo.get('encryptionConfiguration', {}).get('encryptionType', 'N/A')
                    })
                except ClientError:
                    continue
            return repo_info
        except ClientError as e:
            logger.error(f"Error getting ECR repositories in {region}: {e}")
            return [] 
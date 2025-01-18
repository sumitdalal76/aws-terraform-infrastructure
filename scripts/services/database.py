from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class DatabaseServices:
    def __init__(self, session):
        self.session = session

    def get_ebs_volumes(self, region: str) -> List[Dict]:
        """Get information about EBS volumes in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            volumes = ec2.describe_volumes()
            return [{
                'VolumeId': vol['VolumeId'],
                'Size': vol['Size'],
                'VolumeType': vol['VolumeType'],
                'State': vol['State'],
                'Encrypted': vol['Encrypted'],
                'IOPS': vol.get('Iops', 'N/A'),
                'AvailabilityZone': vol['AvailabilityZone'],
                'Attachments': [{
                    'InstanceId': att['InstanceId'],
                    'State': att['State'],
                    'Device': att['Device']
                } for att in vol['Attachments']],
                'Tags': vol.get('Tags', [])
            } for vol in volumes['Volumes']]
        except ClientError as e:
            logger.error(f"Error getting EBS volumes in {region}: {e}")
            return []

    def get_efs_filesystems(self, region: str) -> List[Dict]:
        """Get information about EFS file systems in a region."""
        efs = self.session.client('efs', region_name=region, config=boto3_config)
        try:
            filesystems = efs.describe_file_systems()
            fs_info = []
            for fs in filesystems['FileSystems']:
                try:
                    # Get mount targets for each file system
                    mount_targets = efs.describe_mount_targets(FileSystemId=fs['FileSystemId'])
                    fs_info.append({
                        'FileSystemId': fs['FileSystemId'],
                        'Name': next((tag['Value'] for tag in fs.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                        'Size': fs['SizeInBytes']['Value'],
                        'LifeCycleState': fs['LifeCycleState'],
                        'PerformanceMode': fs['PerformanceMode'],
                        'Encrypted': fs['Encrypted'],
                        'ThroughputMode': fs['ThroughputMode'],
                        'MountTargets': len(mount_targets['MountTargets'])
                    })
                except ClientError:
                    continue
            return fs_info
        except ClientError as e:
            logger.error(f"Error getting EFS file systems in {region}: {e}")
            return []

    def get_rds_instances(self, region: str) -> Dict[str, List[Dict]]:
        """Get information about RDS instances and clusters in a region."""
        rds = self.session.client('rds', region_name=region, config=boto3_config)
        try:
            # Get DB instances
            instances = rds.describe_db_instances()
            instance_info = [{
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'EngineVersion': instance['EngineVersion'],
                'DBInstanceClass': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus'],
                'Endpoint': instance.get('Endpoint', {}).get('Address', 'N/A'),
                'MultiAZ': instance['MultiAZ'],
                'StorageType': instance['StorageType'],
                'AllocatedStorage': instance['AllocatedStorage']
            } for instance in instances['DBInstances']]

            # Get DB clusters
            try:
                clusters = rds.describe_db_clusters()
                cluster_info = [{
                    'DBClusterIdentifier': cluster['DBClusterIdentifier'],
                    'Engine': cluster['Engine'],
                    'EngineVersion': cluster['EngineVersion'],
                    'Status': cluster['Status'],
                    'MultiAZ': cluster.get('MultiAZ', False),
                    'ReaderEndpoint': cluster.get('ReaderEndpoint', 'N/A'),
                    'WriterEndpoint': cluster.get('Endpoint', 'N/A'),
                    'DatabaseName': cluster.get('DatabaseName', 'N/A'),
                    'InstanceCount': len(cluster.get('DBClusterMembers', []))
                } for cluster in clusters['DBClusters']]
            except ClientError:
                cluster_info = []

            return {
                'instances': instance_info,
                'clusters': cluster_info
            }
        except ClientError as e:
            logger.error(f"Error getting RDS information in {region}: {e}")
            return {'instances': [], 'clusters': []}

    def get_dynamodb_tables(self, region: str) -> List[Dict]:
        """Get information about DynamoDB tables in a region."""
        dynamodb = self.session.client('dynamodb', region_name=region, config=boto3_config)
        try:
            tables = dynamodb.list_tables()
            table_info = []
            for table_name in tables['TableNames']:
                try:
                    table = dynamodb.describe_table(TableName=table_name)['Table']
                    table_info.append({
                        'TableName': table['TableName'],
                        'Status': table['TableStatus'],
                        'ItemCount': table.get('ItemCount', 0),
                        'SizeBytes': table.get('TableSizeBytes', 0),
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': table['ProvisionedThroughput'].get('ReadCapacityUnits', 0),
                            'WriteCapacityUnits': table['ProvisionedThroughput'].get('WriteCapacityUnits', 0)
                        },
                        'BillingMode': table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED'),
                        'GlobalSecondaryIndexes': len(table.get('GlobalSecondaryIndexes', [])),
                        'LocalSecondaryIndexes': len(table.get('LocalSecondaryIndexes', []))
                    })
                except ClientError:
                    continue
            return table_info
        except ClientError as e:
            logger.error(f"Error getting DynamoDB tables in {region}: {e}")
            return []

    def get_elasticache_clusters(self, region: str) -> List[Dict]:
        """Get information about ElastiCache clusters in a region."""
        elasticache = self.session.client('elasticache', region_name=region, config=boto3_config)
        try:
            clusters = elasticache.describe_cache_clusters(ShowCacheNodeInfo=True)
            return [{
                'CacheClusterId': cluster['CacheClusterId'],
                'Engine': cluster['Engine'],
                'EngineVersion': cluster['EngineVersion'],
                'CacheNodeType': cluster['CacheNodeType'],
                'NumCacheNodes': cluster['NumCacheNodes'],
                'Status': cluster['CacheClusterStatus'],
                'PreferredAvailabilityZone': cluster.get('PreferredAvailabilityZone', 'N/A'),
                'CacheSubnetGroup': cluster.get('CacheSubnetGroupName', 'N/A'),
                'AutoMinorVersionUpgrade': cluster.get('AutoMinorVersionUpgrade', False)
            } for cluster in clusters['CacheClusters']]
        except ClientError as e:
            logger.error(f"Error getting ElastiCache clusters in {region}: {e}")
            return []

    def get_s3_bucket_policies(self) -> List[Dict]:
        """Get information about S3 bucket policies."""
        s3 = self.session.client('s3', config=boto3_config)
        try:
            buckets = s3.list_buckets()['Buckets']
            policy_info = []
            for bucket in buckets:
                try:
                    policy = s3.get_bucket_policy(Bucket=bucket['Name'])
                    policy_info.append({
                        'BucketName': bucket['Name'],
                        'PolicyExists': True,
                        'Policy': policy['Policy']
                    })
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                        policy_info.append({
                            'BucketName': bucket['Name'],
                            'PolicyExists': False,
                            'Policy': 'No policy attached'
                        })
                    continue
            return policy_info
        except ClientError as e:
            logger.error(f"Error getting S3 bucket policies: {e}")
            return [] 
from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from ..utils.aws_utils import boto3_config, make_api_call

logger = logging.getLogger(__name__)

class DatabaseServices:
    def __init__(self, session):
        self.session = session

    def get_rds_instances(self, region: str) -> List[Dict]:
        """Get information about RDS instances in a region."""
        rds = self.session.client('rds', region_name=region, config=boto3_config)
        try:
            instances = rds.describe_db_instances()
            return [{
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'InstanceClass': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus'],
                'Endpoint': instance.get('Endpoint', {}).get('Address', 'N/A'),
                'MultiAZ': instance['MultiAZ']
            } for instance in instances['DBInstances']]
        except ClientError as e:
            logger.error(f"Error getting RDS instances in {region}: {e}")
            return []

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
                        'ProvisionedThroughput': f"Read: {table['ProvisionedThroughput'].get('ReadCapacityUnits', 0)}, "
                                               f"Write: {table['ProvisionedThroughput'].get('WriteCapacityUnits', 0)}"
                    })
                except ClientError:
                    continue
            return table_info
        except ClientError as e:
            logger.error(f"Error getting DynamoDB tables in {region}: {e}")
            return [] 
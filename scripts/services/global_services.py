from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from ..utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class GlobalServices:
    def __init__(self, session):
        self.session = session

    def get_s3_buckets(self) -> List[Dict]:
        """Get information about S3 buckets."""
        s3 = self.session.client('s3', config=boto3_config)
        try:
            buckets = s3.list_buckets()
            return [{
                'Name': bucket['Name'],
                'CreationDate': bucket['CreationDate'].isoformat()
            } for bucket in buckets['Buckets']]
        except ClientError as e:
            logger.error(f"Error getting S3 buckets: {e}")
            return []

    def get_route53_info(self) -> List[Dict]:
        """Get information about Route53 hosted zones."""
        route53 = self.session.client('route53', config=boto3_config)
        try:
            zones = route53.list_hosted_zones()
            return [{
                'Id': zone['Id'],
                'Name': zone['Name'],
                'Private': zone['Config']['PrivateZone'],
                'RecordCount': zone['ResourceRecordSetCount']
            } for zone in zones['HostedZones']]
        except ClientError as e:
            logger.error(f"Error getting Route53 zones: {e}")
            return [] 
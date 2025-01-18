from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from ..utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class NetworkServices:
    def __init__(self, session):
        self.session = session

    def get_vpcs(self, region: str) -> List[Dict]:
        """Get information about VPCs in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            vpcs = ec2.describe_vpcs()
            return [{
                'VpcId': vpc['VpcId'],
                'CidrBlock': vpc['CidrBlock'],
                'IsDefault': vpc['IsDefault'],
                'State': vpc['State'],
                'Tags': vpc.get('Tags', [])
            } for vpc in vpcs['Vpcs']]
        except ClientError as e:
            logger.error(f"Error getting VPCs in {region}: {e}")
            return []

    def get_elb_info(self, region: str) -> List[Dict]:
        """Get information about Elastic Load Balancers in a region."""
        elb = self.session.client('elbv2', region_name=region, config=boto3_config)
        try:
            load_balancers = elb.describe_load_balancers()
            return [{
                'LoadBalancerName': lb['LoadBalancerName'],
                'DNSName': lb['DNSName'],
                'Type': lb['Type'],
                'Scheme': lb['Scheme'],
                'State': lb['State']['Code'],
                'VpcId': lb.get('VpcId', 'N/A')
            } for lb in load_balancers['LoadBalancers']]
        except ClientError as e:
            logger.error(f"Error getting ELBs in {region}: {e}")
            return [] 
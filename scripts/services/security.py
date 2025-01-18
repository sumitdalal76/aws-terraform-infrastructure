from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from ..utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class SecurityServices:
    def __init__(self, session):
        self.session = session

    def get_security_groups(self, region: str) -> List[Dict]:
        """Get information about Security Groups in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            sgs = ec2.describe_security_groups()
            return [{
                'GroupId': sg['GroupId'],
                'GroupName': sg['GroupName'],
                'Description': sg['Description'],
                'VpcId': sg.get('VpcId', 'N/A'),
                'InboundRules': sg['IpPermissions'],
                'OutboundRules': sg['IpPermissionsEgress']
            } for sg in sgs['SecurityGroups']]
        except ClientError as e:
            logger.error(f"Error getting Security Groups in {region}: {e}")
            return []

    def get_acm_certificates(self, region: str) -> List[Dict]:
        """Get information about ACM certificates in a region."""
        acm = self.session.client('acm', region_name=region, config=boto3_config)
        try:
            certs = acm.list_certificates()
            return [{
                'CertificateArn': cert['CertificateArn'],
                'DomainName': cert['DomainName'],
                'Status': cert['Status']
            } for cert in certs['CertificateSummaryList']]
        except ClientError as e:
            logger.error(f"Error getting ACM certificates in {region}: {e}")
            return []

    def get_kms_keys(self, region: str) -> List[Dict]:
        """Get information about KMS keys in a region."""
        kms = self.session.client('kms', region_name=region, config=boto3_config)
        try:
            keys = kms.list_keys()
            key_info = []
            for key in keys['Keys']:
                try:
                    desc = kms.describe_key(KeyId=key['KeyId'])['KeyMetadata']
                    key_info.append({
                        'KeyId': desc['KeyId'],
                        'Arn': desc['Arn'],
                        'State': desc['KeyState'],
                        'Description': desc.get('Description', 'N/A')
                    })
                except ClientError:
                    continue
            return key_info
        except ClientError as e:
            logger.error(f"Error getting KMS keys in {region}: {e}")
            return [] 
from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config

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
                'InboundRules': [{
                    'Protocol': rule.get('IpProtocol', 'All'),
                    'FromPort': rule.get('FromPort', 'All'),
                    'ToPort': rule.get('ToPort', 'All'),
                    'Source': [ip.get('CidrIp', '') or ip.get('GroupId', '') for ip in rule.get('IpRanges', []) + rule.get('UserIdGroupPairs', [])]
                } for rule in sg['IpPermissions']],
                'OutboundRules': [{
                    'Protocol': rule.get('IpProtocol', 'All'),
                    'FromPort': rule.get('FromPort', 'All'),
                    'ToPort': rule.get('ToPort', 'All'),
                    'Destination': [ip.get('CidrIp', '') or ip.get('GroupId', '') for ip in rule.get('IpRanges', []) + rule.get('UserIdGroupPairs', [])]
                } for rule in sg['IpPermissionsEgress']]
            } for sg in sgs['SecurityGroups']]
        except ClientError as e:
            logger.error(f"Error getting Security Groups in {region}: {e}")
            return []

    def get_network_acls(self, region: str) -> List[Dict]:
        """Get information about Network ACLs in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            acls = ec2.describe_network_acls()
            return [{
                'NetworkAclId': acl['NetworkAclId'],
                'VpcId': acl['VpcId'],
                'IsDefault': acl['IsDefault'],
                'Entries': [{
                    'RuleNumber': entry['RuleNumber'],
                    'Protocol': entry['Protocol'],
                    'RuleAction': entry['RuleAction'],
                    'Egress': entry['Egress'],
                    'CidrBlock': entry.get('CidrBlock', 'N/A')
                } for entry in acl['Entries']],
                'Associations': [assoc['SubnetId'] for assoc in acl['Associations']]
            } for acl in acls['NetworkAcls']]
        except ClientError as e:
            logger.error(f"Error getting Network ACLs in {region}: {e}")
            return []

    def get_acm_certificates(self, region: str) -> List[Dict]:
        """Get information about ACM certificates in a region."""
        acm = self.session.client('acm', region_name=region, config=boto3_config)
        try:
            certs = acm.list_certificates()
            cert_details = []
            for cert in certs['CertificateSummaryList']:
                try:
                    details = acm.describe_certificate(CertificateArn=cert['CertificateArn'])['Certificate']
                    cert_details.append({
                        'CertificateArn': details['CertificateArn'],
                        'DomainName': details['DomainName'],
                        'Status': details['Status'],
                        'Type': details['Type'],
                        'InUseBy': details.get('InUseBy', []),
                        'ExpiresOn': details.get('NotAfter', 'N/A')
                    })
                except ClientError:
                    continue
            return cert_details
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
                    aliases = kms.list_aliases(KeyId=key['KeyId'])['Aliases']
                    key_info.append({
                        'KeyId': desc['KeyId'],
                        'Arn': desc['Arn'],
                        'State': desc['KeyState'],
                        'Description': desc.get('Description', 'N/A'),
                        'Enabled': desc['Enabled'],
                        'KeyManager': desc['KeyManager'],
                        'Aliases': [alias['AliasName'] for alias in aliases]
                    })
                except ClientError:
                    continue
            return key_info
        except ClientError as e:
            logger.error(f"Error getting KMS keys in {region}: {e}")
            return []

    def get_secrets(self, region: str) -> List[Dict]:
        """Get information about Secrets Manager secrets in a region."""
        secrets = self.session.client('secretsmanager', region_name=region, config=boto3_config)
        try:
            secret_list = secrets.list_secrets()
            return [{
                'Name': secret['Name'],
                'ARN': secret['ARN'],
                'Description': secret.get('Description', 'N/A'),
                'LastChangedDate': secret.get('LastChangedDate', 'N/A').isoformat() if secret.get('LastChangedDate') else 'N/A',
                'LastAccessedDate': secret.get('LastAccessedDate', 'N/A').isoformat() if secret.get('LastAccessedDate') else 'N/A',
                'Tags': secret.get('Tags', [])
            } for secret in secret_list['SecretList']]
        except ClientError as e:
            logger.error(f"Error getting Secrets Manager secrets in {region}: {e}")
            return []

    def get_iam_policies(self, region: str = None) -> List[Dict]:
        """Get information about IAM policies."""
        iam = self.session.client('iam', config=boto3_config)
        try:
            policies = iam.list_policies(Scope='Local')  # Only get customer managed policies
            policy_info = []
            for policy in policies['Policies']:
                try:
                    versions = iam.list_policy_versions(PolicyArn=policy['Arn'])
                    policy_info.append({
                        'PolicyName': policy['PolicyName'],
                        'PolicyId': policy['PolicyId'],
                        'Arn': policy['Arn'],
                        'Description': policy.get('Description', 'N/A'),
                        'VersionCount': len(versions['Versions']),
                        'AttachmentCount': policy['AttachmentCount']
                    })
                except ClientError:
                    continue
            return policy_info
        except ClientError as e:
            logger.error(f"Error getting IAM policies: {e}")
            return [] 
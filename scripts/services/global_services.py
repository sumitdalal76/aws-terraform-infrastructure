from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class GlobalServices:
    def __init__(self, session):
        self.session = session

    def get_s3_buckets(self) -> List[Dict]:
        """Get information about S3 buckets and their policies."""
        s3 = self.session.client('s3', config=boto3_config)
        try:
            buckets = s3.list_buckets()
            bucket_info = []
            for bucket in buckets['Buckets']:
                info = {
                    'Name': bucket['Name'],
                    'CreationDate': bucket['CreationDate'].isoformat()
                }
                # Get bucket policy if exists
                try:
                    policy = s3.get_bucket_policy(Bucket=bucket['Name'])
                    info['Policy'] = policy.get('Policy', 'N/A')
                except ClientError:
                    info['Policy'] = 'No policy'
                bucket_info.append(info)
            return bucket_info
        except ClientError as e:
            logger.error(f"Error getting S3 buckets: {e}")
            return []

    def get_cloudfront_distributions(self) -> List[Dict]:
        """Get information about CloudFront distributions."""
        cloudfront = self.session.client('cloudfront', config=boto3_config)
        try:
            distributions = cloudfront.list_distributions()
            if 'DistributionList' in distributions:
                return [{
                    'Id': dist['Id'],
                    'DomainName': dist['DomainName'],
                    'Status': dist['Status'],
                    'Enabled': dist['Enabled'],
                    'Origins': [origin['DomainName'] for origin in dist['Origins']['Items']]
                } for dist in distributions['DistributionList'].get('Items', [])]
            return []
        except ClientError as e:
            logger.error(f"Error getting CloudFront distributions: {e}")
            return []

    def get_waf_info(self) -> Dict[str, List[Dict]]:
        """Get information about WAF rules and ACLs."""
        wafv2 = self.session.client('wafv2', config=boto3_config)
        try:
            # Get WAF web ACLs for both REGIONAL and CLOUDFRONT scopes
            acls = {}
            for scope in ['REGIONAL', 'CLOUDFRONT']:
                try:
                    acls[scope] = wafv2.list_web_acls(Scope=scope)['WebACLs']
                except ClientError:
                    acls[scope] = []

            return {
                'WebACLs': [{
                    'Name': acl['Name'],
                    'Id': acl['Id'],
                    'ARN': acl['ARN'],
                    'Scope': scope
                } for scope, scope_acls in acls.items() for acl in scope_acls]
            }
        except ClientError as e:
            logger.error(f"Error getting WAF information: {e}")
            return {'WebACLs': []}

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

    def get_iam_info(self) -> Dict[str, List[Dict]]:
        """Get information about IAM users, roles, and groups."""
        iam = self.session.client('iam', config=boto3_config)
        try:
            # Get Users
            users = [{
                'UserName': user['UserName'],
                'UserId': user['UserId'],
                'Arn': user['Arn'],
                'CreateDate': user['CreateDate'].isoformat()
            } for user in iam.list_users()['Users']]

            # Get Roles
            roles = [{
                'RoleName': role['RoleName'],
                'RoleId': role['RoleId'],
                'Arn': role['Arn'],
                'CreateDate': role['CreateDate'].isoformat(),
                'Description': role.get('Description', 'N/A')
            } for role in iam.list_roles()['Roles']]

            # Get Groups
            groups = [{
                'GroupName': group['GroupName'],
                'GroupId': group['GroupId'],
                'Arn': group['Arn'],
                'CreateDate': group['CreateDate'].isoformat()
            } for group in iam.list_groups()['Groups']]

            return {
                'users': users,
                'roles': roles,
                'groups': groups
            }
        except ClientError as e:
            logger.error(f"Error getting IAM information: {e}")
            return {'users': [], 'roles': [], 'groups': []} 
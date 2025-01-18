from typing import Dict, List
from botocore.exceptions import ClientError
import logging
from utils.aws_utils import boto3_config

logger = logging.getLogger(__name__)

class NetworkServices:
    def __init__(self, session):
        self.session = session

    def get_vpcs_and_subnets(self, region: str) -> Dict[str, List[Dict]]:
        """Get information about VPCs and their subnets in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            vpcs = ec2.describe_vpcs()
            subnets = ec2.describe_subnets()
            
            return {
                'vpcs': [{
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State'],
                    'IsDefault': vpc['IsDefault'],
                    'Tags': vpc.get('Tags', [])
                } for vpc in vpcs['Vpcs']],
                'subnets': [{
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'CidrBlock': subnet['CidrBlock'],
                    'AvailabilityZone': subnet['AvailabilityZone'],
                    'State': subnet['State'],
                    'Tags': subnet.get('Tags', [])
                } for subnet in subnets['Subnets']]
            }
        except ClientError as e:
            logger.error(f"Error getting VPCs and Subnets in {region}: {e}")
            return {'vpcs': [], 'subnets': []}

    def get_internet_gateways(self, region: str) -> List[Dict]:
        """Get information about Internet Gateways in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            igws = ec2.describe_internet_gateways()
            return [{
                'InternetGatewayId': igw['InternetGatewayId'],
                'Attachments': igw['Attachments'],
                'Tags': igw.get('Tags', [])
            } for igw in igws['InternetGateways']]
        except ClientError as e:
            logger.error(f"Error getting Internet Gateways in {region}: {e}")
            return []

    def get_nat_gateways(self, region: str) -> List[Dict]:
        """Get information about NAT Gateways in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            nat_gateways = ec2.describe_nat_gateways()
            return [{
                'NatGatewayId': nat['NatGatewayId'],
                'SubnetId': nat['SubnetId'],
                'VpcId': nat['VpcId'],
                'State': nat['State'],
                'Tags': nat.get('Tags', [])
            } for nat in nat_gateways['NatGateways']]
        except ClientError as e:
            logger.error(f"Error getting NAT Gateways in {region}: {e}")
            return []

    def get_transit_gateways(self, region: str) -> List[Dict]:
        """Get information about Transit Gateways in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            tgws = ec2.describe_transit_gateways()
            return [{
                'TransitGatewayId': tgw['TransitGatewayId'],
                'State': tgw['State'],
                'OwnerId': tgw['OwnerId'],
                'Description': tgw.get('Description', 'N/A'),
                'Tags': tgw.get('Tags', [])
            } for tgw in tgws['TransitGateways']]
        except ClientError as e:
            logger.error(f"Error getting Transit Gateways in {region}: {e}")
            return []

    def get_vpc_endpoints(self, region: str) -> List[Dict]:
        """Get information about VPC Endpoints in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            endpoints = ec2.describe_vpc_endpoints()
            return [{
                'VpcEndpointId': endpoint['VpcEndpointId'],
                'VpcId': endpoint['VpcId'],
                'ServiceName': endpoint['ServiceName'],
                'State': endpoint['State'],
                'Type': endpoint['VpcEndpointType'],
                'Tags': endpoint.get('Tags', [])
            } for endpoint in endpoints['VpcEndpoints']]
        except ClientError as e:
            logger.error(f"Error getting VPC Endpoints in {region}: {e}")
            return []

    def get_route_tables(self, region: str) -> List[Dict]:
        """Get information about Route Tables in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            route_tables = ec2.describe_route_tables()
            return [{
                'RouteTableId': rt['RouteTableId'],
                'VpcId': rt['VpcId'],
                'Routes': rt['Routes'],
                'Associations': rt['Associations'],
                'Tags': rt.get('Tags', [])
            } for rt in route_tables['RouteTables']]
        except ClientError as e:
            logger.error(f"Error getting Route Tables in {region}: {e}")
            return []

    def get_network_interfaces(self, region: str) -> List[Dict]:
        """Get information about Network Interfaces in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            enis = ec2.describe_network_interfaces()
            return [{
                'NetworkInterfaceId': eni['NetworkInterfaceId'],
                'SubnetId': eni['SubnetId'],
                'VpcId': eni['VpcId'],
                'PrivateIpAddress': eni['PrivateIpAddress'],
                'Status': eni['Status'],
                'Tags': eni.get('Tags', [])
            } for eni in enis['NetworkInterfaces']]
        except ClientError as e:
            logger.error(f"Error getting Network Interfaces in {region}: {e}")
            return []

    def get_elastic_ips(self, region: str) -> List[Dict]:
        """Get information about Elastic IPs in a region."""
        ec2 = self.session.client('ec2', region_name=region, config=boto3_config)
        try:
            eips = ec2.describe_addresses()
            return [{
                'PublicIp': eip['PublicIp'],
                'AllocationId': eip.get('AllocationId'),
                'InstanceId': eip.get('InstanceId', 'N/A'),
                'NetworkInterfaceId': eip.get('NetworkInterfaceId', 'N/A'),
                'Tags': eip.get('Tags', [])
            } for eip in eips['Addresses']]
        except ClientError as e:
            logger.error(f"Error getting Elastic IPs in {region}: {e}")
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
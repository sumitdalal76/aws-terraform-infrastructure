#!/usr/bin/env python3
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, WaiterError
import json
import time
from typing import Dict, List
import logging
from rich.console import Console
from rich.table import Table
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Configure boto3 with retries
boto3_config = Config(
    retries = dict(
        max_attempts = 3,  # Number of retry attempts
        mode = 'adaptive'  # Exponential backoff
    ),
    connect_timeout = 10,  # Connection timeout in seconds
    read_timeout = 30     # Read timeout in seconds
)

class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = self._get_regions()
        self.inventory_data = {}
        
    def _get_regions(self) -> List[str]:
        """Get list of all AWS regions."""
        try:
            ec2 = self.session.client('ec2', config=boto3_config)
            regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
            return regions
        except ClientError as e:
            logger.error(f"Error getting regions: {e}")
            return []

    def _make_api_call(self, func, *args, **kwargs):
        """Generic method to make AWS API calls with retry logic."""
        max_retries = 3
        retry_delay = 1  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                if e.response['Error']['Code'] in ['RequestLimitExceeded', 'Throttling']:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for API call: {e}")
                        return None
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"API throttling, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error in API call: {e}")
                return None

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

    def get_rds_instances(self, region: str) -> List[Dict]:
        """Get detailed information about RDS instances in a region."""
        rds = self.session.client('rds', region_name=region)
        try:
            instances = rds.describe_db_instances()
            return [{
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'DBInstanceClass': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus']
            } for instance in instances['DBInstances']]
        except ClientError as e:
            logger.error(f"Error getting RDS instances in {region}: {e}")
            return []

    def get_s3_buckets(self) -> List[Dict]:
        """Get information about S3 buckets."""
        s3 = self.session.client('s3')
        try:
            buckets = s3.list_buckets()['Buckets']
            return [{
                'Name': bucket['Name'],
                'CreationDate': bucket['CreationDate'].isoformat()
            } for bucket in buckets]
        except ClientError as e:
            logger.error(f"Error getting S3 buckets: {e}")
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

    def get_vpcs(self, region: str) -> List[Dict]:
        """Get information about VPCs in a region."""
        ec2 = self.session.client('ec2', region_name=region)
        try:
            vpcs = ec2.describe_vpcs()
            return [{
                'Name': next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                'VpcId': vpc['VpcId'],
                'CidrBlock': vpc['CidrBlock'],
                'State': vpc['State'],
                'IsDefault': vpc['IsDefault'],
                'Tags': vpc.get('Tags', [])
            } for vpc in vpcs['Vpcs']]
        except ClientError as e:
            logger.error(f"Error getting VPCs in {region}: {e}")
            return []

    def get_dynamodb_tables(self, region: str) -> List[Dict]:
        """Get information about DynamoDB tables in a region."""
        dynamodb = self.session.client('dynamodb', region_name=region)
        try:
            tables = dynamodb.list_tables()['TableNames']
            table_info = []
            for table_name in tables:
                table = dynamodb.describe_table(TableName=table_name)['Table']
                table_info.append({
                    'TableName': table['TableName'],
                    'Status': table['TableStatus'],
                    'ItemCount': table.get('ItemCount', 0),
                    'SizeBytes': table.get('TableSizeBytes', 0),
                    'ProvisionedThroughput': f"Read: {table['ProvisionedThroughput']['ReadCapacityUnits']}, Write: {table['ProvisionedThroughput']['WriteCapacityUnits']}"
                })
            return table_info
        except ClientError as e:
            logger.error(f"Error getting DynamoDB tables in {region}: {e}")
            return []

    def get_elb_info(self, region: str) -> Dict:
        """Get information about all types of load balancers in a region."""
        try:
            elbv2_client = self.session.client('elbv2', region_name=region)
            elb_client = self.session.client('elb', region_name=region)
            
            # Get ALB/NLB (v2)
            modern_lbs = elbv2_client.describe_load_balancers()['LoadBalancers']
            modern_lb_info = [{
                'LoadBalancerName': lb['LoadBalancerName'],
                'DNSName': lb['DNSName'],
                'Type': lb['Type'],
                'State': lb['State']['Code']
            } for lb in modern_lbs]
            
            # Get Classic LB
            classic_lbs = elb_client.describe_load_balancers()['LoadBalancerDescriptions']
            classic_lb_info = [{
                'LoadBalancerName': lb['LoadBalancerName'],
                'DNSName': lb['DNSName'],
                'Type': 'classic',
                'State': 'active'
            } for lb in classic_lbs]
            
            return modern_lb_info + classic_lb_info
        except ClientError as e:
            logger.error(f"Error getting ELB information in {region}: {e}")
            return []

    def get_ecs_info(self, region: str) -> Dict:
        """Get information about ECS clusters and services."""
        try:
            ecs = self.session.client('ecs', region_name=region)
            clusters = ecs.list_clusters()['clusterArns']
            
            cluster_info = []
            for cluster_arn in clusters:
                services = ecs.list_services(cluster=cluster_arn)['serviceArns']
                cluster_info.append({
                    'ClusterArn': cluster_arn,
                    'ServiceCount': len(services)
                })
            return cluster_info
        except ClientError as e:
            logger.error(f"Error getting ECS information in {region}: {e}")
            return []

    def get_route53_info(self) -> List[Dict]:
        """Get information about Route53 hosted zones."""
        try:
            route53 = self.session.client('route53')
            zones = route53.list_hosted_zones()['HostedZones']
            return [{
                'Name': zone['Name'],
                'Id': zone['Id'],
                'RecordCount': zone['ResourceRecordSetCount'],
                'Private': zone['Config']['PrivateZone']
            } for zone in zones]
        except ClientError as e:
            logger.error(f"Error getting Route53 information: {e}")
            return []

    def print_table(self, title: str, data: List[Dict]):
        """Print data in a formatted table."""
        if not data:
            return

        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Add columns based on the first item's keys
        columns = list(data[0].keys())
        for column in columns:
            table.add_column(column)
        
        # Add rows
        for item in data:
            row = [str(item[column]) for column in columns]
            table.add_row(*row)
        
        console.print(table)
        console.print("\n")

    def print_json_output(self, data: Dict, title: str = None):
        """Print data in JSON format to console."""
        if title:
            console.print(f"\n[bold yellow]{title}:[/bold yellow]")
        console.print_json(json.dumps(data, indent=2))
        console.print("")

    def print_consolidated_table(self, inventory_data: Dict):
        """Print a consolidated view of all resources in table format."""
        console.print("\n[bold cyan]=== AWS Resource Summary ===[/bold cyan]\n")

        # Global Resources Summary
        if inventory_data['s3_buckets'] or inventory_data['route53_zones']:
            console.print("[bold blue]Global Resources[/bold blue]")
            
            # S3 Buckets
            if inventory_data['s3_buckets']:
                s3_table = Table(title="S3 Buckets", show_header=True, header_style="bold magenta")
                s3_table.add_column("Bucket Name")
                s3_table.add_column("Creation Date")
                for bucket in inventory_data['s3_buckets']:
                    s3_table.add_row(bucket['Name'], bucket['CreationDate'])
                console.print(s3_table)
                console.print("\n")

            # Route53 Zones
            if inventory_data['route53_zones']:
                route53_table = Table(title="Route53 Hosted Zones", show_header=True, header_style="bold magenta")
                route53_table.add_column("Zone Name")
                route53_table.add_column("Zone ID")
                route53_table.add_column("Record Count")
                route53_table.add_column("Type")
                for zone in inventory_data['route53_zones']:
                    zone_type = "Private" if zone['Private'] else "Public"
                    route53_table.add_row(zone['Name'], zone['Id'], str(zone['RecordCount']), zone_type)
                console.print(route53_table)
                console.print("\n")

        # Regional Resources Summary
        console.print("[bold blue]Regional Resources[/bold blue]\n")
        
        for region, resources in inventory_data['regions'].items():
            has_resources = any(resource_list for resource_list in resources.values() if resource_list)
            
            if has_resources:
                console.print(f"[bold green]Region: {region}[/bold green]")
                
                # EC2 Instances
                if resources['ec2_instances']:
                    ec2_table = Table(title="EC2 Instances", show_header=True, header_style="bold magenta")
                    ec2_table.add_column("Instance ID")
                    ec2_table.add_column("Type")
                    ec2_table.add_column("State")
                    ec2_table.add_column("Launch Time")
                    ec2_table.add_column("Name")
                    
                    for instance in resources['ec2_instances']:
                        name = next((tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'Name'), 'N/A')
                        ec2_table.add_row(
                            instance['InstanceId'],
                            instance['InstanceType'],
                            instance['State'],
                            instance['LaunchTime'],
                            name
                        )
                    console.print(ec2_table)
                    console.print("\n")

                # DynamoDB Tables
                if resources['dynamodb_tables']:
                    dynamo_table = Table(title="DynamoDB Tables", show_header=True, header_style="bold magenta")
                    dynamo_table.add_column("Table Name")
                    dynamo_table.add_column("Status")
                    dynamo_table.add_column("Item Count")
                    dynamo_table.add_column("Size (Bytes)")
                    dynamo_table.add_column("Provisioned Throughput")
                    
                    for table in resources['dynamodb_tables']:
                        dynamo_table.add_row(
                            table['TableName'],
                            table['Status'],
                            str(table['ItemCount']),
                            str(table['SizeBytes']),
                            table['ProvisionedThroughput']
                        )
                    console.print(dynamo_table)
                    console.print("\n")

                # Add other resource tables here...

    def print_scan_scope(self):
        """Print the scope of the inventory scan."""
        console.print("\n[bold cyan]=== AWS Resource Inventory Scan Scope ===[/bold cyan]\n")

        services_table = Table(title="Services to Scan", show_header=True, header_style="bold magenta")
        services_table.add_column("Service Type")
        services_table.add_column("Resources")

        # Global Services
        services_table.add_row(
            "Global Services",
            "• IAM (Users, Roles, Groups)\n"
            "• S3 Buckets\n"
            "• Route53 Hosted Zones\n"
            "• CloudFront Distributions\n"
            "• WAF Rules & ACLs"
        )

        # Security Services
        services_table.add_row(
            "Security Services",
            "• Security Groups\n"
            "• Network ACLs\n"
            "• ACM Certificates\n"
            "• KMS Keys\n"
            "• Secrets Manager Secrets\n"
            "• IAM Roles & Policies"
        )

        # Compute & Containers
        services_table.add_row(
            "Compute & Containers",
            "• EC2 Instances\n"
            "• Auto Scaling Groups\n"
            "• Launch Templates\n"
            "• ECS Clusters & Services\n"
            "• EKS Clusters\n"
            "• Lambda Functions\n"
            "• ECR Repositories"
        )

        # Storage & Database
        services_table.add_row(
            "Storage & Database",
            "• EBS Volumes\n"
            "• EFS File Systems\n"
            "• RDS Instances & Clusters\n"
            "• DynamoDB Tables\n"
            "• ElastiCache Clusters\n"
            "• S3 Bucket Policies"
        )

        # Networking
        services_table.add_row(
            "Networking",
            "• VPCs & Subnets\n"
            "• Internet Gateways\n"
            "• NAT Gateways\n"
            "• Transit Gateways\n"
            "• VPC Endpoints\n"
            "• Route Tables\n"
            "• Network Interfaces\n"
            "• Elastic IPs"
        )

        # Load Balancing & DNS
        services_table.add_row(
            "Load Balancing & DNS",
            "• Application Load Balancers\n"
            "• Network Load Balancers\n"
            "• Classic Load Balancers\n"
            "• Target Groups\n"
            "• Route53 Records"
        )

        # Application Services
        services_table.add_row(
            "Application Services",
            "• API Gateway APIs\n"
            "• SNS Topics\n"
            "• SQS Queues\n"
            "• EventBridge Rules\n"
            "• Step Functions"
        )

        # Developer Tools
        services_table.add_row(
            "Developer Tools",
            "• CodeBuild Projects\n"
            "• CodePipeline Pipelines\n"
            "• CodeDeploy Applications\n"
            "• CloudWatch Logs Groups\n"
            "• CloudWatch Alarms"
        )

        console.print(services_table)
        console.print("\n")

    def get_security_groups(self, region: str) -> List[Dict]:
        """Get information about Security Groups in a region."""
        ec2 = self.session.client('ec2', region_name=region)
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
        acm = self.session.client('acm', region_name=region)
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
        kms = self.session.client('kms', region_name=region)
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

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        self.print_scan_scope()
        
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            's3_buckets': self._make_api_call(self.get_s3_buckets),
            'route53_zones': self._make_api_call(self.get_route53_info)
        }
        
        for region in self.regions:
            console.print(f"Scanning region: {region}", style="dim")
            
            # Collect all regional resources with error handling
            regional_data = {
                'vpcs': self._make_api_call(self.get_vpcs, region),
                'ec2_instances': self._make_api_call(self.get_ec2_instances, region),
                'rds_instances': self._make_api_call(self.get_rds_instances, region),
                'lambda_functions': self._make_api_call(self.get_lambda_functions, region),
                'dynamodb_tables': self._make_api_call(self.get_dynamodb_tables, region),
                'load_balancers': self._make_api_call(self.get_elb_info, region),
                'ecs_clusters': self._make_api_call(self.get_ecs_info, region),
                'security_groups': self._make_api_call(self.get_security_groups, region),
                'acm_certificates': self._make_api_call(self.get_acm_certificates, region),
                'kms_keys': self._make_api_call(self.get_kms_keys, region)
            }
            
            # Filter out None values from failed API calls
            self.inventory_data['regions'][region] = {
                k: v for k, v in regional_data.items() if v is not None
            }

        console.print("\n")  # Add spacing before the summary
        self.print_consolidated_table(self.inventory_data)
        return self.inventory_data

    def save_inventory(self, inventory: Dict, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    
    inventory = AWSResourceInventory()
    resources = inventory.generate_inventory()
    
    # Save only to JSON file, no console JSON output
    inventory.save_inventory(resources)
    
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
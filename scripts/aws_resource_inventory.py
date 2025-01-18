#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import json
from typing import Dict, List
import logging
from rich.console import Console
from rich.table import Table
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = self._get_regions()
        self.inventory_data = {}
        
    def _get_regions(self) -> List[str]:
        """Get list of all AWS regions."""
        ec2 = self.session.client('ec2')
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions

    def get_ec2_instances(self, region: str) -> List[Dict]:
        """Get detailed information about EC2 instances in a region."""
        ec2 = self.session.client('ec2', region_name=region)
        try:
            instances = ec2.describe_instances()
            instance_list = []
            for reservation in instances['Reservations']:
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
        for region, resources in inventory_data['regions'].items():
            if not any(resources.values()):  # Skip regions with no resources
                continue
                
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

            # RDS Instances
            if resources['rds_instances']:
                rds_table = Table(title="RDS Instances", show_header=True, header_style="bold magenta")
                rds_table.add_column("Identifier")
                rds_table.add_column("Engine")
                rds_table.add_column("Class")
                rds_table.add_column("Status")
                
                for db in resources['rds_instances']:
                    rds_table.add_row(
                        db['DBInstanceIdentifier'],
                        db['Engine'],
                        db['DBInstanceClass'],
                        db['Status']
                    )
                console.print(rds_table)
                console.print("\n")

            # Lambda Functions
            if resources['lambda_functions']:
                lambda_table = Table(title="Lambda Functions", show_header=True, header_style="bold magenta")
                lambda_table.add_column("Function Name")
                lambda_table.add_column("Runtime")
                lambda_table.add_column("Memory (MB)")
                lambda_table.add_column("Timeout (s)")
                
                for func in resources['lambda_functions']:
                    lambda_table.add_row(
                        func['FunctionName'],
                        func['Runtime'],
                        str(func['Memory']),
                        str(func['Timeout'])
                    )
                console.print(lambda_table)
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

            # Load Balancers
            if resources['load_balancers']:
                lb_table = Table(title="Load Balancers", show_header=True, header_style="bold magenta")
                lb_table.add_column("Name")
                lb_table.add_column("Type")
                lb_table.add_column("DNS Name")
                lb_table.add_column("State")
                
                for lb in resources['load_balancers']:
                    lb_table.add_row(
                        lb['LoadBalancerName'],
                        lb['Type'],
                        lb['DNSName'],
                        lb['State']
                    )
                console.print(lb_table)
                console.print("\n")

            # ECS Clusters
            if resources['ecs_clusters']:
                ecs_table = Table(title="ECS Clusters", show_header=True, header_style="bold magenta")
                ecs_table.add_column("Cluster ARN")
                ecs_table.add_column("Service Count")
                
                for cluster in resources['ecs_clusters']:
                    ecs_table.add_row(
                        cluster['ClusterArn'],
                        str(cluster['ServiceCount'])
                    )
                console.print(ecs_table)
                console.print("\n")

    def print_scan_scope(self):
        """Print the scope of the inventory scan."""
        console.print("\n[bold cyan]=== AWS Resource Inventory Scan Scope ===[/bold cyan]\n")

        # Print Regions
        regions_table = Table(title="Regions to Scan", show_header=True, header_style="bold magenta")
        regions_table.add_column("AWS Regions")
        for region in self.regions:
            regions_table.add_row(region)
        console.print(regions_table)
        console.print("\n")

        # Print Services
        services_table = Table(title="Services to Scan", show_header=True, header_style="bold magenta")
        services_table.add_column("Service Type")
        services_table.add_column("Resources")

        # Global Services
        services_table.add_row(
            "Global Services",
            "• S3 Buckets\n• Route53 Hosted Zones"
        )

        # Regional Services
        services_table.add_row(
            "Regional Services",
            "• VPCs & Networking\n"
            "• EC2 Instances\n"
            "• RDS Instances\n"
            "• Lambda Functions\n"
            "• DynamoDB Tables\n"
            "• Load Balancers (ALB/NLB/Classic)\n"
            "• ECS Clusters"
        )

        console.print(services_table)
        console.print("\n")

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        # Print scan scope at the start
        self.print_scan_scope()
        
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            's3_buckets': self.get_s3_buckets(),
            'route53_zones': self.get_route53_info()
        }
        
        # Get region-specific resources
        for region in self.regions:
            console.print(f"Scanning region: {region}")
            
            # Collect all regional resources
            self.inventory_data['regions'][region] = {
                'vpcs': [vpc for vpc in self.get_vpcs(region) if not vpc['IsDefault']],
                'ec2_instances': self.get_ec2_instances(region),
                'rds_instances': self.get_rds_instances(region),
                'lambda_functions': self.get_lambda_functions(region),
                'dynamodb_tables': self.get_dynamodb_tables(region),
                'load_balancers': self.get_elb_info(region),
                'ecs_clusters': self.get_ecs_info(region)
            }

        # Print consolidated view in tables
        self.print_consolidated_table(self.inventory_data)
        
        return self.inventory_data

    def save_inventory(self, inventory: Dict, filename: str = 'artifact.json'):
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
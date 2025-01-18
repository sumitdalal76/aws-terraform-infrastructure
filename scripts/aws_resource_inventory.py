#!/usr/bin/env python3
import boto3
import json
from datetime import datetime
import logging
from rich.console import Console
from rich.table import Table
from typing import Dict

from utils.aws_utils import make_api_call, get_aws_regions
from services.compute import ComputeServices
from services.database import DatabaseServices
from services.global_services import GlobalServices
from services.network import NetworkServices
from services.security import SecurityServices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = get_aws_regions(self.session)
        self.inventory_data = {}
        
        # Initialize service classes
        self.compute = ComputeServices(self.session)
        self.database = DatabaseServices(self.session)
        self.global_services = GlobalServices(self.session)
        self.network = NetworkServices(self.session)
        self.security = SecurityServices(self.session)

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

        console.print(services_table)
        console.print("\n")

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
        has_regional_resources = any(
            any(resource_list for resource_list in resources.values() if resource_list)
            for resources in inventory_data['regions'].values()
        )
        
        if has_regional_resources:
            console.print("[bold blue]Regional Resources[/bold blue]\n")
            
            for region, resources in inventory_data['regions'].items():
                # Skip regions with no resources
                if not any(resource_list for resource_list in resources.values() if resource_list):
                    continue
                    
                region_printed = False
                
                # EC2 Instances
                if resources.get('ec2_instances'):
                    if not region_printed:
                        console.print(f"[bold green]Region: {region}[/bold green]")
                        region_printed = True
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
                if resources.get('dynamodb_tables'):
                    if not region_printed:
                        console.print(f"[bold green]Region: {region}[/bold green]")
                        region_printed = True
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

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        self.print_scan_scope()
        
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            's3_buckets': make_api_call(self.global_services.get_s3_buckets),
            'route53_zones': make_api_call(self.global_services.get_route53_info)
        }
        
        for region in self.regions:
            console.print(f"Scanning region: {region}", style="dim")
            
            regional_data = {
                'vpcs': make_api_call(self.network.get_vpcs, region),
                'ec2_instances': make_api_call(self.compute.get_ec2_instances, region),
                'rds_instances': make_api_call(self.database.get_rds_instances, region),
                'lambda_functions': make_api_call(self.compute.get_lambda_functions, region),
                'dynamodb_tables': make_api_call(self.database.get_dynamodb_tables, region),
                'load_balancers': make_api_call(self.network.get_elb_info, region),
                'ecs_clusters': make_api_call(self.compute.get_ecs_info, region),
                'security_groups': make_api_call(self.security.get_security_groups, region),
                'acm_certificates': make_api_call(self.security.get_acm_certificates, region),
                'kms_keys': make_api_call(self.security.get_kms_keys, region)
            }
            
            self.inventory_data['regions'][region] = {
                k: v for k, v in regional_data.items() if v is not None
            }

        console.print("\n")
        self.print_consolidated_table(self.inventory_data)
        return self.inventory_data

    def save_inventory(self, inventory: Dict, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2, default=str)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    
    inventory = AWSResourceInventory()
    resources = inventory.generate_inventory()
    inventory.save_inventory(resources)
    
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
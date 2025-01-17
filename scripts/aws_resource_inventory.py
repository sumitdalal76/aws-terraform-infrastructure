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

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            's3_buckets': self.get_s3_buckets()
        }
        
        # Print S3 buckets table
        console.print("[bold blue]Global Resources[/bold blue]")
        self.print_table("S3 Buckets", self.inventory_data['s3_buckets'])
        
        # Get region-specific resources
        for region in self.regions:
            console.print(f"[bold green]Region: {region}[/bold green]")
            
            ec2_instances = self.get_ec2_instances(region)
            rds_instances = self.get_rds_instances(region)
            lambda_functions = self.get_lambda_functions(region)
            
            self.inventory_data['regions'][region] = {
                'ec2_instances': ec2_instances,
                'rds_instances': rds_instances,
                'lambda_functions': lambda_functions
            }
            
            # Print tables for each resource type
            self.print_table("EC2 Instances", ec2_instances)
            self.print_table("RDS Instances", rds_instances)
            self.print_table("Lambda Functions", lambda_functions)
        
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
    
    # Save both JSON and detailed report
    inventory.save_inventory(resources, 'aws_inventory.json')
    
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
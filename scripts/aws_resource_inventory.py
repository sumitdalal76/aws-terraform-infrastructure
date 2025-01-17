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

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            's3_buckets': self.get_s3_buckets()
        }
        
        console.print("\n[bold cyan]=== AWS Resource Inventory ===[/bold cyan]\n")
        
        # Print S3 buckets table
        console.print("[bold blue]Global Resources[/bold blue]")
        self.print_table("S3 Buckets", self.inventory_data['s3_buckets'])
        self.print_json_output(self.inventory_data['s3_buckets'], "S3 Buckets JSON")
        
        console.print("\n[bold cyan]=== Regional Resources ===[/bold cyan]\n")
        
        # Get region-specific resources
        for region in self.regions:
            console.print(f"\n[bold green]Scanning region: {region}[/bold green]")
            
            vpcs = self.get_vpcs(region)
            ec2_instances = self.get_ec2_instances(region)
            rds_instances = self.get_rds_instances(region)
            lambda_functions = self.get_lambda_functions(region)
            dynamodb_tables = self.get_dynamodb_tables(region)
            
            self.inventory_data['regions'][region] = {
                'vpcs': vpcs,
                'ec2_instances': ec2_instances,
                'rds_instances': rds_instances,
                'lambda_functions': lambda_functions,
                'dynamodb_tables': dynamodb_tables
            }
            
            self.print_table("VPCs", vpcs)
            self.print_json_output(vpcs, "VPCs JSON")
            self.print_table("EC2 Instances", ec2_instances)
            self.print_json_output(ec2_instances, "EC2 Instances JSON")
            self.print_table("RDS Instances", rds_instances)
            self.print_json_output(rds_instances, "RDS Instances JSON")
            self.print_table("Lambda Functions", lambda_functions)
            self.print_json_output(lambda_functions, "Lambda Functions JSON")
            self.print_table("DynamoDB Tables", dynamodb_tables)
            self.print_json_output(dynamodb_tables, "DynamoDB Tables JSON")
        
        return self.inventory_data

    def save_inventory(self, inventory: Dict, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2)
        logger.info(f"Inventory saved to {filename}")
        
        # Also print the complete inventory to console
        console.print("\n[bold cyan]=== Complete Inventory JSON ===[/bold cyan]")
        self.print_json_output(inventory)

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    
    inventory = AWSResourceInventory()
    resources = inventory.generate_inventory()
    
    # Save both JSON and detailed report
    inventory.save_inventory(resources, 'aws_inventory.json')
    
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
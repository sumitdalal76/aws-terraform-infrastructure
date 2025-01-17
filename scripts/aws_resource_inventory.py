#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import json
from typing import Dict, List
import logging
from rich.console import Console
from rich.table import Table
from datetime import datetime
import botocore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = self._get_regions()
        self.inventory_data = {}
        self.services = self._discover_services()

    def _get_regions(self) -> List[str]:
        """Get list of all AWS regions."""
        ec2 = self.session.client('ec2')
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions

    def _discover_services(self) -> Dict:
        """Automatically discover AWS services and their list methods"""
        services = {}
        
        # Get all available AWS services
        available_services = boto3.Session().get_available_services()
        
        for service_name in available_services:
            try:
                # Create a client for the service
                client = self.session.client(service_name)
                
                # Get all available operations for the service
                operations = client.meta.service_model.operation_names
                
                # Look for list/describe operations
                list_operations = [
                    op for op in operations 
                    if op.startswith(('list_', 'describe_')) 
                    and not op.endswith(('_tags', '_tag_keys', '_tag_values'))
                ]
                
                if list_operations:
                    services[service_name] = {
                        'client': service_name,
                        'list_methods': list_operations
                    }
                    
            except (ClientError, botocore.exceptions.UnknownServiceError) as e:
                logger.debug(f"Skipping service {service_name}: {str(e)}")
                continue
                
        logger.info(f"Discovered {len(services)} AWS services")
        return services

    def get_resources(self, service_name: str, region: str = None) -> Dict[str, List]:
        """Get only active/used resources for a service"""
        resources = {}
        
        try:
            client = self.session.client(service_name, region_name=region)
            
            for method_name in self.services[service_name]['list_methods']:
                try:
                    method = getattr(client, method_name)
                    response = method()
                    
                    # Remove response metadata
                    if 'ResponseMetadata' in response:
                        del response['ResponseMetadata']
                    
                    # Filter and process the response
                    filtered_response = self._filter_active_resources(
                        service_name, 
                        method_name, 
                        response
                    )
                    
                    if filtered_response:
                        resources[method_name] = filtered_response
                        
                except (ClientError, botocore.exceptions.ParamValidationError) as e:
                    logger.debug(f"Error calling {method_name} for {service_name}: {str(e)}")
                    continue
                    
        except ClientError as e:
            logger.error(f"Error accessing {service_name} in {region}: {str(e)}")
            
        return resources

    def _filter_active_resources(self, service_name: str, method_name: str, response: Dict) -> Dict:
        """Filter only active/used resources"""
        if not response:
            return None

        # Handle specific service responses
        if service_name == 'ec2':
            if method_name == 'describe_instances':
                active_instances = []
                for reservation in response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        # Only include running or stopped instances
                        if instance['State']['Name'] not in ['terminated', 'shutting-down']:
                            active_instances.append(instance)
                if active_instances:
                    return {'Reservations': [{'Instances': active_instances}]}
            
            elif method_name == 'describe_vpcs':
                # Filter out default VPCs
                active_vpcs = [
                    vpc for vpc in response.get('Vpcs', [])
                    if not vpc.get('IsDefault', False)
                ]
                if active_vpcs:
                    return {'Vpcs': active_vpcs}

        elif service_name == 'rds':
            if method_name == 'describe_db_instances':
                # Only include active DB instances
                active_dbs = [
                    db for db in response.get('DBInstances', [])
                    if db['DBInstanceStatus'] not in ['deleted', 'deleting']
                ]
                if active_dbs:
                    return {'DBInstances': active_dbs}

        elif service_name == 's3':
            if method_name == 'list_buckets':
                # Only include non-empty buckets
                active_buckets = []
                for bucket in response.get('Buckets', []):
                    try:
                        s3_client = self.session.client('s3')
                        objects = s3_client.list_objects_v2(
                            Bucket=bucket['Name'],
                            MaxKeys=1
                        )
                        if objects.get('Contents'):
                            active_buckets.append(bucket)
                    except ClientError:
                        continue
                if active_buckets:
                    return {'Buckets': active_buckets}

        elif service_name == 'lambda':
            if method_name == 'list_functions':
                # Only include active functions
                active_functions = [
                    func for func in response.get('Functions', [])
                    if func.get('State') != 'Inactive'
                ]
                if active_functions:
                    return {'Functions': active_functions}

        # For other services, check if there's any data
        for key, value in response.items():
            if isinstance(value, list) and value:
                return response
            elif isinstance(value, dict) and value:
                return response

        return None

    def print_resources(self, resources: Dict, service_name: str):
        """Print only non-empty resource tables"""
        if not resources:
            return

        for method_name, resource_data in resources.items():
            if not resource_data:
                continue

            console.print(f"\n[bold blue]{service_name.upper()} - {method_name}[/bold blue]")
            
            # Convert resource data to table format
            table = Table(show_header=True)
            
            # Extract meaningful data from the response
            if isinstance(resource_data, dict):
                # Find the first list in the response
                for key, value in resource_data.items():
                    if isinstance(value, list) and value:
                        resource_data = value
                        break
            
            if isinstance(resource_data, list) and resource_data:
                # Create columns based on the first item
                if isinstance(resource_data[0], dict):
                    columns = list(resource_data[0].keys())
                    for column in columns:
                        table.add_column(column)
                    
                    # Add rows
                    for item in resource_data:
                        row = [str(item.get(col, 'N/A')) for col in columns]
                        table.add_row(*row)
                    
                    console.print(table)
            elif resource_data:
                # If we can't format as a table but have data, print the raw data
                console.print(json.dumps(resource_data, indent=2))

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources"""
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            'global_services': {}
        }
        
        console.print("\n[bold cyan]=== AWS Resource Inventory ===[/bold cyan]\n")
        
        # Handle global services
        global_services = ['s3', 'iam', 'route53', 'cloudfront']
        for service in self.services:
            if service in global_services:
                resources = self.get_resources(service)
                if resources:
                    self.inventory_data['global_services'][service] = resources
                    console.print(f"\n[bold green]Global {service.upper()} Resources[/bold green]")
                    self.print_resources(resources, service)
        
        # Handle regional services
        for region in self.regions:
            console.print(f"\n[bold green]Scanning region: {region}[/bold green]")
            self.inventory_data['regions'][region] = {}
            
            for service_name in self.services:
                if service_name not in global_services:
                    resources = self.get_resources(service_name, region)
                    if resources:
                        self.inventory_data['regions'][region][service_name] = resources
                        self.print_resources(resources, service_name)
        
        return self.inventory_data

    def save_inventory(self, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.inventory_data, f, indent=2)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    inventory = AWSResourceInventory()
    resources = inventory.generate_inventory()
    inventory.save_inventory()
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
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

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AWSResourceInventory:
    def __init__(self):
        self.session = self._get_session()
        self.regions = self._get_regions()
        self.inventory_data = {}
        self.services = self._discover_services()

    def _get_session(self):
        """Create boto3 session with explicit credential check"""
        session = boto3.Session()
        try:
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"Using IAM Role/User: {identity['Arn']}")
            logger.info(f"Account ID: {identity['Account']}")
            
            # Test EC2 permissions explicitly
            ec2 = session.client('ec2', region_name='ca-central-1')
            vpcs = ec2.describe_vpcs()
            logger.info(f"Found {len(vpcs['Vpcs'])} VPCs in ca-central-1")
            
            return session
        except Exception as e:
            logger.error(f"Error with AWS credentials: {str(e)}")
            raise

    def _get_regions(self) -> List[str]:
        """Get list of all AWS regions."""
        ec2 = self.session.client('ec2')
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions

    def _discover_services(self) -> Dict:
        """Discover AWS services with explicit error handling"""
        services = {}
        core_services = ['ec2', 'elasticloadbalancingv2', 'route53', 'acm']
        
        for service_name in core_services:
            try:
                client = self.session.client(service_name)
                logger.info(f"Testing {service_name} access...")
                
                # Test specific service access
                if service_name == 'ec2':
                    vpcs = client.describe_vpcs()
                    logger.info(f"EC2 access successful - Found {len(vpcs['Vpcs'])} VPCs")
                elif service_name == 'elasticloadbalancingv2':
                    lbs = client.describe_load_balancers()
                    logger.info(f"ELB access successful - Found {len(lbs['LoadBalancers'])} Load Balancers")
                
                operations = client.meta.service_model.operation_names
                list_operations = [
                    op for op in operations 
                    if op.startswith(('list_', 'describe_'))
                ]
                
                if list_operations:
                    services[service_name] = {
                        'client': service_name,
                        'list_methods': list_operations
                    }
                    logger.info(f"Added {service_name} with {len(list_operations)} methods")
                    
            except ClientError as e:
                logger.error(f"Error accessing {service_name}: {e.response['Error']['Message']}")
            except Exception as e:
                logger.error(f"Unexpected error with {service_name}: {str(e)}")
        
        return services

    def get_resources(self, service_name: str, region: str = None) -> Dict[str, List]:
        """Get resources with detailed error handling"""
        resources = {}
        try:
            client = self.session.client(service_name, region_name=region)
            logger.info(f"Checking {service_name} in {region or 'global'}")
            
            if service_name == 'ec2':
                # Explicitly check EC2 resources
                vpcs = client.describe_vpcs()
                instances = client.describe_instances()
                logger.info(f"Found {len(vpcs['Vpcs'])} VPCs and {len(instances['Reservations'])} EC2 reservations")
                if vpcs['Vpcs']:
                    resources['describe_vpcs'] = vpcs
                if instances['Reservations']:
                    resources['describe_instances'] = instances
                    
            elif service_name == 'elasticloadbalancingv2':
                # Explicitly check ELB resources
                lbs = client.describe_load_balancers()
                if lbs['LoadBalancers']:
                    resources['describe_load_balancers'] = lbs
                    
        except ClientError as e:
            logger.error(f"Error getting {service_name} resources in {region}: {e.response['Error']['Message']}")
        except Exception as e:
            logger.error(f"Unexpected error with {service_name} in {region}: {str(e)}")
            
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
                    # Select specific columns based on resource type
                    if method_name == 'describe_instances':
                        columns = ['InstanceId', 'InstanceType', 'State', 'PrivateIpAddress', 'PublicIpAddress']
                    elif method_name == 'describe_vpcs':
                        columns = ['VpcId', 'CidrBlock', 'IsDefault', 'State']
                    else:
                        columns = list(resource_data[0].keys())
                    
                    for column in columns:
                        table.add_column(column)
                    
                    # Add rows
                    for item in resource_data:
                        row = [str(item.get(col, 'N/A')) for col in columns]
                        table.add_row(*row)
                    
                    console.print(table)

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
            json.dump(self.inventory_data, f, indent=2, cls=DateTimeEncoder)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    try:
        inventory = AWSResourceInventory()
        
        # Test specific region first
        ca_central = inventory.get_resources('ec2', 'ca-central-1')
        if ca_central:
            console.print("[green]Successfully found resources in ca-central-1[/green]")
            # Use the custom encoder when dumping to JSON
            console.print(json.dumps(ca_central, indent=2, cls=DateTimeEncoder))
        
        resources = inventory.generate_inventory()
        inventory.save_inventory()
        console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        logger.error(f"Error running inventory: {str(e)}")
        raise

if __name__ == "__main__":
    main()
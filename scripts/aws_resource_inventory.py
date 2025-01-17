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
        """Automatically discover all AWS services"""
        services = {}
        
        # Get all available AWS services
        available_services = boto3.Session().get_available_services()
        
        # Common AWS services we're interested in
        common_services = [
            'ec2', 'elbv2', 'route53', 'acm', 'rds', 's3', 
            'lambda', 'cloudfront', 'dynamodb', 'iam'
        ]
        
        # First check common services, then others
        for service_name in sorted(available_services):
            try:
                client = self.session.client(service_name)
                logger.info(f"Testing {service_name} access...")
                
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
                    logger.info(f"Added {service_name} with {len(list_operations)} methods")
                    
            except (ClientError, botocore.exceptions.UnknownServiceError) as e:
                logger.debug(f"Skipping {service_name}: {str(e)}")
                continue
                
        return services

    def get_resources(self, service_name: str, region: str = None) -> Dict[str, List]:
        """Get resources for a service"""
        resources = {}
        
        try:
            client = self.session.client(service_name, region_name=region)
            logger.info(f"Checking {service_name} in {region or 'global'}")
            
            for method_name in self.services[service_name]['list_methods']:
                try:
                    method = getattr(client, method_name)
                    response = method()
                    
                    # Remove response metadata
                    if isinstance(response, dict):
                        response.pop('ResponseMetadata', None)
                    
                    if response and any(response.values()):
                        resources[method_name] = response
                        
                except (ClientError, botocore.exceptions.ParamValidationError) as e:
                    logger.debug(f"Skipping {method_name} for {service_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error accessing {service_name} in {region}: {str(e)}")
            
        return resources

    def print_resources(self, resources: Dict, service_name: str):
        """Print resources in a clean table format"""
        if not resources:
            return

        console.print(f"\n[bold blue]=== {service_name.upper()} Resources ===[/bold blue]")
        
        for method_name, resource_data in resources.items():
            if not resource_data:
                continue
            
            # Create table title from method name
            title = method_name.replace('describe_', '').replace('list_', '').replace('_', ' ').upper()
            table = Table(title=title)
            
            # Extract the actual resource list
            items = []
            if isinstance(resource_data, dict):
                for key, value in resource_data.items():
                    if isinstance(value, list):
                        items = value
                        break
            elif isinstance(resource_data, list):
                items = resource_data
                
            if not items:
                continue
                
            # Get common attributes for the resource type
            if isinstance(items[0], dict):
                # Define important columns for each resource type
                columns = self._get_important_columns(service_name, method_name, items[0])
                
                # Add columns to table
                for col in columns:
                    table.add_column(col.replace('_', ' ').title())
                
                # Add rows
                for item in items:
                    row = []
                    for col in columns:
                        value = item.get(col, 'N/A')
                        if isinstance(value, dict) and 'Name' in value:
                            value = value['Name']
                        elif isinstance(value, list):
                            value = ', '.join([str(v) for v in value])
                        row.append(str(value))
                    table.add_row(*row)
                    
                console.print(table)
                console.print("")

    def _get_important_columns(self, service_name: str, method_name: str, sample_item: Dict) -> List[str]:
        """Get important columns based on resource type"""
        common_columns = ['Id', 'Name', 'Arn', 'State', 'Type']
        specific_columns = {
            'ec2': {
                'describe_instances': ['InstanceId', 'InstanceType', 'State', 'PrivateIpAddress', 'PublicIpAddress'],
                'describe_vpcs': ['VpcId', 'CidrBlock', 'State', 'IsDefault'],
                'describe_subnets': ['SubnetId', 'VpcId', 'CidrBlock', 'AvailabilityZone', 'State'],
                'describe_security_groups': ['GroupId', 'GroupName', 'VpcId', 'Description']
            },
            'elbv2': {
                'describe_load_balancers': ['LoadBalancerArn', 'DNSName', 'State', 'Type', 'Scheme']
            },
            'route53': {
                'list_hosted_zones': ['Id', 'Name', 'Config']
            },
            'acm': {
                'list_certificates': ['CertificateArn', 'DomainName', 'Status']
            }
        }
        
        # Get specific columns if defined
        if service_name in specific_columns and method_name in specific_columns[service_name]:
            return specific_columns[service_name][method_name]
        
        # Otherwise, use available columns that match common patterns
        available_columns = list(sample_item.keys())
        selected_columns = []
        
        # First add common columns if they exist
        for col in common_columns:
            matching_cols = [c for c in available_columns if col.lower() in c.lower()]
            if matching_cols:
                selected_columns.extend(matching_cols)
        
        # Then add any remaining important-looking columns
        for col in available_columns:
            if any(term in col.lower() for term in ['name', 'id', 'arn', 'state', 'type']):
                if col not in selected_columns:
                    selected_columns.append(col)
        
        return selected_columns[:6]  # Limit to 6 columns for readability

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources"""
        console.print("\n[bold cyan]=== AWS Resource Inventory ===[/bold cyan]\n")
        
        timestamp = datetime.now().isoformat()
        self.inventory_data = {
            'timestamp': timestamp,
            'global_services': {},
            'regions': {}
        }
        
        # Handle global services first
        global_services = ['iam', 'route53', 's3', 'cloudfront']
        for service in self.services:
            if service in global_services:
                resources = self.get_resources(service)
                if resources:
                    self.inventory_data['global_services'][service] = resources
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
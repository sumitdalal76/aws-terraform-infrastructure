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
        """Automatically discover AWS services"""
        services = {}
        
        # Core AWS services we're interested in
        core_services = [
            'ec2', 'elbv2', 'route53', 'acm', 'rds', 's3', 
            'lambda', 'cloudfront', 'dynamodb', 'iam'
        ]
        
        for service_name in core_services:
            try:
                client = self.session.client(service_name)
                logger.info(f"Scanning {service_name} service...")
                
                operations = client.meta.service_model.operation_names
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
                    logger.info(f"Found {len(list_operations)} operations for {service_name}")
                    
            except (ClientError, botocore.exceptions.UnknownServiceError) as e:
                logger.error(f"Error scanning {service_name}: {str(e)}")
                continue
                
        return services

    def get_resources(self, service_name: str, region: str = None) -> Dict[str, List]:
        """Get resources for a service"""
        resources = {}
        
        try:
            client = self.session.client(service_name, region_name=region)
            logger.info(f"Scanning {service_name} resources in {region or 'global'}")
            
            if service_name == 'ec2':
                # Explicitly handle EC2 resources
                try:
                    vpcs = client.describe_vpcs()
                    if vpcs.get('Vpcs'):
                        resources['describe_vpcs'] = vpcs
                        logger.info(f"Found {len(vpcs['Vpcs'])} VPCs")

                    instances = client.describe_instances()
                    if instances.get('Reservations'):
                        resources['describe_instances'] = instances
                        logger.info(f"Found {len(instances['Reservations'])} EC2 reservations")

                    subnets = client.describe_subnets()
                    if subnets.get('Subnets'):
                        resources['describe_subnets'] = subnets
                        logger.info(f"Found {len(subnets['Subnets'])} Subnets")

                    security_groups = client.describe_security_groups()
                    if security_groups.get('SecurityGroups'):
                        resources['describe_security_groups'] = security_groups
                        logger.info(f"Found {len(security_groups['SecurityGroups'])} Security Groups")

                except ClientError as e:
                    logger.error(f"Error getting EC2 resources: {str(e)}")

            elif service_name == 'elbv2':
                try:
                    lbs = client.describe_load_balancers()
                    if lbs.get('LoadBalancers'):
                        resources['describe_load_balancers'] = lbs
                        logger.info(f"Found {len(lbs['LoadBalancers'])} Load Balancers")
                except ClientError as e:
                    logger.error(f"Error getting ELB resources: {str(e)}")

            elif service_name == 'route53':
                try:
                    zones = client.list_hosted_zones()
                    if zones.get('HostedZones'):
                        resources['list_hosted_zones'] = zones
                        logger.info(f"Found {len(zones['HostedZones'])} Hosted Zones")
                except ClientError as e:
                    logger.error(f"Error getting Route53 resources: {str(e)}")

            elif service_name == 'acm':
                try:
                    certs = client.list_certificates()
                    if certs.get('CertificateSummaryList'):
                        resources['list_certificates'] = certs
                        logger.info(f"Found {len(certs['CertificateSummaryList'])} Certificates")
                except ClientError as e:
                    logger.error(f"Error getting ACM resources: {str(e)}")

        except Exception as e:
            logger.error(f"Error accessing {service_name} in {region}: {str(e)}")
            
        return resources

    def print_resources(self, resources: Dict, service_name: str):
        """Print resources in a clean table format"""
        if not resources:
            return

        console.print(f"\n[bold yellow]{service_name.upper()} Resources[/bold yellow]")
        
        for method_name, resource_data in resources.items():
            # Handle EC2 instances
            if method_name == 'describe_instances' and 'Reservations' in resource_data:
                table = Table(title="EC2 INSTANCES")
                table.add_column("Instance ID")
                table.add_column("Name")
                table.add_column("Type")
                table.add_column("State")
                table.add_column("Private IP")
                table.add_column("Public IP")

                for reservation in resource_data['Reservations']:
                    for instance in reservation['Instances']:
                        if instance['State']['Name'] != 'terminated':
                            name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                            table.add_row(
                                instance['InstanceId'],
                                name,
                                instance['InstanceType'],
                                instance['State']['Name'],
                                instance.get('PrivateIpAddress', 'N/A'),
                                instance.get('PublicIpAddress', 'N/A')
                            )
                console.print(table)

            # Handle VPCs
            elif method_name == 'describe_vpcs' and 'Vpcs' in resource_data:
                table = Table(title="VPCs")
                table.add_column("VPC ID")
                table.add_column("CIDR Block")
                table.add_column("Name")
                table.add_column("State")

                for vpc in resource_data['Vpcs']:
                    name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                    table.add_row(
                        vpc['VpcId'],
                        vpc['CidrBlock'],
                        name,
                        vpc['State']
                    )
                console.print(table)

            # Handle Subnets
            elif method_name == 'describe_subnets' and 'Subnets' in resource_data:
                table = Table(title="SUBNETS")
                table.add_column("Subnet ID")
                table.add_column("VPC ID")
                table.add_column("CIDR Block")
                table.add_column("AZ")
                table.add_column("Name")

                for subnet in resource_data['Subnets']:
                    name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                    table.add_row(
                        subnet['SubnetId'],
                        subnet['VpcId'],
                        subnet['CidrBlock'],
                        subnet['AvailabilityZone'],
                        name
                    )
                console.print(table)

            # Handle Load Balancers
            elif method_name == 'describe_load_balancers' and 'LoadBalancers' in resource_data:
                table = Table(title="LOAD BALANCERS")
                table.add_column("Name")
                table.add_column("DNS Name")
                table.add_column("Type")
                table.add_column("Scheme")
                table.add_column("State")

                for lb in resource_data['LoadBalancers']:
                    table.add_row(
                        lb['LoadBalancerName'],
                        lb['DNSName'],
                        lb['Type'],
                        lb['Scheme'],
                        lb['State']['Code']
                    )
                console.print(table)

            # Handle Security Groups
            elif method_name == 'describe_security_groups' and 'SecurityGroups' in resource_data:
                table = Table(title="SECURITY GROUPS")
                table.add_column("Group ID")
                table.add_column("Name")
                table.add_column("VPC ID")
                table.add_column("Description")

                for sg in resource_data['SecurityGroups']:
                    table.add_row(
                        sg['GroupId'],
                        sg['GroupName'],
                        sg.get('VpcId', 'N/A'),
                        sg['Description']
                    )
                console.print(table)

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
        console.print("\n[bold cyan]=== AWS Resource Inventory ===[/bold cyan]")
        
        # Handle global services first
        global_services = ['iam', 'route53', 's3', 'cloudfront']
        console.print("\n[bold green]Scanning Global Services...[/bold green]")
        
        for service in global_services:
            if service in self.services:
                resources = self.get_resources(service)
                if resources:
                    console.print(f"\n[bold blue]Found {service.upper()} Resources:[/bold blue]")
                    self.print_resources(resources, service)
        
        # Handle regional services
        console.print("\n[bold green]Scanning Regional Services...[/bold green]")
        
        # Focus on ca-central-1
        region = 'ca-central-1'
        console.print(f"\n[bold blue]Region: {region}[/bold blue]")
        
        regional_services = [s for s in self.services if s not in global_services]
        for service_name in regional_services:
            resources = self.get_resources(service_name, region)
            if resources:
                console.print(f"\n[bold blue]Found {service_name.upper()} Resources:[/bold blue]")
                self.print_resources(resources, service_name)
                
                # Store in inventory data
                if region not in self.inventory_data:
                    self.inventory_data[region] = {}
                self.inventory_data[region][service_name] = resources
        
        return self.inventory_data

    def save_inventory(self, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.inventory_data, f, indent=2, cls=DateTimeEncoder)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]")
    try:
        inventory = AWSResourceInventory()
        inventory.generate_inventory()
        inventory.save_inventory()
        console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        logger.error(f"Error running inventory: {str(e)}")
        raise

if __name__ == "__main__":
    main()
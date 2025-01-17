#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from rich.console import Console
from rich.table import Table
import json
import os
from typing import Dict, List

# Initialize console for table output
console = Console()

def list_all_resources():
    session = boto3.Session()
    ec2_client = session.client("ec2")
    
    try:
        # Verify IAM credentials
        sts = session.client('sts')
        caller_identity = sts.get_caller_identity()
        console.print(f"[bold green]Using IAM Role/User: {caller_identity['Arn']}[/bold green]")
        console.print(f"[bold green]Account ID: {caller_identity['Account']}[/bold green]")
    except ClientError as e:
        console.print(f"[bold red]Error verifying credentials: {str(e)}[/bold red]")
        return

    try:
        # Get all AWS regions
        regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
        console.print(f"[bold cyan]\nRegions to be scanned:[/bold cyan]")
        console.print(f"[cyan]{', '.join(sorted(regions))}[/cyan]")
    except ClientError as e:
        console.print(f"[bold red]Error fetching regions: {str(e)}[/bold red]")
        return

    try:
        # Get all available AWS services dynamically
        available_services = session.get_available_services()
        console.print(f"[bold cyan]\nServices to be scanned:[/bold cyan]")
        console.print(f"[cyan]{', '.join(sorted(available_services))}[/cyan]")
        console.print(f"\n[bold cyan]Starting AWS Resource Inventory...[/bold cyan]")
    except ClientError as e:
        console.print(f"[bold red]Error fetching available services: {str(e)}[/bold red]")
        return

    all_resources = {}
    
    for region in regions:
        for service in available_services:
            try:
                client = session.client(service, region_name=region)
                operations = client.meta.service_model.operation_names
                list_operations = [op for op in operations if op.startswith("list_") or op.startswith("describe_")]

                for operation in list_operations:
                    try:
                        response = getattr(client, operation)()
                        resources = next(
                            (value for key, value in response.items() if isinstance(value, list) and value), []
                        )

                        if resources:
                            console.print(f"[bold green]Found {len(resources)} resources in {service}:{operation} ({region})[/bold green]")
                            formatted_resources = [
                                {"Region": region, "Service": service, **flatten_dict(resource)}
                                for resource in resources
                            ]
                            all_resources.setdefault(service, []).extend(formatted_resources)

                    except ClientError as e:
                        error_code = e.response['Error']['Code']
                        if error_code in ['AccessDeniedException', 'UnauthorizedOperation']:
                            console.print(f"[bold yellow]Access denied for {service}:{operation} in {region}[/bold yellow]")
                        elif error_code == 'OptInRequired':
                            console.print(f"[bold yellow]Region {region} requires opt-in for {service}[/bold yellow]")
                        else:
                            console.print(f"[bold red]Error in {service}:{operation} - {error_code}: {e.response['Error']['Message']}[/bold red]")
                        continue
                    except Exception as e:
                        console.print(f"[bold red]Error during {service}:{operation} in {region}: {str(e)}[/bold red]")
                        continue

            except (ClientError, EndpointConnectionError) as e:
                if hasattr(e, 'response'):
                    error_code = e.response['Error']['Code']
                    error_message = e.response['Error']['Message']
                    console.print(f"[bold red]Error accessing {service} in {region}: {error_code} - {error_message}[/bold red]")
                else:
                    console.print(f"[bold red]Error accessing {service} in {region}: {str(e)}[/bold red]")
                continue

    # Print consolidated tables
    if all_resources:
        for service, items in all_resources.items():
            print_table(service.title(), items)
        
        # Save inventory to JSON
        output_file = "aws_all_resources.json"
        with open(output_file, "w") as f:
            json.dump(all_resources, f, indent=4)
        console.print(f"[bold green]Inventory saved to {output_file}[/bold green]")
    else:
        console.print("[bold yellow]No resources found. This might be due to insufficient permissions.[/bold yellow]")

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flattens nested dictionaries to handle complex AWS resource structures.
    For example, {"a": {"b": 1}} becomes {"a_b": 1}.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def print_table(title, items):
    """Prints a table with a dynamic column structure."""
    if not items:
        console.print(f"[bold yellow]{title}: No resources found.[/bold yellow]")
        return

    table = Table(title=title)
    keys = items[0].keys()  # Extract keys from the first item
    for key in keys:
        table.add_column(key)

    for item in items:
        table.add_row(*[str(item.get(key, "N/A")) for key in keys])

    console.print(table)

def get_resources(self, service_name: str, region: str = None) -> Dict[str, List]:
    """Get resources for a service"""
    resources = {}
    
    try:
        client = self.session.client(service_name, region_name=region)
        logger.info(f"\nScanning {service_name} resources in {region or 'global'}")
        
        for method_name in self.services[service_name]['list_methods']:
            try:
                method = getattr(client, method_name)
                response = method()
                
                # Remove response metadata
                if isinstance(response, dict):
                    response.pop('ResponseMetadata', None)
                
                if response and any(response.values()):
                    resources[method_name] = response
                    logger.info(f"✓ Found resources using {method_name}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                if error_code == 'AccessDeniedException' or error_code == 'UnauthorizedOperation':
                    logger.error(f"❌ Permission denied for {service_name}:{method_name} - {error_message}")
                elif error_code == 'OptInRequired':
                    logger.warning(f"⚠️  Region {region} requires opt-in for {service_name}")
                else:
                    logger.error(f"❌ Error in {service_name}:{method_name} - {error_code}: {error_message}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error in {service_name}:{method_name} - {str(e)}")
                continue
                
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ Failed to access {service_name} in {region}: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"❌ Unexpected error accessing {service_name} in {region}: {str(e)}")
        
    return resources

def print_resources(self, resources: Dict, service_name: str):
    """Print resources in a clean table format"""
    if not resources:
        return

    try:
        console.print(f"\n[bold yellow]{service_name.upper()} Resources[/bold yellow]")
        
        for method_name, resource_data in resources.items():
            if not resource_data:
                continue
                
            # Get the main list of resources
            items = []
            if isinstance(resource_data, dict):
                for key, value in resource_data.items():
                    if isinstance(value, list) and value:
                        items = value
                        break
            elif isinstance(resource_data, list):
                items = resource_data
                
            if not items:
                continue
                
            # Create table
            title = method_name.replace('describe_', '').replace('list_', '').replace('_', ' ').upper()
            table = Table(title=title, show_header=True)
            
            try:
                # Add columns based on resource type
                if isinstance(items[0], dict):
                    columns = self._get_important_columns(items[0])
                    for col in columns:
                        table.add_column(col.replace('_', ' ').title())
                    
                    # Add rows
                    for item in items:
                        row = []
                        for col in columns:
                            value = item.get(col, 'N/A')
                            if isinstance(value, (dict, list)):
                                value = str(value)
                            row.append(str(value))
                        table.add_row(*row)
                    
                    console.print(table)
                    console.print("")
            except Exception as e:
                logger.error(f"❌ Error formatting table for {service_name}:{method_name} - {str(e)}")
                
    except Exception as e:
        logger.error(f"❌ Error printing resources for {service_name} - {str(e)}")

def _get_important_columns(self, item: Dict) -> List[str]:
    """Get the most important columns for a resource"""
    # Common important fields
    important_fields = [
        'id', 'name', 'arn', 'type', 'state', 'status',
        'vpc_id', 'subnet_id', 'instance_id', 'description'
    ]
    
    columns = []
    available_columns = list(item.keys())
    
    # First add common important fields if they exist
    for field in important_fields:
        matching_cols = [col for col in available_columns if field.lower() in col.lower()]
        if matching_cols:
            columns.extend(matching_cols)
    
    # Then add any remaining fields up to a reasonable limit
    remaining_cols = [col for col in available_columns if col not in columns]
    columns.extend(remaining_cols[:4])  # Limit to 4 additional columns
    
    return columns[:6]  # Limit to 6 total columns for readability

def generate_inventory(self) -> Dict:
    """Generate complete inventory of AWS resources"""
    console.print("\n[bold cyan]=== AWS Resource Inventory ===[/bold cyan]\n")
    
    # Handle global services first
    global_services = ['iam', 'route53', 's3', 'cloudfront']
    console.print("[bold green]Scanning Global Services...[/bold green]")
    
    for service in global_services:
        if service in self.services:
            resources = self.get_resources(service)
            if resources:
                self.print_resources(resources, service)
    
    # Handle regional services
    console.print("\n[bold green]Scanning Regional Services...[/bold green]")
    
    for region in self.regions:
        console.print(f"\n[bold blue]Region: {region}[/bold blue]")
        
        for service_name in self.services:
            if service_name not in global_services:
                resources = self.get_resources(service_name, region)
                if resources:
                    self.print_resources(resources, service_name)
    
    if not self.inventory_data:
        console.print("[bold yellow]No resources found. This might be due to permissions or empty regions.[/bold yellow]")
    
    return self.inventory_data

if __name__ == "__main__":
    list_all_resources()

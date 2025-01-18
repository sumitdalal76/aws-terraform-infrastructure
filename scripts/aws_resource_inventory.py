#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from rich.console import Console
from rich.table import Table
import json
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set
import logging
import resource
import argparse
from pathlib import Path

# Increase maximum number of open files
resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))

# Initialize console and logger
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSResourceLister:
    def __init__(self, directory="./data", parallel=10, verbose=False):
        self.session = boto3.Session()
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.parallel = parallel
        self.verbose = verbose
        
    def list_resources(self, region=None, service=None, operation=None):
        """Main method to list AWS resources"""
        try:
            # Verify credentials
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            console.print(f"[bold green]Using IAM Role/User: {identity['Arn']}[/bold green]")
            console.print(f"[bold green]Account ID: {identity['Account']}[/bold green]\n")
            
            # Get regions if not specified
            regions = [region] if region else self._get_regions()
            
            # Get services if not specified
            services = [service] if service else self._get_available_services()
            
            console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
            
            # Create work items
            work_items = []
            for svc in services:
                if operation:
                    operations = [operation]
                else:
                    operations = self._get_service_operations(svc)
                
                for op in operations:
                    for reg in regions:
                        if self._is_regional_service(svc):
                            work_items.append((svc, reg, op))
                        elif reg == regions[0]:  # Global services only need to be queried once
                            work_items.append((svc, None, op))
            
            # Randomize work items to avoid API throttling
            random.shuffle(work_items)
            
            # Execute work items
            with ThreadPoolExecutor(max_workers=self.parallel) as executor:
                futures = [executor.submit(self._query_resource, svc, reg, op) 
                          for svc, reg, op in work_items]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error in worker thread: {str(e)}")
            
        except Exception as e:
            console.print(f"[bold red]Error in main execution: {str(e)}[/bold red]")

    def _query_resource(self, service: str, region: str, operation: str):
        """Query a specific AWS resource"""
        try:
            client = self.session.client(service, region_name=region)
            method = getattr(client, operation, None)
            
            if not method:
                if self.verbose:
                    logger.warning(f"Operation {operation} not found for {service}")
                return
            
            try:
                response = method()
                # Find the list of resources in the response
                resources = self._find_resource_list(response)
                
                if resources:
                    status = "+++"
                    self._save_to_file(service, region, operation, response)
                    if self.verbose:
                        console.print(f"[green]{status} {service} {region or 'global'} {operation} - Found {len(resources)} resources[/green]")
                else:
                    status = "---"
                    if self.verbose:
                        console.print(f"[yellow]{status} {service} {region or 'global'} {operation} - No resources found[/yellow]")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDeniedException':
                    if self.verbose:
                        console.print(f"[yellow]>:| {service} {region or 'global'} {operation} - Access Denied[/yellow]")
                elif error_code != 'InvalidAction':  # Skip reporting invalid actions
                    console.print(f"[red]!!! {service} {region or 'global'} {operation} - {error_code}[/red]")
            
        except Exception as e:
            if not str(e).endswith('has no attribute'):  # Skip attribute errors
                console.print(f"[red]!!! {service} {region or 'global'} {operation} - {str(e)}[/red]")

    def _find_resource_list(self, response: Dict) -> List:
        """Find the list of resources in an AWS API response"""
        if not isinstance(response, dict):
            return []
            
        # Look for list values that aren't empty
        for value in response.values():
            if isinstance(value, list) and value:
                return value
                
        return []

    def _save_to_file(self, service: str, region: str, operation: str, data: Dict):
        """Save response data to JSON file"""
        filename = f"{service}_{operation}_{region or 'global'}.json"
        filepath = self.directory / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _get_regions(self) -> List[str]:
        """Get list of AWS regions"""
        ec2 = self.session.client('ec2')
        try:
            return [r['RegionName'] for r in ec2.describe_regions()['Regions']]
        except ClientError as e:
            console.print(f"[bold red]Error fetching regions: {str(e)}[/bold red]")
            return ['us-east-1']

    def _get_available_services(self) -> List[str]:
        """Get list of available AWS services"""
        return self.session.get_available_services()

    def _get_service_operations(self, service: str) -> List[str]:
        """Get list of available operations for a service"""
        try:
            client = self.session.client(service)
            operations = []
            
            # Common operation prefixes that typically return resources
            prefixes = ('Describe', 'List', 'Get')
            
            # Skip known problematic operations
            skip_operations = {
                'ListTagsForResource',  # Common operation that often fails
                'GetResourcePolicy',    # Common operation that often fails
                'DescribeEngineDefaultParameters',
                'DescribeVpcEndpointConnections',
                'ListUniqueProblems',
                'GetDeviceProfile',
                'ListCasesForContact',
                'GetServiceSyncBlockerSummary',
                'GetRecommendationReportDetails'
            }
            
            # Service-specific operation mapping
            service_operations = {
                'ec2': [
                    'DescribeInstances',
                    'DescribeVolumes',
                    'DescribeSecurityGroups',
                    'DescribeVpcs',
                    'DescribeSubnets',
                    'DescribeNetworkInterfaces'
                ],
                's3': [
                    'ListBuckets'
                ],
                'rds': [
                    'DescribeDBInstances',
                    'DescribeDBClusters'
                ],
                'lambda': [
                    'ListFunctions'
                ],
                'iam': [
                    'ListUsers',
                    'ListRoles',
                    'ListGroups'
                ]
                # Add more service-specific operations as needed
            }
            
            # Use service-specific operations if available
            if service in service_operations:
                return service_operations[service]
            
            # Otherwise, discover operations dynamically
            for op in client.meta.service_model.operation_names:
                if (op.startswith(prefixes) and 
                    not op.endswith('List') and  # Skip operations that return lists of other operations
                    op not in skip_operations):
                    operations.append(op)
            
            return operations
            
        except Exception as e:
            logger.warning(f"Error getting operations for {service}: {str(e)}")
            return []

    def _is_regional_service(self, service: str) -> bool:
        """Check if a service is regional or global"""
        global_services = {'iam', 's3', 'cloudfront', 'route53', 'organizations'}
        return service not in global_services

def show_resources(files, verbose=False):
    """Show resources from saved JSON files"""
    for file in files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                
            if verbose:
                console.print(f"\n[bold cyan]Contents of {file}:[/bold cyan]")
                console.print(json.dumps(data, indent=2))
            else:
                console.print(f"\n[bold cyan]Resources in {file}:[/bold cyan]")
                resource_count = sum(len(v) for v in data.values() if isinstance(v, list))
                console.print(f"Found {resource_count} resources")
                
        except Exception as e:
            console.print(f"[bold red]Error reading {file}: {str(e)}[/bold red]")

def main():
    parser = argparse.ArgumentParser(description='List all AWS resources')
    parser.add_argument('--region', help='AWS region to query')
    parser.add_argument('--service', help='AWS service to query')
    parser.add_argument('--operation', help='Specific operation to query')
    parser.add_argument('--directory', default='./data', help='Directory to store results')
    parser.add_argument('--parallel', type=int, default=10, help='Number of parallel queries')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--show', nargs='+', help='Show contents of saved JSON files')
    
    args = parser.parse_args()
    
    if args.show:
        show_resources(args.show, args.verbose)
    else:
        lister = AWSResourceLister(args.directory, args.parallel, args.verbose)
        lister.list_resources(args.region, args.service, args.operation)

if __name__ == "__main__":
    main()

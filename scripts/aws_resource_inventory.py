import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from tabulate import tabulate
from colorama import init, Fore, Style
import json
import concurrent.futures
import re
from typing import Dict, List, Any, Set
import time
import random

init()  # Initialize colorama for cross-platform colored output

def get_all_regions() -> List[str]:
    """Get list of all AWS regions."""
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions
    except ClientError as e:
        print(f"{Fore.RED}Error fetching regions: {e}{Style.RESET_ALL}")
        return ['us-east-1']  # Fallback to default region

def get_available_services() -> List[str]:
    """Get list of all available AWS services."""
    session = boto3.Session()
    return session.get_available_services()

def get_service_operations(service: str) -> Set[str]:
    """Get list of operations for a service that might list resources."""
    try:
        client = boto3.client(service, region_name='us-east-1')
        operations = set()
        
        for operation in client.meta.service_model.operation_names:
            # Look for operations that might list resources
            if any(pattern in operation.lower() for pattern in [
                'describe', 'list', 'get', 'search'
            ]) and not any(exclude in operation.lower() for exclude in [
                'password', 'metric', 'log', 'token', 'parameter'
            ]):
                operations.add(operation)
                
        return operations
    except (ClientError, EndpointConnectionError):
        return set()

def extract_resources(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract resources from an AWS API response."""
    resources = []
    
    # Look for common patterns in response keys that might contain resources
    resource_keys = [k for k in response.keys() if any(
        pattern in k.lower() for pattern in [
            'arns', 'resources', 'ids', 'names', 'list',
            'set', 'results', 'items', 'entries'
        ]
    )]
    
    for key in resource_keys:
        if isinstance(response[key], list):
            for item in response[key]:
                if isinstance(item, dict):
                    # Try to find an identifier
                    identifier = None
                    for id_key in ['Arn', 'Id', 'Name', 'ResourceId', 'ResourceArn']:
                        if id_key in item:
                            identifier = item[id_key]
                            break
                    
                    if identifier:
                        resources.append({
                            'identifier': identifier,
                            'details': item
                        })
    
    return resources

def scan_service_region(service: str, region: str, operation: str) -> Dict[str, Any]:
    """Scan a specific service in a region using the given operation."""
    try:
        client = boto3.client(service, region_name=region)
        method = getattr(client, operation)
        
        try:
            response = method()
            if isinstance(response, dict):
                resources = extract_resources(response)
                if resources:
                    return {
                        'service': service,
                        'region': region,
                        'operation': operation,
                        'resources': resources
                    }
        except ClientError as e:
            if 'AccessDenied' in str(e):
                print(f"{Fore.YELLOW}Access Denied: {service}.{operation} in {region}{Style.RESET_ALL}")
            return None
        
    except Exception as e:
        if not isinstance(e, (ClientError, EndpointConnectionError)):
            print(f"{Fore.RED}Error scanning {service}.{operation} in {region}: {e}{Style.RESET_ALL}")
    return None

def scan_resources():
    """Scan AWS resources across all regions and services."""
    print(f"\n{Fore.BLUE}🔍 Starting AWS Resource Scanner{Style.RESET_ALL}")
    
    regions = get_all_regions()
    print(f"\n{Fore.YELLOW}📍 Scanning Regions:{Style.RESET_ALL}")
    print(', '.join(regions))
    
    services = get_available_services()
    print(f"\n{Fore.YELLOW}🔧 Available Services:{Style.RESET_ALL}")
    print(', '.join(services))
    
    all_resources = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        for service in services:
            operations = get_service_operations(service)
            
            for region in regions:
                for operation in operations:
                    # Add some randomization to avoid throttling
                    time.sleep(random.uniform(0.1, 0.3))
                    futures.append(
                        executor.submit(scan_service_region, service, region, operation)
                    )
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result and result['resources']:
                service = result['service']
                if service not in all_resources:
                    all_resources[service] = []
                all_resources[service].extend([
                    {
                        'region': result['region'],
                        'arn': resource['identifier'],
                        'tags': resource['details'].get('Tags', []),
                        'details': json.dumps(resource['details'], default=str)
                    }
                    for resource in result['resources']
                ])
    
    return all_resources

def print_table_format(resources):
    """Print resources in table format."""
    print(f"\n{Fore.GREEN}📊 Resources (Table Format):{Style.RESET_ALL}")
    
    table_data = []
    for service, resource_list in resources.items():
        for resource in resource_list:
            table_data.append([
                service,
                resource['region'],
                resource['arn'],
                json.dumps(resource.get('tags', []), default=str),
                resource.get('details', '')[:100] + '...' if len(resource.get('details', '')) > 100 else resource.get('details', '')
            ])
    
    if table_data:
        headers = ['Service', 'Region', 'Identifier', 'Tags', 'Details']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    else:
        print("No resources found")

def print_list_format(resources):
    """Print resources in list format."""
    print(f"\n{Fore.GREEN}📝 Resources (List Format):{Style.RESET_ALL}")
    
    for service, resource_list in resources.items():
        print(f"\n{Fore.YELLOW}Service: {service}{Style.RESET_ALL}")
        for resource in resource_list:
            print(f"{Fore.CYAN}  Region: {resource['region']}{Style.RESET_ALL}")
            print(f"  Identifier: {resource['arn']}")
            if resource.get('tags'):
                print(f"  Tags: {json.dumps(resource['tags'], default=str)}")
            print(f"  Details: {resource['details']}")
            print("  ---")

def main():
    try:
        resources = scan_resources()
        
        if not resources:
            print(f"\n{Fore.YELLOW}⚠️ No resources found. This could mean:{Style.RESET_ALL}")
            print("  - The account is new or empty")
            print("  - Insufficient permissions")
            print("  - Resources exist but are not tagged")
            return

        print_table_format(resources)
        print_list_format(resources)
        
    except Exception as e:
        print(f"{Fore.RED}\n❌ Fatal error: {e}{Style.RESET_ALL}")
        exit(1)

if __name__ == "__main__":
    main()
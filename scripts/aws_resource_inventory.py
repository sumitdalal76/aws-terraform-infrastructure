import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate
from colorama import init, Fore, Style
import json

init()  # Initialize colorama for cross-platform colored output

def get_all_regions():
    """Get list of all AWS regions."""
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions
    except ClientError as e:
        print(f"{Fore.RED}Error fetching regions: {e}{Style.RESET_ALL}")
        return ['us-east-1']  # Fallback to default region

def get_all_services(region):
    """Get list of all AWS services in a region."""
    try:
        quotas = boto3.client('service-quotas', region_name=region)
        services = [service['ServiceCode'] for service in quotas.list_services()['Services']]
        return services
    except ClientError as e:
        print(f"{Fore.RED}Error fetching services in {region}: {e}{Style.RESET_ALL}")
        return []

def scan_resources():
    """Scan AWS resources across all regions."""
    print(f"\n{Fore.BLUE}🔍 Starting AWS Resource Scanner{Style.RESET_ALL}")
    
    # Get all regions
    regions = get_all_regions()
    print(f"\n{Fore.YELLOW}📍 Scanning Regions:{Style.RESET_ALL}")
    print(', '.join(regions))

    # Get services from us-east-1 as reference
    services = get_all_services('us-east-1')
    print(f"\n{Fore.YELLOW}🔧 Scanning Services:{Style.RESET_ALL}")
    print(', '.join(services))

    resources = {}

    for region in regions:
        try:
            print(f"\n{Fore.CYAN}⏳ Scanning region: {region}{Style.RESET_ALL}")
            
            tagging = boto3.client('resourcegroupstaggingapi', region_name=region)
            paginator = tagging.get_paginator('get_resources')
            
            for page in paginator.paginate():
                for resource in page['ResourceTagMappingList']:
                    arn = resource['ResourceARN']
                    service = arn.split(':')[2]
                    
                    if service not in resources:
                        resources[service] = []
                    
                    resources[service].append({
                        'region': region,
                        'arn': arn,
                        'tags': resource.get('Tags', [])
                    })
            
            if not page['ResourceTagMappingList']:
                print(f"{Fore.WHITE}No resources found in {region}{Style.RESET_ALL}")
                
        except ClientError as e:
            print(f"{Fore.RED}Error scanning region {region}: {e}{Style.RESET_ALL}")

    return resources

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
                json.dumps(resource['tags'])
            ])
    
    if table_data:
        headers = ['Service', 'Region', 'Resource ARN', 'Tags']
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
            print(f"  ARN: {resource['arn']}")
            print(f"  Tags: {json.dumps(resource['tags'])}")
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
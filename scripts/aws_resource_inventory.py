import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from tabulate import tabulate
from colorama import init, Fore, Style
import json
import concurrent.futures
import time
import random
from typing import Dict, List
from prettytable import PrettyTable

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

def scan_ec2_resources(region):
    """Scan EC2 resources in a region."""
    resources = []
    try:
        ec2 = boto3.client('ec2', region_name=region)
        
        # Get instances
        try:
            instances = ec2.describe_instances()
            for reservation in instances.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    resources.append({
                        'type': 'EC2 Instance',
                        'id': instance['InstanceId'],
                        'details': instance
                    })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning EC2 instances in {region}: {e}{Style.RESET_ALL}")

        # Get VPCs
        try:
            vpcs = ec2.describe_vpcs()
            for vpc in vpcs.get('Vpcs', []):
                resources.append({
                    'type': 'VPC',
                    'id': vpc['VpcId'],
                    'details': vpc
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning VPCs in {region}: {e}{Style.RESET_ALL}")

        # Get Subnets
        try:
            subnets = ec2.describe_subnets()
            for subnet in subnets.get('Subnets', []):
                resources.append({
                    'type': 'Subnet',
                    'id': subnet['SubnetId'],
                    'details': subnet
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning Subnets in {region}: {e}{Style.RESET_ALL}")

        # Get Security Groups
        try:
            security_groups = ec2.describe_security_groups()
            for sg in security_groups.get('SecurityGroups', []):
                resources.append({
                    'type': 'Security Group',
                    'id': sg['GroupId'],
                    'details': sg
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning Security Groups in {region}: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error scanning EC2 resources in {region}: {e}{Style.RESET_ALL}")
    
    return region, resources

def scan_elb_resources(region):
    """Scan ELB resources in a region."""
    resources = []
    try:
        elb = boto3.client('elbv2', region_name=region)
        
        # Get Load Balancers
        try:
            lbs = elb.describe_load_balancers()
            for lb in lbs.get('LoadBalancers', []):
                resources.append({
                    'type': 'Load Balancer',
                    'id': lb['LoadBalancerArn'],
                    'details': lb
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning Load Balancers in {region}: {e}{Style.RESET_ALL}")

        # Get Target Groups
        try:
            target_groups = elb.describe_target_groups()
            for tg in target_groups.get('TargetGroups', []):
                resources.append({
                    'type': 'Target Group',
                    'id': tg['TargetGroupArn'],
                    'details': tg
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning Target Groups in {region}: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error scanning ELB resources in {region}: {e}{Style.RESET_ALL}")
    
    return region, resources

def scan_rds_resources(region):
    """Scan RDS resources in a region."""
    resources = []
    try:
        rds = boto3.client('rds', region_name=region)
        
        # Get DB Instances
        try:
            instances = rds.describe_db_instances()
            for instance in instances.get('DBInstances', []):
                resources.append({
                    'type': 'RDS Instance',
                    'id': instance['DBInstanceIdentifier'],
                    'details': instance
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning RDS instances in {region}: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error scanning RDS resources in {region}: {e}{Style.RESET_ALL}")
    
    return region, resources

def scan_s3_resources():
    """Scan S3 resources (global service)."""
    resources = []
    try:
        s3 = boto3.client('s3')
        
        # Get Buckets
        try:
            buckets = s3.list_buckets()
            for bucket in buckets.get('Buckets', []):
                resources.append({
                    'type': 'S3 Bucket',
                    'id': bucket['Name'],
                    'details': bucket
                })
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                print(f"{Fore.RED}Error scanning S3 buckets: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error scanning S3 resources: {e}{Style.RESET_ALL}")
    
    return 'global', resources

def scan_resources():
    """Scan AWS resources across all regions."""
    print(f"\n{Fore.BLUE}🔍 Starting AWS Resource Scanner{Style.RESET_ALL}")
    
    regions = get_all_regions()
    print(f"\n{Fore.YELLOW}📍 Scanning Regions:{Style.RESET_ALL}")
    print(', '.join(regions))
    
    all_resources = {}
    
    # Scan S3 (global service)
    region, s3_resources = scan_s3_resources()
    if s3_resources:
        all_resources['S3'] = s3_resources
    
    # Scan regional services
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Scan EC2 resources
        ec2_futures = [executor.submit(scan_ec2_resources, region) for region in regions]
        for future in concurrent.futures.as_completed(ec2_futures):
            region, resources = future.result()
            if resources:
                all_resources[f'EC2 ({region})'] = resources
        
        # Scan ELB resources
        elb_futures = [executor.submit(scan_elb_resources, region) for region in regions]
        for future in concurrent.futures.as_completed(elb_futures):
            region, resources = future.result()
            if resources:
                all_resources[f'ELB ({region})'] = resources
        
        # Scan RDS resources
        rds_futures = [executor.submit(scan_rds_resources, region) for region in regions]
        for future in concurrent.futures.as_completed(rds_futures):
            region, resources = future.result()
            if resources:
                all_resources[f'RDS ({region})'] = resources
    
    return all_resources

def print_table_format(resources):
    """Print resources in table format."""
    print(f"\n{Fore.GREEN}📊 Resources (Table Format):{Style.RESET_ALL}")
    
    table_data = []
    for service, resource_list in resources.items():
        for resource in resource_list:
            table_data.append([
                service,
                resource['type'],
                resource['id'],
                json.dumps(resource['details'].get('Tags', []), default=str)
            ])
    
    if table_data:
        headers = ['Service', 'Type', 'Identifier', 'Tags']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    else:
        print("No resources found")

def print_list_format(resources):
    """Print resources in list format."""
    print(f"\n{Fore.GREEN}📝 Resources (List Format):{Style.RESET_ALL}")
    
    for service, resource_list in resources.items():
        print(f"\n{Fore.YELLOW}Service: {service}{Style.RESET_ALL}")
        for resource in resource_list:
            print(f"{Fore.CYAN}  Type: {resource['type']}{Style.RESET_ALL}")
            print(f"  Identifier: {resource['id']}")
            if resource['details'].get('Tags'):
                print(f"  Tags: {json.dumps(resource['details']['Tags'], default=str)}")
            print(f"  Details: {json.dumps(resource['details'], default=str)}")
            print("  ---")

def _get_core_services(self) -> Dict[str, List[str]]:
    """Get mapping of core AWS services and their important operations"""
    return {
        # Networking & VPC Services
        'ec2': [  # VPC-related operations are part of EC2 API
            # VPC Resources
            'DescribeVpcs',
            'DescribeSubnets',
            'DescribeRouteTables',
            'DescribeInternetGateways',
            'DescribeNatGateways',
            'DescribeVpcEndpoints',
            'DescribeVpcPeeringConnections',
            'DescribeVpnGateways',
            'DescribeVpnConnections',
            'DescribeTransitGateways',
            'DescribeNetworkAcls',
            # Security
            'DescribeSecurityGroups',
            'DescribeNetworkInterfaces',
            # EC2 Resources
            'DescribeInstances',
            'DescribeVolumes',
            'DescribeKeyPairs',
            'DescribeSnapshots',
            'DescribeAddresses',  # Elastic IPs
            'DescribePlacementGroups'
        ],
        
        # Load Balancing
        'elbv2': [  # Application and Network Load Balancers
            'DescribeLoadBalancers',
            'DescribeTargetGroups',
            'DescribeListeners',
            'DescribeRules'
        ],
        'elb': [  # Classic Load Balancers
            'DescribeLoadBalancers'
        ],

        # Compute Services
        'lambda': [
            'ListFunctions',
            'ListLayers',
            'ListEventSourceMappings'
        ],
        'ecs': [
            'ListClusters',
            'ListServices',
            'ListTaskDefinitions',
            'ListTasks'
        ],
        'eks': [
            'ListClusters',
            'ListNodegroups'
        ],
        'autoscaling': [
            'DescribeAutoScalingGroups',
            'DescribeLaunchConfigurations',
            'DescribeScalingPolicies'
        ],

        # Storage Services
        's3': [
            'ListBuckets',
            'GetBucketLocation',
            'GetBucketVersioning',
            'GetBucketEncryption'
        ],
        'efs': [
            'DescribeFileSystems',
            'DescribeMountTargets'
        ],
        'ebs': [
            'ListSnapshotBlocks'
        ],

        # Database Services
        'rds': [
            'DescribeDBInstances',
            'DescribeDBClusters',
            'DescribeDBSnapshots',
            'DescribeDBSubnetGroups',
            'DescribeOptionGroups'
        ],
        'dynamodb': [
            'ListTables',
            'DescribeTable',
            'ListBackups',
            'DescribeContinuousBackups'
        ],
        'elasticache': [
            'DescribeCacheClusters',
            'DescribeReplicationGroups',
            'DescribeCacheSubnetGroups'
        ],

        # DNS & Content Delivery
        'route53': [
            'ListHostedZones',
            'ListResourceRecordSets',
            'ListHealthChecks'
        ],
        'cloudfront': [
            'ListDistributions',
            'ListCachePolicies',
            'ListOriginRequestPolicies'
        ],

        # Security Services
        'iam': [
            'ListUsers',
            'ListRoles',
            'ListGroups',
            'ListPolicies',
            'ListServerCertificates',
            'ListInstanceProfiles'
        ],
        'kms': [
            'ListKeys',
            'ListAliases'
        ],
        'acm': [
            'ListCertificates'
        ],
        'waf': [
            'ListWebACLs',
            'ListRules'
        ],
        'wafv2': [
            'ListWebACLs',
            'ListIPSets',
            'ListRegexPatternSets'
        ],
        'secretsmanager': [
            'ListSecrets'
        ],

        # Container Services
        'ecr': [
            'DescribeRepositories',
            'DescribeImages'
        ],

        # Infrastructure as Code
        'cloudformation': [
            'ListStacks',
            'ListStackSets',
            'ListChangeSets'
        ],

        # Source Control & CI/CD
        'codecommit': [
            'ListRepositories',
            'ListBranches'
        ],
        'codebuild': [
            'ListProjects',
            'ListBuilds'
        ],
        'codepipeline': [
            'ListPipelines'
        ],

        # Monitoring & Logging
        'cloudwatch': [
            'ListMetrics',
            'DescribeAlarms',
            'DescribeAlarmHistory'
        ],
        'cloudtrail': [
            'DescribeTrails',
            'ListTags'
        ],
        'logs': [  # CloudWatch Logs
            'DescribeLogGroups',
            'DescribeMetricFilters'
        ],

        # Messaging Services
        'sns': [
            'ListTopics',
            'ListSubscriptions'
        ],
        'sqs': [
            'ListQueues',
            'GetQueueAttributes'
        ],

        # API Services
        'apigateway': [
            'GetRestApis',
            'GetStages',
            'GetDomainNames'
        ],
        'apigatewayv2': [  # HTTP/WebSocket APIs
            'GetApis',
            'GetStages'
        ]
    }

def _save_output(self, resources: Dict[str, List[Dict]], output_file: str = "aws_inventory.json") -> None:
    """Save the inventory results to a file and print formatted output"""
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(resources, f, indent=2, default=str)
    
    # Print summary header
    print("\n🔍 Starting AWS Resource Scanner")
    
    # Print scanned regions
    print("📍 Scanning Regions:")
    print(", ".join(self.regions))
    
    # Create PrettyTable for resources
    table = PrettyTable()
    table.field_names = ["Service", "Type", "Identifier", "Tags"]
    table.align = "l"  # Left align text
    table.max_width = 100  # Limit column width
    
    # Add rows to table
    for service, items in resources.items():
        for item in items:
            region = f" ({item.get('Region', '')})" if item.get('Region') else ''
            service_name = f"{service}{region}"
            
            # Truncate long tag lists
            tags = item.get('Tags', [])
            if len(str(tags)) > 50:
                tags = str(tags)[:47] + "..."
            
            table.add_row([
                service_name,
                item.get('Type', ''),
                item.get('Identifier', ''),
                tags
            ])
    
    # Print table
    print("\n📊 Resources (Table Format):")
    print(table)
    
    print(f"\n💾 Full inventory saved to: {output_file}")

def scan(self) -> None:
    """Main method to scan AWS resources"""
    try:
        resources = self._scan_resources()
        self._save_output(resources, "aws_inventory.json")
    except Exception as e:
        print(f"❌ Error scanning resources: {str(e)}")
        raise

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
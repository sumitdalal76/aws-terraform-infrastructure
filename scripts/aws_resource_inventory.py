#!/usr/bin/env python3
import boto3
import json
from datetime import datetime
import logging
from rich.console import Console
from rich.table import Table
from typing import Dict

from utils.aws_utils import make_api_call, get_aws_regions
from services.compute import ComputeServices
from services.database import DatabaseServices
from services.global_services import GlobalServices
from services.network import NetworkServices
from services.security import SecurityServices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = get_aws_regions(self.session)
        self.inventory_data = {}
        
        # Initialize service classes
        self.compute = ComputeServices(self.session)
        self.database = DatabaseServices(self.session)
        self.global_services = GlobalServices(self.session)
        self.network = NetworkServices(self.session)
        self.security = SecurityServices(self.session)

    def print_scan_scope(self):
        """Print the scope of the inventory scan."""
        console.print("\n[bold cyan]=== AWS Resource Inventory Scan Scope ===[/bold cyan]\n")

        services_table = Table(title="Services to Scan", show_header=True, header_style="bold magenta")
        services_table.add_column("Service Type")
        services_table.add_column("Resources")

        # Global Services
        services_table.add_row(
            "Global Services",
            "• IAM (Users, Roles, Groups)\n"
            "• S3 Buckets\n"
            "• Route53 Hosted Zones\n"
            "• CloudFront Distributions\n"
            "• WAF Rules & ACLs"
        )

        # Security Services
        services_table.add_row(
            "Security Services",
            "• Security Groups\n"
            "• Network ACLs\n"
            "• ACM Certificates\n"
            "• KMS Keys\n"
            "• Secrets Manager Secrets\n"
            "• IAM Roles & Policies"
        )

        # Compute & Containers
        services_table.add_row(
            "Compute & Containers",
            "• EC2 Instances\n"
            "• Auto Scaling Groups\n"
            "• Launch Templates\n"
            "• ECS Clusters & Services\n"
            "• EKS Clusters\n"
            "• Lambda Functions\n"
            "• ECR Repositories"
        )

        # Storage & Database
        services_table.add_row(
            "Storage & Database",
            "• EBS Volumes\n"
            "• EFS File Systems\n"
            "• RDS Instances & Clusters\n"
            "• DynamoDB Tables\n"
            "• ElastiCache Clusters\n"
            "• S3 Bucket Policies"
        )

        # Networking
        services_table.add_row(
            "Networking",
            "• VPCs & Subnets\n"
            "• Internet Gateways\n"
            "• NAT Gateways\n"
            "• Transit Gateways\n"
            "• VPC Endpoints\n"
            "• Route Tables\n"
            "• Network Interfaces\n"
            "• Elastic IPs"
        )

        console.print(services_table)
        console.print("\n")

    def print_consolidated_table(self, inventory_data: Dict):
        """Print a consolidated view of all resources in table format."""
        console.print("\n[bold cyan]=== AWS Resource Summary ===[/bold cyan]\n")

        # Global Resources Summary
        console.print("[bold blue]Global Resources[/bold blue]\n")
        
        # IAM Resources
        if inventory_data.get('iam'):
            iam_data = inventory_data['iam']
            
            # IAM Users
            if iam_data.get('users'):
                users_table = Table(title="IAM Users", show_header=True, header_style="bold magenta")
                users_table.add_column("Username")
                users_table.add_column("User ID")
                users_table.add_column("ARN")
                users_table.add_column("Create Date")
                
                for user in iam_data['users']:
                    users_table.add_row(
                        user['UserName'],
                        user['UserId'],
                        user['Arn'],
                        user['CreateDate']
                    )
                console.print(users_table)
                console.print("\n")
            
            # IAM Roles
            if iam_data.get('roles'):
                roles_table = Table(title="IAM Roles", show_header=True, header_style="bold magenta")
                roles_table.add_column("Role Name")
                roles_table.add_column("Role ID")
                roles_table.add_column("ARN")
                roles_table.add_column("Description")
                roles_table.add_column("Create Date")
                
                for role in iam_data['roles']:
                    roles_table.add_row(
                        role['RoleName'],
                        role['RoleId'],
                        role['Arn'],
                        role['Description'],
                        role['CreateDate']
                    )
                console.print(roles_table)
                console.print("\n")
            
            # IAM Groups
            if iam_data.get('groups'):
                groups_table = Table(title="IAM Groups", show_header=True, header_style="bold magenta")
                groups_table.add_column("Group Name")
                groups_table.add_column("Group ID")
                groups_table.add_column("ARN")
                groups_table.add_column("Create Date")
                
                for group in iam_data['groups']:
                    groups_table.add_row(
                        group['GroupName'],
                        group['GroupId'],
                        group['Arn'],
                        group['CreateDate']
                    )
                console.print(groups_table)
                console.print("\n")

        # S3 Buckets
        if inventory_data.get('s3_buckets'):
            s3_table = Table(title="S3 Buckets", show_header=True, header_style="bold magenta")
            s3_table.add_column("Bucket Name")
            s3_table.add_column("Creation Date")
            s3_table.add_column("Policy")
            
            for bucket in inventory_data['s3_buckets']:
                s3_table.add_row(
                    bucket['Name'],
                    bucket['CreationDate'],
                    bucket.get('Policy', 'No policy')
                )
            console.print(s3_table)
            console.print("\n")

        # Route53 Hosted Zones
        if inventory_data.get('route53_zones'):
            route53_table = Table(title="Route53 Hosted Zones", show_header=True, header_style="bold magenta")
            route53_table.add_column("Zone Name")
            route53_table.add_column("Zone ID")
            route53_table.add_column("Record Count")
            route53_table.add_column("Type")
            
            for zone in inventory_data['route53_zones']:
                route53_table.add_row(
                    zone['Name'],
                    zone['Id'],
                    str(zone['RecordCount']),
                    'Private' if zone['Private'] else 'Public'
                )
            console.print(route53_table)
            console.print("\n")

        # CloudFront Distributions
        if inventory_data.get('cloudfront'):
            cloudfront_table = Table(title="CloudFront Distributions", show_header=True, header_style="bold magenta")
            cloudfront_table.add_column("Distribution ID")
            cloudfront_table.add_column("Domain Name")
            cloudfront_table.add_column("Status")
            cloudfront_table.add_column("Enabled")
            cloudfront_table.add_column("Origins")
            
            for dist in inventory_data['cloudfront']:
                cloudfront_table.add_row(
                    dist['Id'],
                    dist['DomainName'],
                    dist['Status'],
                    str(dist['Enabled']),
                    ', '.join(dist['Origins'])
                )
            console.print(cloudfront_table)
            console.print("\n")

        # WAF Rules & ACLs
        if inventory_data.get('waf', {}).get('WebACLs'):
            waf_table = Table(title="WAF Web ACLs", show_header=True, header_style="bold magenta")
            waf_table.add_column("Name")
            waf_table.add_column("ID")
            waf_table.add_column("ARN")
            waf_table.add_column("Scope")
            
            for acl in inventory_data['waf']['WebACLs']:
                waf_table.add_row(
                    acl['Name'],
                    acl['Id'],
                    acl['ARN'],
                    acl['Scope']
                )
            console.print(waf_table)
            console.print("\n")

        # Regional Resources Summary
        has_regional_resources = any(
            any(resource_list for resource_list in resources.values() if resource_list)
            for resources in inventory_data['regions'].values()
        )
        
        if has_regional_resources:
            console.print("[bold blue]Regional Resources[/bold blue]\n")
            
            for region, resources in inventory_data['regions'].items():
                if not any(resources.values()):
                    continue
                    
                console.print(f"\n[bold green]Region: {region}[/bold green]")
                
                # VPCs
                if resources.get('vpc_info', {}).get('vpcs'):
                    vpc_table = Table(title="VPCs", show_header=True, header_style="bold magenta")
                    vpc_table.add_column("VPC ID")
                    vpc_table.add_column("CIDR Block")
                    vpc_table.add_column("State")
                    vpc_table.add_column("Is Default")
                    vpc_table.add_column("Name")
                    
                    for vpc in resources['vpc_info']['vpcs']:
                        name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                        vpc_table.add_row(
                            vpc['VpcId'],
                            vpc['CidrBlock'],
                            vpc['State'],
                            str(vpc['IsDefault']),
                            name
                        )
                    console.print(vpc_table)
                    console.print("\n")

                # Subnets
                if resources.get('vpc_info', {}).get('subnets'):
                    subnet_table = Table(title="Subnets", show_header=True, header_style="bold magenta")
                    subnet_table.add_column("Subnet ID")
                    subnet_table.add_column("VPC ID")
                    subnet_table.add_column("CIDR Block")
                    subnet_table.add_column("AZ")
                    subnet_table.add_column("State")
                    subnet_table.add_column("Name")
                    
                    for subnet in resources['vpc_info']['subnets']:
                        name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                        subnet_table.add_row(
                            subnet['SubnetId'],
                            subnet['VpcId'],
                            subnet['CidrBlock'],
                            subnet['AvailabilityZone'],
                            subnet['State'],
                            name
                        )
                    console.print(subnet_table)
                    console.print("\n")

                # Internet Gateways
                if resources.get('internet_gateways'):
                    igw_table = Table(title="Internet Gateways", show_header=True, header_style="bold magenta")
                    igw_table.add_column("IGW ID")
                    igw_table.add_column("State")
                    igw_table.add_column("VPC ID")
                    igw_table.add_column("Name")
                    
                    for igw in resources['internet_gateways']:
                        name = next((tag['Value'] for tag in igw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                        attachments = [att['VpcId'] for att in igw['Attachments'] if att['State'] == 'available']
                        igw_table.add_row(
                            igw['InternetGatewayId'],
                            'Attached' if attachments else 'Detached',
                            '\n'.join(attachments) or 'N/A',
                            name
                        )
                    console.print(igw_table)
                    console.print("\n")

                # NAT Gateways
                if resources.get('nat_gateways'):
                    nat_table = Table(title="NAT Gateways", show_header=True, header_style="bold magenta")
                    nat_table.add_column("NAT ID")
                    nat_table.add_column("VPC ID")
                    nat_table.add_column("Subnet ID")
                    nat_table.add_column("State")
                    nat_table.add_column("Name")
                    
                    for nat in resources['nat_gateways']:
                        name = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                        nat_table.add_row(
                            nat['NatGatewayId'],
                            nat['VpcId'],
                            nat['SubnetId'],
                            nat['State'],
                            name
                        )
                    console.print(nat_table)
                    console.print("\n")

                # Transit Gateways
                if resources.get('transit_gateways'):
                    tgw_table = Table(title="Transit Gateways", show_header=True, header_style="bold magenta")
                    tgw_table.add_column("TGW ID")
                    tgw_table.add_column("State")
                    tgw_table.add_column("Owner ID")
                    tgw_table.add_column("Description")
                    
                    for tgw in resources['transit_gateways']:
                        tgw_table.add_row(
                            tgw['TransitGatewayId'],
                            tgw['State'],
                            tgw['OwnerId'],
                            tgw['Description']
                        )
                    console.print(tgw_table)
                    console.print("\n")

                # VPC Endpoints
                if resources.get('vpc_endpoints'):
                    endpoint_table = Table(title="VPC Endpoints", show_header=True, header_style="bold magenta")
                    endpoint_table.add_column("Endpoint ID")
                    endpoint_table.add_column("VPC ID")
                    endpoint_table.add_column("Service Name")
                    endpoint_table.add_column("Type")
                    endpoint_table.add_column("State")
                    
                    for endpoint in resources['vpc_endpoints']:
                        endpoint_table.add_row(
                            endpoint['VpcEndpointId'],
                            endpoint['VpcId'],
                            endpoint['ServiceName'],
                            endpoint['Type'],
                            endpoint['State']
                        )
                    console.print(endpoint_table)
                    console.print("\n")

                # Route Tables
                if resources.get('route_tables'):
                    rt_table = Table(title="Route Tables", show_header=True, header_style="bold magenta")
                    rt_table.add_column("Route Table ID")
                    rt_table.add_column("VPC ID")
                    rt_table.add_column("Main")
                    rt_table.add_column("Associated Subnets")
                    rt_table.add_column("Routes Count")
                    
                    for rt in resources['route_tables']:
                        is_main = any(assoc.get('Main', False) for assoc in rt['Associations'])
                        associated_subnets = [assoc['SubnetId'] for assoc in rt['Associations'] if 'SubnetId' in assoc]
                        rt_table.add_row(
                            rt['RouteTableId'],
                            rt['VpcId'],
                            'Yes' if is_main else 'No',
                            '\n'.join(associated_subnets) or 'None',
                            str(len(rt['Routes']))
                        )
                    console.print(rt_table)
                    console.print("\n")

                # Network Interfaces
                if resources.get('network_interfaces'):
                    eni_table = Table(title="Network Interfaces", show_header=True, header_style="bold magenta")
                    eni_table.add_column("ENI ID")
                    eni_table.add_column("Subnet ID")
                    eni_table.add_column("VPC ID")
                    eni_table.add_column("Private IP")
                    eni_table.add_column("Status")
                    
                    for eni in resources['network_interfaces']:
                        eni_table.add_row(
                            eni['NetworkInterfaceId'],
                            eni['SubnetId'],
                            eni['VpcId'],
                            eni['PrivateIpAddress'],
                            eni['Status']
                        )
                    console.print(eni_table)
                    console.print("\n")

                # Elastic IPs
                if resources.get('elastic_ips'):
                    eip_table = Table(title="Elastic IPs", show_header=True, header_style="bold magenta")
                    eip_table.add_column("Public IP")
                    eip_table.add_column("Allocation ID")
                    eip_table.add_column("Instance ID")
                    eip_table.add_column("Network Interface ID")
                    
                    for eip in resources['elastic_ips']:
                        eip_table.add_row(
                            eip['PublicIp'],
                            eip['AllocationId'] or 'N/A',
                            eip['InstanceId'],
                            eip['NetworkInterfaceId']
                        )
                    console.print(eip_table)
                    console.print("\n")

                # EC2 Instances
                if resources.get('ec2_instances'):
                    ec2_table = Table(title="EC2 Instances", show_header=True, header_style="bold magenta")
                    ec2_table.add_column("Instance ID")
                    ec2_table.add_column("Name")
                    ec2_table.add_column("Type")
                    ec2_table.add_column("State")
                    ec2_table.add_column("Private IP")
                    ec2_table.add_column("Public IP")
                    
                    for instance in resources['ec2_instances']:
                        ec2_table.add_row(
                            instance['InstanceId'],
                            instance['Name'],
                            instance['InstanceType'],
                            instance['State'],
                            instance['PrivateIpAddress'],
                            instance['PublicIpAddress']
                        )
                    console.print(ec2_table)
                    console.print("\n")

                # Auto Scaling Groups
                if resources.get('auto_scaling_groups'):
                    asg_table = Table(title="Auto Scaling Groups", show_header=True, header_style="bold magenta")
                    asg_table.add_column("Name")
                    asg_table.add_column("Desired")
                    asg_table.add_column("Min")
                    asg_table.add_column("Max")
                    asg_table.add_column("Instances")
                    asg_table.add_column("Health Check")
                    asg_table.add_column("Status")
                    
                    for asg in resources['auto_scaling_groups']:
                        asg_table.add_row(
                            asg['AutoScalingGroupName'],
                            str(asg['DesiredCapacity']),
                            str(asg['MinSize']),
                            str(asg['MaxSize']),
                            str(asg['InstanceCount']),
                            asg['HealthCheckType'],
                            asg['Status']
                        )
                    console.print(asg_table)
                    console.print("\n")

                # Launch Templates
                if resources.get('launch_templates'):
                    lt_table = Table(title="Launch Templates", show_header=True, header_style="bold magenta")
                    lt_table.add_column("Name")
                    lt_table.add_column("ID")
                    lt_table.add_column("Default Version")
                    lt_table.add_column("Latest Version")
                    lt_table.add_column("Instance Type")
                    lt_table.add_column("Image ID")
                    
                    for template in resources['launch_templates']:
                        lt_table.add_row(
                            template['LaunchTemplateName'],
                            template['LaunchTemplateId'],
                            str(template['DefaultVersion']),
                            str(template['LatestVersion']),
                            template['InstanceType'],
                            template['ImageId']
                        )
                    console.print(lt_table)
                    console.print("\n")

                # ECS Clusters
                if resources.get('ecs_clusters'):
                    ecs_table = Table(title="ECS Clusters", show_header=True, header_style="bold magenta")
                    ecs_table.add_column("Cluster Name")
                    ecs_table.add_column("Status")
                    ecs_table.add_column("Active Services")
                    ecs_table.add_column("Running Tasks")
                    ecs_table.add_column("Pending Tasks")
                    ecs_table.add_column("Container Instances")
                    
                    for cluster in resources['ecs_clusters']:
                        ecs_table.add_row(
                            cluster['ClusterName'],
                            cluster['Status'],
                            str(cluster['ActiveServices']),
                            str(cluster['RunningTasks']),
                            str(cluster['PendingTasks']),
                            str(cluster['ContainerInstances'])
                        )
                    console.print(ecs_table)
                    console.print("\n")

                # EKS Clusters
                if resources.get('eks_clusters'):
                    eks_table = Table(title="EKS Clusters", show_header=True, header_style="bold magenta")
                    eks_table.add_column("Name")
                    eks_table.add_column("Status")
                    eks_table.add_column("Version")
                    eks_table.add_column("Platform Version")
                    eks_table.add_column("VPC ID")
                    
                    for cluster in resources['eks_clusters']:
                        eks_table.add_row(
                            cluster['Name'],
                            cluster['Status'],
                            cluster['Version'],
                            cluster['PlatformVersion'],
                            cluster['VpcId']
                        )
                    console.print(eks_table)
                    console.print("\n")

                # Lambda Functions
                if resources.get('lambda_functions'):
                    lambda_table = Table(title="Lambda Functions", show_header=True, header_style="bold magenta")
                    lambda_table.add_column("Function Name")
                    lambda_table.add_column("Runtime")
                    lambda_table.add_column("Memory (MB)")
                    lambda_table.add_column("Timeout (s)")
                    lambda_table.add_column("Last Modified")
                    
                    for function in resources['lambda_functions']:
                        lambda_table.add_row(
                            function['FunctionName'],
                            function['Runtime'],
                            str(function['Memory']),
                            str(function['Timeout']),
                            function['LastModified']
                        )
                    console.print(lambda_table)
                    console.print("\n")

                # ECR Repositories
                if resources.get('ecr_repositories'):
                    ecr_table = Table(title="ECR Repositories", show_header=True, header_style="bold magenta")
                    ecr_table.add_column("Repository Name")
                    ecr_table.add_column("URI")
                    ecr_table.add_column("Image Count")
                    ecr_table.add_column("Created At")
                    ecr_table.add_column("Encryption Type")
                    
                    for repo in resources['ecr_repositories']:
                        ecr_table.add_row(
                            repo['RepositoryName'],
                            repo['RepositoryUri'],
                            str(repo['ImageCount']),
                            repo['CreatedAt'],
                            repo['EncryptionType']
                        )
                    console.print(ecr_table)
                    console.print("\n")

                # DynamoDB Tables
                if resources.get('dynamodb_tables'):
                    dynamo_table = Table(title="DynamoDB Tables", show_header=True, header_style="bold magenta")
                    dynamo_table.add_column("Table Name")
                    dynamo_table.add_column("Status")
                    dynamo_table.add_column("Item Count")
                    dynamo_table.add_column("Size (Bytes)")
                    dynamo_table.add_column("Provisioned Throughput")
                    
                    for table in resources['dynamodb_tables']:
                        dynamo_table.add_row(
                            table['TableName'],
                            table['Status'],
                            str(table['ItemCount']),
                            str(table['SizeBytes']),
                            table['ProvisionedThroughput']
                        )
                    console.print(dynamo_table)
                    console.print("\n")

                # Security Groups
                if resources.get('security_groups'):
                    sg_table = Table(title="Security Groups", show_header=True, header_style="bold magenta")
                    sg_table.add_column("Group ID")
                    sg_table.add_column("Name")
                    sg_table.add_column("VPC ID")
                    sg_table.add_column("Description")
                    sg_table.add_column("Inbound Rules")
                    
                    for sg in resources['security_groups']:
                        inbound_rules = "\n".join([
                            f"{rule['Protocol']}:{rule['FromPort']}-{rule['ToPort']} from {','.join(rule['Source'])}"
                            for rule in sg['InboundRules']
                        ])
                        sg_table.add_row(
                            sg['GroupId'],
                            sg['GroupName'],
                            sg['VpcId'],
                            sg['Description'],
                            inbound_rules
                        )
                    console.print(sg_table)
                    console.print("\n")

                # Network ACLs
                if resources.get('network_acls'):
                    nacl_table = Table(title="Network ACLs", show_header=True, header_style="bold magenta")
                    nacl_table.add_column("NACL ID")
                    nacl_table.add_column("VPC ID")
                    nacl_table.add_column("Is Default")
                    nacl_table.add_column("Associated Subnets")
                    
                    for nacl in resources['network_acls']:
                        nacl_table.add_row(
                            nacl['NetworkAclId'],
                            nacl['VpcId'],
                            str(nacl['IsDefault']),
                            "\n".join(nacl['Associations'])
                        )
                    console.print(nacl_table)
                    console.print("\n")

                # ACM Certificates
                if resources.get('acm_certificates'):
                    cert_table = Table(title="ACM Certificates", show_header=True, header_style="bold magenta")
                    cert_table.add_column("Domain Name")
                    cert_table.add_column("Status")
                    cert_table.add_column("Type")
                    cert_table.add_column("Expires On")
                    
                    for cert in resources['acm_certificates']:
                        cert_table.add_row(
                            cert['DomainName'],
                            cert['Status'],
                            cert['Type'],
                            str(cert['ExpiresOn'])
                        )
                    console.print(cert_table)
                    console.print("\n")

                # KMS Keys
                if resources.get('kms_keys'):
                    kms_table = Table(title="KMS Keys", show_header=True, header_style="bold magenta")
                    kms_table.add_column("Key ID")
                    kms_table.add_column("State")
                    kms_table.add_column("Description")
                    kms_table.add_column("Key Manager")
                    kms_table.add_column("Aliases")
                    
                    for key in resources['kms_keys']:
                        kms_table.add_row(
                            key['KeyId'],
                            key['State'],
                            key['Description'],
                            key['KeyManager'],
                            "\n".join(key['Aliases'])
                        )
                    console.print(kms_table)
                    console.print("\n")

                # Secrets Manager Secrets
                if resources.get('secrets'):
                    secrets_table = Table(title="Secrets Manager Secrets", show_header=True, header_style="bold magenta")
                    secrets_table.add_column("Name")
                    secrets_table.add_column("Description")
                    secrets_table.add_column("Last Changed")
                    secrets_table.add_column("Last Accessed")
                    
                    for secret in resources['secrets']:
                        secrets_table.add_row(
                            secret['Name'],
                            secret['Description'],
                            str(secret['LastChangedDate']),
                            str(secret['LastAccessedDate'])
                        )
                    console.print(secrets_table)
                    console.print("\n")

                # IAM Policies (Customer Managed)
                if resources.get('iam_policies'):
                    policies_table = Table(title="IAM Policies (Customer Managed)", show_header=True, header_style="bold magenta")
                    policies_table.add_column("Policy Name")
                    policies_table.add_column("Description")
                    policies_table.add_column("Version Count")
                    policies_table.add_column("Attachment Count")
                    
                    for policy in resources['iam_policies']:
                        policies_table.add_row(
                            policy['PolicyName'],
                            policy['Description'],
                            str(policy['VersionCount']),
                            str(policy['AttachmentCount'])
                        )
                    console.print(policies_table)
                    console.print("\n")

                # EBS Volumes
                if resources.get('ebs_volumes'):
                    ebs_table = Table(title="EBS Volumes", show_header=True, header_style="bold magenta")
                    ebs_table.add_column("Volume ID")
                    ebs_table.add_column("Size (GB)")
                    ebs_table.add_column("Type")
                    ebs_table.add_column("State")
                    ebs_table.add_column("Encrypted")
                    ebs_table.add_column("IOPS")
                    ebs_table.add_column("Attached To")
                    
                    for volume in resources['ebs_volumes']:
                        attachments = "\n".join([
                            f"{att['InstanceId']} ({att['Device']})"
                            for att in volume['Attachments']
                        ]) or "Not Attached"
                        ebs_table.add_row(
                            volume['VolumeId'],
                            str(volume['Size']),
                            volume['VolumeType'],
                            volume['State'],
                            str(volume['Encrypted']),
                            str(volume['IOPS']),
                            attachments
                        )
                    console.print(ebs_table)
                    console.print("\n")

                # EFS File Systems
                if resources.get('efs_filesystems'):
                    efs_table = Table(title="EFS File Systems", show_header=True, header_style="bold magenta")
                    efs_table.add_column("File System ID")
                    efs_table.add_column("Name")
                    efs_table.add_column("Size (Bytes)")
                    efs_table.add_column("State")
                    efs_table.add_column("Performance Mode")
                    efs_table.add_column("Encrypted")
                    efs_table.add_column("Mount Targets")
                    
                    for fs in resources['efs_filesystems']:
                        efs_table.add_row(
                            fs['FileSystemId'],
                            fs['Name'],
                            str(fs['Size']),
                            fs['LifeCycleState'],
                            fs['PerformanceMode'],
                            str(fs['Encrypted']),
                            str(fs['MountTargets'])
                        )
                    console.print(efs_table)
                    console.print("\n")

                # RDS Instances
                if resources.get('rds_info', {}).get('instances'):
                    rds_table = Table(title="RDS Instances", show_header=True, header_style="bold magenta")
                    rds_table.add_column("Identifier")
                    rds_table.add_column("Engine")
                    rds_table.add_column("Version")
                    rds_table.add_column("Class")
                    rds_table.add_column("Status")
                    rds_table.add_column("Multi-AZ")
                    rds_table.add_column("Storage (GB)")
                    
                    for instance in resources['rds_info']['instances']:
                        rds_table.add_row(
                            instance['DBInstanceIdentifier'],
                            instance['Engine'],
                            instance['EngineVersion'],
                            instance['DBInstanceClass'],
                            instance['Status'],
                            str(instance['MultiAZ']),
                            str(instance['AllocatedStorage'])
                        )
                    console.print(rds_table)
                    console.print("\n")

                # RDS Clusters
                if resources.get('rds_info', {}).get('clusters'):
                    clusters_table = Table(title="RDS Clusters", show_header=True, header_style="bold magenta")
                    clusters_table.add_column("Identifier")
                    clusters_table.add_column("Engine")
                    clusters_table.add_column("Version")
                    clusters_table.add_column("Status")
                    clusters_table.add_column("Multi-AZ")
                    clusters_table.add_column("Instances")
                    clusters_table.add_column("Database")
                    
                    for cluster in resources['rds_info']['clusters']:
                        clusters_table.add_row(
                            cluster['DBClusterIdentifier'],
                            cluster['Engine'],
                            cluster['EngineVersion'],
                            cluster['Status'],
                            str(cluster['MultiAZ']),
                            str(cluster['InstanceCount']),
                            cluster['DatabaseName']
                        )
                    console.print(clusters_table)
                    console.print("\n")

                # DynamoDB Tables
                if resources.get('dynamodb_tables'):
                    dynamodb_table = Table(title="DynamoDB Tables", show_header=True, header_style="bold magenta")
                    dynamodb_table.add_column("Table Name")
                    dynamodb_table.add_column("Status")
                    dynamodb_table.add_column("Items")
                    dynamodb_table.add_column("Size (Bytes)")
                    dynamodb_table.add_column("Billing Mode")
                    dynamodb_table.add_column("Provisioned Throughput")
                    
                    for table in resources['dynamodb_tables']:
                        throughput = f"Read: {table['ProvisionedThroughput']['ReadCapacityUnits']}, " \
                                   f"Write: {table['ProvisionedThroughput']['WriteCapacityUnits']}"
                        dynamodb_table.add_row(
                            table['TableName'],
                            table['Status'],
                            str(table['ItemCount']),
                            str(table['SizeBytes']),
                            table['BillingMode'],
                            throughput if table['BillingMode'] == 'PROVISIONED' else 'On-Demand'
                        )
                    console.print(dynamodb_table)
                    console.print("\n")

                # ElastiCache Clusters
                if resources.get('elasticache_clusters'):
                    cache_table = Table(title="ElastiCache Clusters", show_header=True, header_style="bold magenta")
                    cache_table.add_column("Cluster ID")
                    cache_table.add_column("Engine")
                    cache_table.add_column("Version")
                    cache_table.add_column("Node Type")
                    cache_table.add_column("Nodes")
                    cache_table.add_column("Status")
                    cache_table.add_column("AZ")
                    
                    for cluster in resources['elasticache_clusters']:
                        cache_table.add_row(
                            cluster['CacheClusterId'],
                            cluster['Engine'],
                            cluster['EngineVersion'],
                            cluster['CacheNodeType'],
                            str(cluster['NumCacheNodes']),
                            cluster['Status'],
                            cluster['PreferredAvailabilityZone']
                        )
                    console.print(cache_table)
                    console.print("\n")

                # S3 Bucket Policies
                if resources.get('s3_bucket_policies'):
                    policy_table = Table(title="S3 Bucket Policies", show_header=True, header_style="bold magenta")
                    policy_table.add_column("Bucket Name")
                    policy_table.add_column("Has Policy")
                    
                    for policy in resources['s3_bucket_policies']:
                        policy_table.add_row(
                            policy['BucketName'],
                            str(policy['PolicyExists'])
                        )
                    console.print(policy_table)
                    console.print("\n")

    def generate_inventory(self) -> Dict:
        """Generate complete inventory of AWS resources."""
        self.print_scan_scope()
        
        timestamp = datetime.now().isoformat()
        
        # Global Services
        self.inventory_data = {
            'timestamp': timestamp,
            'regions': {},
            'iam': make_api_call(self.global_services.get_iam_info),
            's3_buckets': make_api_call(self.global_services.get_s3_buckets),
            'route53_zones': make_api_call(self.global_services.get_route53_info),
            'cloudfront': make_api_call(self.global_services.get_cloudfront_distributions),
            'waf': make_api_call(self.global_services.get_waf_info)
        }
        
        for region in self.regions:
            console.print(f"Scanning region: {region}", style="dim")
            
            regional_data = {
                # Networking Services
                'vpc_info': make_api_call(self.network.get_vpcs_and_subnets, region),
                'internet_gateways': make_api_call(self.network.get_internet_gateways, region),
                'nat_gateways': make_api_call(self.network.get_nat_gateways, region),
                'transit_gateways': make_api_call(self.network.get_transit_gateways, region),
                'vpc_endpoints': make_api_call(self.network.get_vpc_endpoints, region),
                'route_tables': make_api_call(self.network.get_route_tables, region),
                'network_interfaces': make_api_call(self.network.get_network_interfaces, region),
                'elastic_ips': make_api_call(self.network.get_elastic_ips, region),
                
                # Storage & Database Services
                'ebs_volumes': make_api_call(self.database.get_ebs_volumes, region),
                'efs_filesystems': make_api_call(self.database.get_efs_filesystems, region),
                'rds_info': make_api_call(self.database.get_rds_instances, region),
                'dynamodb_tables': make_api_call(self.database.get_dynamodb_tables, region),
                'elasticache_clusters': make_api_call(self.database.get_elasticache_clusters, region),
                's3_bucket_policies': make_api_call(self.database.get_s3_bucket_policies),
                
                # Compute & Containers
                'ec2_instances': make_api_call(self.compute.get_ec2_instances, region),
                'auto_scaling_groups': make_api_call(self.compute.get_auto_scaling_groups, region),
                'launch_templates': make_api_call(self.compute.get_launch_templates, region),
                'ecs_clusters': make_api_call(self.compute.get_ecs_info, region),
                'eks_clusters': make_api_call(self.compute.get_eks_clusters, region),
                'lambda_functions': make_api_call(self.compute.get_lambda_functions, region),
                'ecr_repositories': make_api_call(self.compute.get_ecr_repositories, region),
                
                # Security Services
                'security_groups': make_api_call(self.security.get_security_groups, region),
                'network_acls': make_api_call(self.security.get_network_acls, region),
                'acm_certificates': make_api_call(self.security.get_acm_certificates, region),
                'kms_keys': make_api_call(self.security.get_kms_keys, region),
                'secrets': make_api_call(self.security.get_secrets, region),
                'iam_policies': make_api_call(self.security.get_iam_policies, region),
                
                # Database
                'rds_instances': make_api_call(self.database.get_rds_instances, region),
                'dynamodb_tables': make_api_call(self.database.get_dynamodb_tables, region),
                
                # Network
                'vpcs': make_api_call(self.network.get_vpcs, region),
                'load_balancers': make_api_call(self.network.get_elb_info, region)
            }
            
            self.inventory_data['regions'][region] = {
                k: v for k, v in regional_data.items() if v is not None
            }
        
        return self.inventory_data

    def save_inventory(self, inventory: Dict, filename: str = 'aws_inventory.json'):
        """Save inventory to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2, default=str)
        logger.info(f"Inventory saved to {filename}")

def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]\n")
    
    inventory = AWSResourceInventory()
    resources = inventory.generate_inventory()
    inventory.save_inventory(resources)
    
    console.print("\n[bold cyan]AWS Resource Inventory Complete![/bold cyan]")

if __name__ == "__main__":
    main()
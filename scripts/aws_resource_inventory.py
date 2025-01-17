#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
import json

# Initialize console for table output
console = Console()

def list_all_resources():
    session = boto3.Session()
    ec2_client = session.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # Supported services
    all_resources = {
        "ec2_instances": [],
        "vpcs": [],
        "subnets": [],
        "security_groups": [],
        "elastic_ips": [],
    }

    for region in regions:
        console.print(f"[bold cyan]Scanning region: {region}[/bold cyan]")
        ec2_client = session.client('ec2', region_name=region)

        try:
            # EC2 Instances
            instances = ec2_client.describe_instances().get("Reservations", [])
            ec2_instances = [
                {
                    "Region": region,
                    "InstanceId": instance["InstanceId"],
                    "State": instance["State"]["Name"],
                    "Type": instance["InstanceType"],
                    "PrivateIp": instance.get("PrivateIpAddress"),
                    "PublicIp": instance.get("PublicIpAddress"),
                }
                for reservation in instances
                for instance in reservation["Instances"]
            ]
            all_resources["ec2_instances"].extend(ec2_instances)

            # VPCs (Exclude default VPCs)
            vpcs = ec2_client.describe_vpcs().get("Vpcs", [])
            vpc_list = [
                {
                    "Region": region,
                    "VpcId": vpc["VpcId"],
                    "CidrBlock": vpc["CidrBlock"],
                    "State": vpc["State"],
                }
                for vpc in vpcs
                if not vpc["IsDefault"]
            ]
            all_resources["vpcs"].extend(vpc_list)

            # Subnets
            subnets = ec2_client.describe_subnets().get("Subnets", [])
            subnet_list = [
                {
                    "Region": region,
                    "SubnetId": subnet["SubnetId"],
                    "VpcId": subnet["VpcId"],
                    "CidrBlock": subnet["CidrBlock"],
                    "AvailabilityZone": subnet["AvailabilityZone"],
                }
                for subnet in subnets
            ]
            all_resources["subnets"].extend(subnet_list)

            # Security Groups
            security_groups = ec2_client.describe_security_groups().get("SecurityGroups", [])
            sg_list = [
                {
                    "Region": region,
                    "GroupId": sg["GroupId"],
                    "GroupName": sg["GroupName"],
                    "VpcId": sg.get("VpcId", "N/A"),
                    "Description": sg["Description"],
                }
                for sg in security_groups
            ]
            all_resources["security_groups"].extend(sg_list)

            # Elastic IPs
            eips = ec2_client.describe_addresses().get("Addresses", [])
            eip_list = [
                {
                    "Region": region,
                    "PublicIp": eip["PublicIp"],
                    "InstanceId": eip.get("InstanceId", "N/A"),
                    "AllocationId": eip.get("AllocationId", "N/A"),
                }
                for eip in eips
            ]
            all_resources["elastic_ips"].extend(eip_list)

        except ClientError as e:
            console.print(f"[bold red]Error fetching data in {region}: {e}[/bold red]")
            continue

    # Print consolidated tables
    print_table("EC2 Instances", all_resources["ec2_instances"])
    print_table("VPCs", all_resources["vpcs"])
    print_table("Subnets", all_resources["subnets"])
    print_table("Security Groups", all_resources["security_groups"])
    print_table("Elastic IPs", all_resources["elastic_ips"])

    # Save inventory to JSON
    with open("aws_all_resources.json", "w") as f:
        json.dump(all_resources, f, indent=4)
    console.print("[bold cyan]Inventory saved to aws_all_resources.json[/bold cyan]")

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
        table.add_row(*[str(item[key]) for key in keys])

    console.print(table)

if __name__ == "__main__":
    list_all_resources()

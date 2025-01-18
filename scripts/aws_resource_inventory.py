#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import json
from rich.console import Console
from rich.table import Table

# Initialize console for table output
console = Console()

def list_resources(service, operation, region):
    """
    Generic function to list resources for a specific service and operation in a region.
    """
    session = boto3.Session()
    try:
        client = session.client(service, region_name=region)
        # Dynamically call the operation
        response = getattr(client, operation)()
        for key, value in response.items():
            if isinstance(value, list) and value:
                return value  # Return only populated lists
    except ClientError as e:
        console.print(f"[bold red]Error with {service}:{operation} in {region}: {e}[/bold red]")
    except AttributeError:
        console.print(f"[bold yellow]Operation {operation} not found for {service}[/bold yellow]")
    return []


def scan_resources():
    """
    Scan AWS account for specific resources using dynamic service and operation queries.
    """
    # Initialize AWS session and regions
    session = boto3.Session()
    regions = [region["RegionName"] for region in session.client("ec2").describe_regions()["Regions"]]
    console.print(f"[bold cyan]Scanning resources in regions: {', '.join(regions)}[/bold cyan]")

    # Define services and their operations to query
    services_operations = {
        "ec2": ["DescribeVpcs", "DescribeSubnets", "DescribeSecurityGroups"],
        "s3": ["ListBuckets"],
        # Add more services and operations as needed
    }

    # Display services being scanned
    console.print("\n[bold cyan]Services and operations being scanned:[/bold cyan]")
    for service, operations in services_operations.items():
        console.print(f"[bold green]{service}:[/bold green] {', '.join(operations)}")

    all_resources = []

    for region in regions:
        console.print(f"\n[bold green]Scanning region: {region}[/bold green]")
        for service, operations in services_operations.items():
            for operation in operations:
                resources = list_resources(service, operation, region)
                if resources:
                    for resource in resources:
                        all_resources.append({
                            "Region": region,
                            "Service": service,
                            "Operation": operation,
                            "Resource": resource,
                        })

    # Save results to JSON
    if all_resources:
        with open("aws_resources.json", "w") as f:
            json.dump(all_resources, f, indent=4)
        console.print("[bold cyan]Resources saved to aws_resources.json[/bold cyan]")
    else:
        console.print("[bold red]No resources found.[/bold red]")

    # Print results in table format
    print_resources_table(all_resources)


def print_resources_table(resources):
    """
    Print resources in a consolidated table format.
    """
    if not resources:
        console.print("[bold yellow]No resources to display.[/bold yellow]")
        return

    table = Table(title="AWS Resources")
    table.add_column("Region")
    table.add_column("Service")
    table.add_column("Operation")
    table.add_column("Resource")

    for res in resources:
        table.add_row(
            res["Region"],
            res["Service"],
            res["Operation"],
            json.dumps(res["Resource"], indent=2)
        )

    console.print(table)


if __name__ == "__main__":
    scan_resources()

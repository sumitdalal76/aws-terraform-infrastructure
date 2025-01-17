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
    ec2_client = session.client("ec2")

    # Get all AWS regions
    regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
    console.print(f"[bold cyan]Scanning resources for all regions: {', '.join(regions)}[/bold cyan]")

    # Get all available AWS services dynamically
    available_services = session.get_available_services()
    console.print(f"[bold cyan]Scanning for all services: {', '.join(available_services)}[/bold cyan]")

    all_resources = {}

    for region in regions:
        console.print(f"\n[bold green]Scanning region: {region}[/bold green]")

        for service in available_services:
            try:
                client = session.client(service, region_name=region)

                # Discover available operations dynamically
                operations = client.meta.service_model.operation_names
                list_operations = [op for op in operations if op.startswith("list_") or op.startswith("describe_")]

                for operation in list_operations:
                    try:
                        # Call the operation dynamically
                        response = getattr(client, operation)()
                        # Extract the first non-empty key (expected resource list)
                        resources = next(
                            (value for key, value in response.items() if isinstance(value, list) and value), []
                        )

                        if resources:
                            formatted_resources = [
                                {"Region": region, "Service": service, **flatten_dict(resource)}
                                for resource in resources
                            ]
                            all_resources.setdefault(service, []).extend(formatted_resources)

                    except ClientError as e:
                        console.print(f"[bold yellow]No permissions or empty response for {operation} in {service}[/bold yellow]")
                        continue
            except ClientError as e:
                console.print(f"[bold red]Error initializing client for {service} in {region}: {e}[/bold red]")
                continue

    # Print consolidated tables
    for service, items in all_resources.items():
        if items:  # Only print if items exist
            print_table(service.title(), items)

    # Save inventory to JSON
    with open("aws_all_resources.json", "w") as f:
        json.dump(all_resources, f, indent=4)
    console.print("[bold cyan]Inventory saved to aws_all_resources.json[/bold cyan]")

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

if __name__ == "__main__":
    list_all_resources()

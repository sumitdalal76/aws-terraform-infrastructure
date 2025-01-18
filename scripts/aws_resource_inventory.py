import subprocess
from rich.console import Console
from rich.table import Table
import json

# Initialize console for better terminal output
console = Console()

def list_s3_buckets():
    """
    List S3 buckets using AWS CLI
    """
    try:
        # List buckets using AWS CLI
        result = subprocess.run(
            ["aws", "s3", "ls"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create and populate table
        table = Table(title="AWS S3 Buckets")
        table.add_column("Creation Date", style="cyan")
        table.add_column("Bucket Name", style="green")
        
        # Parse and add each bucket to the table
        for line in result.stdout.strip().split('\n'):
            if line:  # Skip empty lines
                date_str, bucket_name = line.strip().split(' ', 1)
                table.add_row(date_str, bucket_name)
        
        # Print the table
        console.print(table)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error listing buckets: {str(e)}[/bold red]")
        raise

def list_vpcs():
    """
    List VPCs using AWS CLI
    """
    try:
        # List VPCs using AWS CLI
        result = subprocess.run(
            ["aws", "ec2", "describe-vpcs", "--output", "text", "--query", "Vpcs[].[VpcId,CidrBlock,State]"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create and populate table
        table = Table(title="AWS VPCs")
        table.add_column("VPC ID", style="cyan")
        table.add_column("CIDR Block", style="green")
        table.add_column("State", style="yellow")
        
        # Parse and add each VPC to the table
        for line in result.stdout.strip().split('\n'):
            if line:  # Skip empty lines
                vpc_id, cidr, state = line.strip().split('\t')
                table.add_row(vpc_id, cidr, state)
        
        # Print the table
        console.print(table)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error listing VPCs: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    console.print("\n[bold cyan]Scanning S3 Buckets...[/bold cyan]")
    list_s3_buckets()
    
    console.print("\n[bold cyan]Scanning VPCs...[/bold cyan]")
    list_vpcs()

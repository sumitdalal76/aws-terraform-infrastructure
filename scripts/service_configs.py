# List of services to scan
SERVICES_TO_SCAN = ['s3', 'vpc']

# Service configurations dictionary
SERVICE_CONFIGS = {
    's3': {
        'title': 'S3 Buckets',
        'regional': False,
        'columns': ['Creation Date', 'Bucket Name'],
        'command': lambda: ["aws", "s3", "ls"]
    },
    'vpc': {
        'title': 'VPCs',
        'regional': True,
        'columns': ['Region', 'VPC ID', 'CIDR Block', 'State', 'DHCP Options'],
        'command': lambda region: [
            "aws", "ec2", "describe-vpcs",
            "--region", region,
            "--filters", "Name=is-default,Values=false",
            "--query", "Vpcs[].[VpcId,CidrBlock,State,DhcpOptionsId]",
            "--output", "text"
        ]
    }
}
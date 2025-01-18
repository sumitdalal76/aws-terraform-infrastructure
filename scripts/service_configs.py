# List of services to scan
SERVICES_TO_SCAN = ['s3', 'vpc']

# Service configurations dictionary
SERVICE_CONFIGS = {
    's3': {
        'title': 'S3 Buckets',
        'regional': False,
        'columns': [
            {'header': 'Creation Date', 'style': 'cyan'},
            {'header': 'Bucket Name', 'style': 'green'}
        ],
        'command': lambda: ["aws", "s3", "ls"]
    },
    'vpc': {
        'title': 'VPCs',
        'regional': True,
        'columns': [
            {'header': 'Region', 'style': 'blue'},
            {'header': 'VPC ID', 'style': 'cyan'},
            {'header': 'CIDR Block', 'style': 'green'},
            {'header': 'State', 'style': 'yellow'}
        ],
        'command': lambda region: [
            "aws", "ec2", "describe-vpcs",
            "--region", region,
            "--output", "text",
            "--query", "Vpcs[?IsDefault==`false`].[VpcId,CidrBlock,State]"
        ]
    }
    # Add more services here
}
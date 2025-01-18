import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
import time
from typing import Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure boto3 with retries
boto3_config = Config(
    retries = dict(
        max_attempts = 3,
        mode = 'adaptive'
    ),
    connect_timeout = 10,
    read_timeout = 30
)

def make_api_call(func: Callable, *args, **kwargs) -> Any:
    """Generic method to make AWS API calls with retry logic."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            if e.response['Error']['Code'] in ['RequestLimitExceeded', 'Throttling']:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for API call: {e}")
                    return None
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"API throttling, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"API call failed: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            return None

def get_aws_regions(session: boto3.Session) -> list:
    """Get list of all AWS regions."""
    try:
        ec2 = session.client('ec2', config=boto3_config)
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return regions
    except ClientError as e:
        logger.error(f"Error getting regions: {e}")
        return [] 
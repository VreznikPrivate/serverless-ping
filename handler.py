import json
import os
import time
import boto3
import logging
import sys
import socket
import re


# get this file's directory independent of where it's run from
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "vendored"))

#import requests  # noqa
#from raven.contrib.awslambda import LambdaClient  # noqa

#raven_client = LambdaClient()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

boto_client = None


def current_time_in_seconds():
    return time.time()


def response_with_message(message):
    logger.info(message)
    return {"statusCode": 200, "body": json.dumps({"message": message})}


def publish_elapsed_time_for_host(elapsed_time, host):
    global boto_client
    if not boto_client:
        boto_client = boto3.client('cloudwatch')

    boto_client.put_metric_data(
        Namespace=os.environ.get('PING_ALARM_NAMESPACE'),
        MetricData=[
            {
                'MetricName': os.environ.get('PING_METRIC_NAME'),
                'Dimensions': [
                    {
                        'Name': 'Host',
                        'Value': host
                    },
                ],
                'Value': elapsed_time,
                'Unit': 'Seconds'
            },
        ]
    )


def pingtest(event, context):
    ping_host = os.environ.get('PING_HOST')
    ping_port = os.environ.get('PING_PORT')
    start = current_time_in_seconds()
    
    s = socket.socket()
    s.settimeout(1)

    msg = "Attempting to connect to "  + ping_host +  " on port " +  ping_port
    logger.info(msg)
    try:
        s.connect((ping_host, 40443))
        logger.info("Success")
        elapsed_time = current_time_in_seconds() - start
        publish_elapsed_time_for_host(elapsed_time, ping_host)
        return response_with_message("Pinged: {} Duration: {}".format(ping_host, elapsed_time))
    except socket.error:
        logger.info("Failed")
        #logger.info(e)
        publish_elapsed_time_for_host(0, ping_host)
        return response_with_message("Checked failed for {}, {}".format(ping_host))
    finally:
        s.close()    

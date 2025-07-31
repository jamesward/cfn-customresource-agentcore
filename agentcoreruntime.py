from typing import Optional

from crhelper import CfnResource
import logging
import boto3

logger = logging.getLogger(__name__)

helper = CfnResource(json_logging=False, log_level='DEBUG', boto_level='CRITICAL', sleep_on_delete=120, ssl_verify=None)

client = boto3.client('bedrock-agentcore-control')

def find_agent_runtime_id(target_arn) -> Optional[str]:
    agent_runtimes = client.list_agent_runtimes()
    print(agent_runtimes)

    agent_runtimes = agent_runtimes.get('agentRuntimes', [])

    matching_runtime = next(
        (runtime for runtime in agent_runtimes
         if runtime['agentRuntimeArn'] == target_arn),
        None
    )

    return matching_runtime['agentRuntimeId']

@helper.create
def create(event, context):
    logger.info(f"Received event: {event}")

    name = event['LogicalResourceId']
    container_uri = event['ResourceProperties']['ContainerUri']
    role_arn = event['ResourceProperties']['RoleArn']
    server_protocol = event['ResourceProperties']['ServerProtocol']

    response = client.create_agent_runtime(
        agentRuntimeName=name,
        agentRuntimeArtifact={
            'containerConfiguration': {
                'containerUri': container_uri
            }
        },
        protocolConfiguration={
            'serverProtocol': server_protocol
        },
        networkConfiguration={
            "networkMode":"PUBLIC"
        },
        roleArn=role_arn
    )

    print(response)

    # todo: use status

    # {
    #     'agentRuntimeArn': 'string',
    #     'workloadIdentityDetails': {
    #         'workloadIdentityArn': 'string'
    #     },
    #     'agentRuntimeId': 'string',
    #     'agentRuntimeVersion': 'string',
    #     'createdAt': datetime(2015, 1, 1),
    #     'status': 'CREATING'|'CREATE_FAILED'|'UPDATING'|'UPDATE_FAILED'|'READY'|'DELETING'
    # }

    return response['agentRuntimeArn']

@helper.update
def update(event, context):
    logger.info(f"Received event: {event}")

    resource_id = event['PhysicalResourceId']

    maybe_agent_runtime_id = find_agent_runtime_id(resource_id)

    if maybe_agent_runtime_id is None:
        raise Exception(f"Could not find agent runtime with id {resource_id}")
    else:
        container_uri = event['ResourceProperties']['ContainerUri']
        role_arn = event['ResourceProperties']['RoleArn']
        server_protocol = event['ResourceProperties']['ServerProtocol']

        response = client.update_agent_runtime(
            agentRuntimeId=maybe_agent_runtime_id,
            agentRuntimeArtifact={
                'containerConfiguration': {
                    'containerUri': container_uri
                }
            },
            roleArn=role_arn,
            networkConfiguration={
                'networkMode': 'PUBLIC'
            },
            protocolConfiguration={
                'serverProtocol': server_protocol
            },
        )

        print(response)

        # todo: use status

        return response['agentRuntimeArn']

@helper.delete
def delete(event, context):
    logger.info(f"Received event: {event}")

    resource_id = event['PhysicalResourceId']

    maybe_agent_runtime_id = find_agent_runtime_id(resource_id)

    if maybe_agent_runtime_id is None:
        raise Exception(f"Could not find agent runtime with id {resource_id}")
    else:
        client.delete_agent_runtime(agentRuntimeId=maybe_agent_runtime_id)

        # todo: handle status
        # 'status': 'CREATING'|'CREATE_FAILED'|'UPDATING'|'UPDATE_FAILED'|'READY'|'DELETING'


def handler(event, context):
    helper(event, context)

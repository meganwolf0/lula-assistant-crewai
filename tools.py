from kubernetes import client, config
from langchain.tools import tool
import json
import subprocess
import sys
import base64


@tool
def get_cluster_resources() -> str:
    """ A generic tool to extract all api resources from a Kubernetes cluster as string json"""
    config.load_kube_config()

    command = r"""
    kubectl api-resources | awk 'NR>1 {if (NF==5) print $1","$2","$3","$4","$5; else if (NF==4) print $1",,"$2","$3","$4}' | jq -R -s -c 'split("\n") | 
    map(select(length > 0) | split(",") | {resource: .[0], shortNames: .[1], apiGroup: .[2], namespaced: .[3], kind: .[4]})'
    """

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl command: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON output: {e.msg}", file=sys.stderr)
        sys.exit(1)


@tool
def get_named_resources(input_str: str) -> str:
    """ A generic tool to extract named resources from a Kubernetes cluster based on input parameters 
    
    The input string should be formatted as 'resource_type,namespace_scoped' where namespace_scoped is 
    either "true" or "false".
    
    Example inputs: 'nodes,false', 'pods,true', 'deployments,true'"""
    config.load_kube_config()

    resource_type, namespace_scoped = input_str.split(',')

    if namespace_scoped == "true":
        command = r"""kubectl get %s --all-namespaces -o json | jq '[.items[] | {name: .metadata.name, namespace: .metadata.namespace}]'""" % resource_type
    elif namespace_scoped == "false":
        command = r"""kubectl get %s -o json | jq '[.items[] | {name: .metadata.name}]'""" % resource_type
    else:
        return f"Could not interpret namespace_scoped value: {namespace_scoped}"

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing kubectl command for {resource_type}: {e.stderr}"

@tool
def get_resource(input_str: str) -> str:
    """ A generic tool to extract a single named resource from a Kubernetes cluster based on input parameters 
    
    The input string should be formatted as 'resource_type,resource_name,namespace'. For cluster-scoped resources
    the namespace should be "none".
    
    Example inputs: 'node,agent-1,none', 'pods,test-pod,default'"""
    config.load_kube_config()

    resource_type, resource_name, namespace = input_str.split(',')

    if namespace == "none":
        command = f"kubectl get {resource_type} {resource_name} -o json"
    else:
        command = f"kubectl get {resource_type} {resource_name} -n {namespace} -o json"

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing kubectl command for {resource_type} named {resource_name} in namespace {namespace}: {e.stderr}"


@tool
def base64_decode(input_str: str) -> str:
    """ A generic tool to decode a base64 encoded string """
    try:
        decoded_str = base64.b64decode(input_str).decode('utf-8')
        return decoded_str
    except base64.binascii.Error as e:
        return "Error: Input string is not valid base64 encoded text."
    except UnicodeDecodeError as e:
        return "Error: Decoded text could not be converted to UTF-8."

# @tool
# def opa_eval(json_data: str) -> str:
#     """ A generic tool to evaluate a given data input against a given Rego policy """
#     json_py = json.loads(json_data)
#     # data, policy = input_str.split(',')
#     data = json_py['data']
#     policy = json_py['policy']

#     command = f"echo '{data}' | opa eval -i -d - -p '{policy}'"

#     try:
#         result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         return result.stdout
#     except subprocess.CalledProcessError as e:
#         return f"Error executing opa eval command: {e.stderr}"
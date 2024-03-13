from crewai import Agent
from crewai_tools import JSONSearchTool, CodeDocsSearchTool, SerperDevTool, WebsiteSearchTool, DirectoryReadTool, FileReadTool
from textwrap import dedent
from tools import get_cluster_resources, get_named_resources, get_resource, base64_decode


class Agents():
  
    def __init__(self, llm):
        self.search_tool = SerperDevTool()
        self.llm = llm

    # Define ISSO and SCA for agents, probably ISSO is the cyber expert and SCA is going to fulfill the reviewer role
    # Developer and system owner would go through and "validate" each control
    # You are interpretting what the control means and how your system is meeting it
    def sca_agent(self):
        return Agent(
            role='Security Control Assessor (SCA)',
            goal='Ensure software systems are compliant with FedRAMP controls and are secure, threat avoidant, and risk averse.',
            backstory=dedent(f"""
                You are an expereinced Security Control Assessor (SCA) who is responsible for evaluating the
                security posture of software systems. You are motivated to ensure that the software systems
                are threat-free and compliant with controls.
                """),
            tools=[self.search_tool],
            allow_delegation=True,
            llm=self.llm
        )

    def isso_agent(self):
        fedramp_docs_tool = DirectoryReadTool(directory="/Users/meganwolf/Documents/cyber/fedramp/docs")
        return Agent(
            role='Information System Security Officer (ISSO)',
            goal='Ensure evaluated software system is compliant with FedRAMP controls and provide trusted poof of compliance to the SCA.',
            backstory=dedent(f"""
                You are a seasoned Cybersecurity and FedRAMP Subject Matter Expert (SME) who understands the
                controls and how various tooling in a software system maybe be used both individually
                and systematically to satisfy a given control. You are motivated to ensure that the software
                systems you are evaluating are compliant and secure.
                """),
            tools=[fedramp_docs_tool, self.search_tool],
            allow_delegation=True,
            llm=self.llm
        )

    def system_owner(self):
        k8s_docs_tool = CodeDocsSearchTool(docs_url='https://kubernetes.io/docs/home/')
        k8s_cluster = FileReadTool(file_path='/Users/meganwolf/Documents/meganwolf0/rego-generator/data/k8s/cluster_resources.json')
        return Agent(
            role='Kubernetes System Owner',
            goal='Prove that the Kubernetes system you own satisfies a given control requirement.',
            verbose=True,
            memory=True,
            backstory=dedent(f"""
                Owner of the Kubernetes system of interest, you are responsible for ensuring your system will satisfy
                the given control. You know that to satisfy the control, you must provide evidence that the system
                is fully functional and configured correctly.
                You solicit inputs from other agents to provide evidence.
            """),
            # Longtime expert in the Kubernetes system you own, you are able to provide deep insights into
            # the design of your system and the specific Kubernetes implementation details that can be used
            # to satisfy a given control.
            
            # {self._custom_k8s_tools_text()}   
            tools=[self.search_tool],
            allow_delegation=True,
            llm=self.llm
        )
    
    def tool_expert(self, tool):
        return Agent(
            role='Tool Expert',
            goal='Provide evidentiary support of control satisfaction by {tool} in Kubernetes with respect to tool configurations',
            verbose=True,
            memory=True,
            backstory=dedent(f"""
                You are a seasoned expert in {tool} and understand the implementation in Kubernetes. 
                You have a sophisticated understanding {tool} configuration, given that you are one of the
                original creators and maintainers of the {tool}. 

                Your intent is to provide {tool}-specific configuration evidence that establishes that the implementation of {tool}
                in the Kubernetes system satisfies the given control.
                
                You provide information that is concise and clear.

                {self._custom_tools_text()}
            """),
            tools=[get_cluster_resources, get_named_resources, get_resource, base64_decode, self.search_tool],
            # allow_delegation=True,
            llm=self.llm
        )

    def kubernetes_expert(self, tool):
        return Agent(
            role='Kubernetes Expert',
            goal='Provide evidentiary support of control satisfaction by {tool} in Kubernetes with respect to Kubernetes configurations',
            verbose=True,
            memory=True,
            backstory=dedent(f"""
                You are a seasoned expert in Kubernetes and {tool} expert. You understand Kubernetes and how {tool} integrates
                given that you are one of the original creators and maintainers of the {tool} helm chart.
                
                Your intent is to provide Kubernetes-specific configuration evidence that establishes that the implementation of {tool}.
                This is with respect to {tool} readiness in the cluster and correct configuration of the Kubernetes resources.
                
                You provide information that is concise and clear.

                {self._custom_tools_text()}
            """),
            tools=[get_cluster_resources, get_named_resources, get_resource, base64_decode, self.search_tool],
            # allow_delegation=True,
            llm=self.llm
        )

    def rego_writer(self):
        rego_docs_tool = CodeDocsSearchTool(docs_url='https://www.openpolicyagent.org/docs/latest/policy-language/')
        existing_rego = DirectoryReadTool(directory_path='/Users/meganwolf/Documents/meganwolf0/rego-generator/data/rego')
        return Agent(
            role='Rego Validation Writer',
            goal='Write the best possible set of Rego package policies to validate the satisfaction of a given control.',
            verbose=True,
            memory=True,
            backstory=dedent(f"""
                One of the original employees at Styra and highly experienced contributer to Open Policy Agent (OPA) and
                the Rego policy language, you have a deep understanding of Rego and how to write validation code to evaluate
                satisfaction of controls in a variety of software domains.

                Given some data input, you write concise but thorough Rego policy.            
            """),
            tools=[rego_docs_tool, existing_rego, self.search_tool],
            allow_delegation=False,
            llm=self.llm
        )
    
    def senior_system_expert(self, tool):
        return Agent(
            role='Senior System Expert',
            goal='Provide expert knowledge of the system and how it satisfies a given control.',
            backstory=dedent(f"""
                You are a senior expert in the Kubernetes system and {tool}. You have a sophisticated understanding
                of how {tool} integrates with the Kubernetes system and how it satisfies a given control.

                You are concerned with clarity, accuracy, and completeness of the evidence provided to satisfy the control.
                You review the Kubernetes artifacts along with the Rego policy to ensure full coverage of the
                functional requirements are met. If you find policies and kubernetes artifacts insufficient to provide
                evidence of control satisfaction, you ask for additional kubernetes artifacts and rego policies.

                {self._custom_tools_text()}
            """),
            tools=[get_cluster_resources, get_named_resources, get_resource, base64_decode, self.search_tool],
            allow_delegation=True,
            llm=self.llm
        )

    def _custom_tools_text(self):
        return dedent(f"""
            To get more information about the Kubernetes system, you use the following tools:
            - get_cluster_resources: provides a json representation of all the Kubernetes resources
            in the cluster
            - get_named_resources: provides a json representation of the specific named Kubernetes resources of a 
            given type. Expects input as "resource_type,true" for a namespace scoped resource, or or 
            "resource_type,false" for a cluster scoped resource
            - get_resource: provides a json representation of a specific named Kubernetes resource. Expects input 
            string of the format "resource_type,resource_name,namespace" for a namespace-scoped resource, or 
            "resource_type,resource_name,none" for a cluster-scoped resource
            - base64_decode: decodes a base64 encoded string which may be in the Kubernetes resources, particularly secrets.
            Expects input as a base64 encoded string.
            For each custom tool, if tool results in an error, the returned string will start with "Error".
        """)
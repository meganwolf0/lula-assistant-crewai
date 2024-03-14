from crewai import Task
from textwrap import dedent

class Tasks():
    def __init__(self, tool):
        self.tool = tool

    def get_all_relevant_controls(self, agent):
        return Task(
            name="get_all_relevant_controls",
            description=dedent(f"""
                Extract a list of all the FedRAMP High controls from the provided documentation in data/fedramp/docs.
                Generate a list of the subest of controls that could be satisfied or partially satisfied by the {self.tool}.
                Consult with other agents as needed to better understand the system and the implementation of {self.tool}.
                """),
            expected_output=dedent(f"""
                A list of all relevant controls that are satisfied or partially satisfied by the {self.tool}, along with some
                jutification for why the control is relevant to the {self.tool}.
                """),
            agent=agent
        )

    def break_down_control(self, agent, control):
        return Task(
            name="break_down_control",
            description=dedent(f"""
                Given the following control: {control}
                Use the knowledge of your system and {self.tool} to determine how the capabilities 
                of {self.tool} operating in the system can be used to partially or fully satisfy the control.
                Consult other agents as needed to understand the control and the {self.tool}.
                Break out the control into specific functional requirements that can be evaluated
                using artifacts of the Kubernetes system specific to the {self.tool} implementation there.
                """),
            expected_output=dedent(f"""
                Concise functional requirements that can be evaluated by examining Kubernetes resources.
                """),
            agent=agent
        )
    
    def generate_evidentiary_support(self, context_tasks, agent, previous_task, check_type):
        return Task(
            name="generate_evidentiary_support",
            description=dedent(f"""
                Given the functional requirements for the control found in {previous_task}, extract data from Kubernetes
                resources that implement {self.tool} and specifically with respect to the {check_type} of {self.tool} in the cluster.

                You should prove {self._evidence_text(check_type)}

                Check with human on completeness of resources extracted.

                For the Kubernetes resources extracted, write one or many rego validation policies, to be evaluated in an Open Policy 
                Agent (OPA) server that inputs one or many of these resources and outputs a boolean value indicating whether the 
                resource satisfies the functional requirement.
                
                Be thorough when writing the policies, but break them down so that discrete functionality is checked in each package. 
                Prioritize creating many concise policies.
                Use the sample.md file in the data/rego directory as a reference for how the OPA inputs rego policy should be structured.
                """),

            # The sets of resoures you extract should provide some data to determine that {self.tool} is functional with respect to
            # it's {check_type} in the cluster. Prioritize the highlest level Kubernetes orchestration artifacts, such as deployments, 
            # daemonsets, statefulsets, replicasets for the workloads, and the services that expose the workloads.
            # Brevity of data is not a concern, but completeness is.
            # Criteria for satisfaction:
            #     - {self.tool} is healthy in the cluster, the workloads should be running and ready
            #     - {self.tool} is fully functional in the cluster, the workloads should be able to perform their intended functions
            #     - {self.tool} has the correct configuration to perform it's specific tasks which satisfy the control
            expected_output=dedent(f"""
                One or many rego policy packages that can be used in Open Policy Agent to prove {self._evidence_text(check_type)}. 
                For each package output:
                - description of the expected input data
                - description of the purpose of the particular policy - particularly which system function is it intending to validate
                - rego policy with "package validation" header and returned "validation" variable of boolean type
                Each of these outputs are termed as "evidentiary support" for the control satisfaction.
                """),
            agent=agent,
            context=context_tasks
        )

    def extract_k8s_support(self, agent):
        return Task(
            name="extract_k8s_support",
            description=dedent(f"""
                Using the functional requirements from the previous task, extract all data about the Kubernetes
                cluster and the specific resources used by {self.tool} that can be used as support for proof
                that {self.tool} is capable of satisfying the requirements.

                The sets of resoures you extract should provide some data to determine that {self.tool} is fully 
                functional in the cluster. It should also provide evidence of the configuration of {self.tool} in the cluster.
                Brevity of data is not a concern, but completeness is.

                Return all relevant Kubernetes support data found that can help evaluate these points.
                """),
            expected_output=dedent(f"""
                Each requirement, along with the json representation of the artifacts that may be 
                evaluated to satisfy the requirement.
                """),
            agent=agent
        )

    def write_rego_validation(self, agent):
        return Task(
            name="write_rego_validation",
            description=dedent(f"""
                Given Kubernetes system artifacts that pertain to the ability of {self.tool} to perform specific functions,
                write one or many rego policy packages, to be evaluated in an Open Policy Agent (OPA) server, that help determine whether the control 
                is satisfied by {self.tool}. Criteria for satisfaction:
                - {self.tool} is healthy in the cluster, the workloads should be running and ready
                - {self.tool} is fully functional in the cluster, the workloads should be able to perform their intended functions
                - {self.tool} has the correct configuration to perform it's specific tasks which satisfy the control
                Be thorough when writing the policies, but break them down so that discrete functionality is checked in each package. 
                Prioritize creating many concise policies.
                The package input data will be any Kubernetes json artifacts needed, which could include the resource specification, configuration data, 
                or other relevant cluster outputs. The input data is of type JSON.
                The policy should be "package validation" and should provie a "validation" value that is true or false.
                The policy is most useful if it also provided other outputs that could be used to help diagnose the cause of unsatisfied functions.
                Use the sample.md file in the data/rego directory as a reference for how the OPA inputs rego policy should be structured.
                """),
            expected_output=dedent(f"""
                One or many rego policy packages that can be used in Open Policy Agent. For each package output:
                - description of the expected input data
                - description of the purpose of the particular policy - particularly which system function is it intending to validate
                - rego policy with "package validation" header and "validation" variable that returns true or false
                Each of these outputs are termed as "evidence" for the control satisfaction
                """),
            agent=agent
        )
    
    def review_evidence(self, context_tasks, agent, control, tasks):
        return Task(
            name="review_evidence",
            description=dedent(f"""
                Given the following control text: {control}
                And the provided evidence that the control is being met by {self.tool} in the Kubernetes cluster, i.e.,
                the input and rego policy packages from the preceeding tasks: {tasks}
                
                Evaluate if the evidence is sufficient in terms of completeness and correctness to satisfy the control.

                Clean up the policies such that there is no redundancy and the policies are concise, clear, and consisent.
                """),
            expected_output=dedent(f"""
                List of refined evidentiary support that is non-redudant, concise, clear, and consistent.
                Each item in the list should have:
                - description of the expected input data
                - description of the purpose of the particular policy - particularly which system function is it intending to validate
                - rego policy with "package validation" header and "validation" variable that returns true or false
                """),
            agent=agent,
            context=context_tasks
        )
    
    def _evidence_text(self, type) -> str:
        text = ""
        if type == "healthiness":
            text = dedent(f"""
                {self.tool} is healthy in the cluster and the workloads should be running, ready, and instrumented correctly. 
                Prioritize writing policies against the the highlest level Kubernetes resources, such as deployments, 
                daemonsets, statefulsets, replicasets to determine the readiness and state of the workloads.
                """)
        elif type == "functionality":
            text = dedent(f"""
                {self.tool} is fully functional in the cluster and the workloads are configured to perform their intended functions. 
                Prioritize the configuration of the workloads and the services that expose the workloads.
                """)
        elif type == "configuration":
            text = dedent(f"""
                {self.tool} has the correct tool-specific configuration to perform it's specific tasks which satisfy the control. 
                Prioritize the tool-specific configuration data, typically in the form of environment variables, configmap data, or
                secret data.
                """)
        return text
            
    def _tasks_str(self, tasks):
        return ", ".join([task for task in tasks])
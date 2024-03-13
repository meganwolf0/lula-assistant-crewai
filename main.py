from crewai import Crew
from textwrap import dedent
from agents import Agents
from tasks import Tasks

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4-0125-preview")

from dotenv import load_dotenv
load_dotenv()

class LulaCrew:
  def __init__(self):
     self.agents = Agents(llm)

  def run_rego_gen(self, tool, control):
    # Agents for crew's tasks
    # isso_agent = self.agents.isso_agent()
    system_owner = self.agents.system_owner()
    tool_expert = self.agents.tool_expert(tool)
    kubernetes_expert = self.agents.kubernetes_expert(tool)
    # rego_writer = self.agents.rego_writer()
    senior_system_expert = self.agents.senior_system_expert(tool)

    # Tasks for the crew
    tasks = Tasks(tool)

    break_down_control = tasks.break_down_control(system_owner, control)
    # generate_healthiness_evidence = tasks.generate_evidentiary_support(tool_expert, "break_down_control", "healthiness")
    # generate_functionality_evidence = tasks.generate_evidentiary_support(tool_expert, "break_down_control", "functionality")
    # generate_configuration_evidence = tasks.generate_evidentiary_support(tool_expert, "break_down_control", "configuration")
    # evidence_tasks =["generate_healthiness_evidence", "generate_functionality_evidence", "generate_configuration_evidence"]
    generate_kubernetes_config_evidence = tasks.generate_evidentiary_support([break_down_control], kubernetes_expert, "break_down_control", "healthiness")
    generate_tool_config_evidence = tasks.generate_evidentiary_support([break_down_control], tool_expert, "break_down_control", "configuration")
    evidence_tasks =["generate_kubernetes_config_evidence", "generate_tool_config_evidence"]
    # extract_k8s_support = tasks.extract_k8s_support(tool_expert)
    # write_rego_validation = tasks.write_rego_validation(rego_writer)
    review_evidence = tasks.review_evidence([generate_kubernetes_config_evidence, generate_tool_config_evidence], senior_system_expert, control, evidence_tasks)

    crew = Crew(
      agents=[
        system_owner,
        tool_expert,
        senior_system_expert
      ],
      tasks=[
        break_down_control,
        generate_kubernetes_config_evidence,
        generate_tool_config_evidence,
        review_evidence
      ],
      verbose=True
    )

    result = crew.kickoff()
    return result

  def run_control_allocation(self, tool):
    """ Allocate controls for a given tool running in a given system."""
    # Agents for crew's tasks
    isso_agent = self.agents.isso_agent()
    system_owner = self.agents.system_owner()
    tool_expert = self.agents.tool_expert(tool)
    # rego_writer = self.agents.rego_writer()
    # senior_system_expert = self.agents.senior_system_expert(tool)

    # Tasks for the crew
    tasks = Tasks(tool)

    get_all_relevant_controls = tasks.get_all_relevant_controls(system_owner)
    # extract_k8s_support = tasks.extract_k8s_support(tool_expert)
    # write_rego_validation = tasks.write_rego_validation(rego_writer)
    # review_evidence = tasks.review_evidence(senior_system_expert, control, evidence_tasks)

    crew = Crew(
      agents=[
        isso_agent,
        system_owner,
        tool_expert,
        # rego_writer,
        # senior_system_expert
      ],
      tasks=[
        get_all_relevant_controls,
      ],
      verbose=True
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    lula_crew = LulaCrew()
    
    # TO DO: Add prompt for the user to input the tool name
    toolName = "promtail"

    # TO DO: Add a prompt for the user to input the control text
    controlText = dedent(f"""
        An event is any observable occurrence in an organizational information system. 
        Organizations identify audit events as those events which are significant and relevant to the security of information systems and the environments in which those systems operate in order to meet specific and ongoing audit needs. 
        Audit events can include, for example, password changes, failed logons, or failed accesses related to information systems, administrative privilege usage, PIV credential usage, or third-party credential usage. 
        In determining the set of auditable events, organizations consider the auditing appropriate for each of the security controls to be implemented. 
        To balance auditing requirements with other information system needs, this control also requires identifying that subset of auditable events that are audited at a given point in time.
        """)
    
    # TO DO: Add prompt for the user to input the system name (currently unused)
    systemName = "Platform One Big Bang on Kubernetes"

    # Control evidence thread:
    print("## Welcome to Lula Assistant Crew")
    print('-------------------------------')
    
    result = lula_crew.run_rego_gen(toolName, controlText)

    print(result)

    # Control -> tool allocation thread:
    # print("## Welcome to Control Mapping Crew")
    # print('-------------------------------')

    # result = lula_crew.run_control_allocation(toolName)

    # print(result)

# Lula Assistant - CrewAI
An Assistant to aid in the creation of Lula Validation Artifacts using CrewAI

## Getting Started
**Requirements**
- Running Kubernetes cluster of interest in current context
- The following Environment Variables (can add .env to directory and script will read):
    - SERPER_API_KEY=key
    - OPENAI_API_KEY=key
        - Note: You will need to have a billing account set-up

**Run**

To run the script
```bash
poetry run python main.py
```

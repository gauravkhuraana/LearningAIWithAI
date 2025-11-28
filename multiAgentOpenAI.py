import os
import warnings
from dotenv import load_dotenv
from openai import AzureOpenAI

# Suppress deprecation warnings for Assistants API
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Clear the console
os.system('cls' if os.name=='nt' else 'clear')

# Load environment variables from .env file
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Create specialized assistants
print("Creating specialized assistants...")

priority_assistant = client.beta.assistants.create(
    name="priority_agent",
    instructions="""
Assess how urgent a ticket is based on its description.

Respond with one of the following levels:
- High: User-facing or blocking issues
- Medium: Time-sensitive but not breaking anything
- Low: Cosmetic or non-urgent tasks

Only output the urgency level and a very brief explanation.
""",
    model=deployment_name
)

team_assistant = client.beta.assistants.create(
    name="team_agent",
    instructions="""
Decide which team should own each ticket.

Choose from the following teams:
- Frontend
- Backend
- Infrastructure
- Marketing

Base your answer on the content of the ticket. Respond with the team name and a very brief explanation.
""",
    model=deployment_name
)

effort_assistant = client.beta.assistants.create(
    name="effort_agent",
    instructions="""
Estimate how much work each ticket will require.

Use the following scale:
- Small: Can be completed in a day
- Medium: 2-3 days of work
- Large: Multi-day or cross-team effort

Base your estimate on the complexity implied by the ticket. Respond with the effort level and a brief justification.
""",
    model=deployment_name
)

# Create a thread
print("Creating thread...")
thread = client.beta.threads.create()

# Get user input
prompt = input("\nWhat's the support problem you need to resolve?: ")

# Add user message to thread
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=prompt
)

print("\nProcessing ticket through agents. Please wait...\n")

# Run each assistant and collect results
results = {}

# Priority assessment
print("Assessing priority...")
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=priority_assistant.id
)

if run.status == "completed":
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    results["priority"] = messages.data[0].content[0].text.value
else:
    results["priority"] = f"Failed: {run.status}"

# Team assignment
print("Determining team assignment...")
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=team_assistant.id
)

if run.status == "completed":
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    results["team"] = messages.data[0].content[0].text.value
else:
    results["team"] = f"Failed: {run.status}"

# Effort estimation
print("Estimating effort...")
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=effort_assistant.id
)

if run.status == "completed":
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    results["effort"] = messages.data[0].content[0].text.value
else:
    results["effort"] = f"Failed: {run.status}"

# Display results
print("\n" + "="*60)
print("TICKET TRIAGE RESULTS")
print("="*60)
print(f"\nOriginal Ticket:\n{prompt}\n")
print(f"Priority Assessment:\n{results['priority']}\n")
print(f"Team Assignment:\n{results['team']}\n")
print(f"Effort Estimation:\n{results['effort']}\n")
print("="*60)

# Clean up
print("\nCleaning up assistants...")
client.beta.assistants.delete(priority_assistant.id)
print("Deleted priority assistant.")
client.beta.assistants.delete(team_assistant.id)
print("Deleted team assistant.")
client.beta.assistants.delete(effort_assistant.id)
print("Deleted effort assistant.")
print("\nDone!")

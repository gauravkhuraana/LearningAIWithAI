"""
🎯 THE SIMPLEST WAY: GitHub Copilot Extension API

You want to send a prompt and have everything handled automatically?
That's EXACTLY what VS Code Copilot does!

Here's the reality:
"""

# ============================================================
# OPTION A: Use VS Code Copilot (EASIEST - No code needed!)
# ============================================================
"""
Just open VS Code Chat and type:

    "Create test cases for Epic #3 in project SharingIsCaring"

Done! Copilot + MCP handles everything.

This is what you already did and it worked perfectly!
"""


# ============================================================
# OPTION B: Use GitHub Copilot CLI (Simple command line)
# ============================================================
"""
Install GitHub CLI with Copilot extension:
    
    winget install GitHub.cli
    gh extension install github/gh-copilot

Then just run:

    gh copilot suggest "Create test cases for Azure DevOps Epic #3"

"""


# ============================================================
# OPTION C: Use Semantic Kernel (Microsoft's AI Framework)
# ============================================================
"""
This is the "proper" way to do what you want programmatically.
Semantic Kernel connects AI models with tools (like MCP) seamlessly.
"""

# pip install semantic-kernel azure-identity mcp

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_test_cases_with_ai(prompt: str, ado_plugin=None):
    """
    The architecture you want:
    
    Your Prompt → AI Model → MCP Tools → Azure DevOps → Results
    
    This is exactly what Copilot does internally!
    """
    
    # 1. Create kernel (the AI orchestrator)
    kernel = Kernel()
    
    # 2. Add AI service
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not endpoint or not api_key:
        raise ValueError("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file")
    
    kernel.add_service(AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key
    ))
    
    # 3. Add MCP tools as plugins (reuse existing connection if provided)
    if ado_plugin is None:
        print("   🔌 Connecting to Azure DevOps MCP server...")
        ado_plugin = MCPStdioPlugin(
            name="azure_devops",
            command="npx",
            args=["-y", "@azure-devops/mcp@next", os.getenv("AZURE_DEVOPS_ORG", "GauravKhurana0262")],
            description="Azure DevOps work item management",
            kernel=kernel
        )
        await ado_plugin.connect()
        
        # List available tools
        plugin_names = list(kernel.plugins.keys())
        print(f"   ✅ Connected! Loaded plugins: {plugin_names}")
        
        # Get the plugin and check its functions
        if "azure_devops" in kernel.plugins:
            ado_plugin_obj = kernel.plugins["azure_devops"]
            functions = list(ado_plugin_obj.functions.keys())
            print(f"   📦 Available Azure DevOps tools: {len(functions)}")
            if len(functions) > 0:
                print(f"      Tools: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
    
    kernel.add_plugin(ado_plugin)
    
    # 4. Create execution settings to enable function calling
    from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
    from semantic_kernel.contents import ChatHistory
    
    execution_settings = kernel.get_service().get_prompt_execution_settings_class()(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    # 5. Use chat completion with automatic function calling
    chat_history = ChatHistory()
    chat_history.add_system_message(
        "You are an Azure DevOps assistant. "
        "IMPORTANT: You MUST use the available Azure DevOps tools to fetch real data. "
        "DO NOT make assumptions or generate fake data. "
        "If you cannot find the work item, say so explicitly."
    )
    chat_history.add_user_message(prompt)
    
    result = await kernel.get_service().get_chat_message_contents(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=kernel
    )
    
    return result[0].content if result else "No response", ado_plugin


# ============================================================  
# OPTION D: The Reality Check
# ============================================================
"""
Here's the truth about what's happening:

┌─────────────────────────────────────────────────────────────┐
│                      VS CODE COPILOT                        │
│                                                             │
│   Your Prompt ──→ Claude/GPT ──→ Tool Decisions            │
│                        │                                    │
│                        ▼                                    │
│              MCP Server (Tool Executor)                     │
│                        │                                    │
│                        ▼                                    │
│                 Azure DevOps API                            │
│                        │                                    │
│                        ▼                                    │
│                    Results                                  │
└─────────────────────────────────────────────────────────────┘

The MCP server is JUST the tool executor.
The AI (Claude/GPT) is the brain that decides what to do.

When you use Copilot in VS Code, you get BOTH:
- The AI brain (Claude/GPT)  
- The MCP tool executor

If you want this in your own code, you need BOTH pieces!
"""


# ============================================================
# OPTION E: Simple REST approach (if you just want automation)
# ============================================================
"""
If you don't need AI to interpret prompts, and you just want to 
automate "create test cases for epic X", use the REST API directly.

See: ado_mcp_client.py - it's simple Python, no AI needed.
"""


print("""
╔═══════════════════════════════════════════════════════════════════╗
║                    WHAT YOU SHOULD DO                             ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  🥇 EASIEST: Just use VS Code Copilot Chat!                       ║
║     Type: "Create test cases for Epic #3"                         ║
║     That's it. You already did this and it worked!                ║
║                                                                   ║
║  🥈 FOR AUTOMATION: Use the REST API wrapper                      ║
║     python ado_mcp_client.py                                      ║
║     (No AI needed, just automated test case creation)             ║
║                                                                   ║
║  🥉 FOR CUSTOM AI: Use Semantic Kernel or LangChain               ║
║     These frameworks let you connect AI + MCP tools               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

The MCP server alone doesn't understand prompts.
It needs an AI (like Copilot) to interpret what you want!
""")


async def main():
    """
    Example prompts demonstrating AI + MCP integration for Azure DevOps
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("🚀 Semantic Kernel + MCP + Azure DevOps Demo\n")
    print("=" * 70)
    
    # Example prompts to execute
    example_prompts = [
        "Create 3 test cases for US #13 in project demo focusing on negative scenarios",
        "Create a bug report for US #13 about navigation menu not working on mobile",
        "List all work items in project demo",
    ]
    
    print("\n📝 Prompts to Execute:")
    for i, prompt in enumerate(example_prompts, 1):
        print(f"   {i}. {prompt}")
    
    print("\n" + "=" * 70)
    
    try:
        print("\n🔧 Initializing AI + MCP setup...\n")
        
        # Validate environment variables
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        ado_pat = os.getenv("AZURE_DEVOPS_PAT")
        ado_org = os.getenv("AZURE_DEVOPS_ORG", "GauravKhurana0262")
        
        if not endpoint or not api_key:
            print("❌ Missing Azure OpenAI credentials!")
            print("   Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file")
            return
        
        if not ado_pat:
            print("❌ Missing Azure DevOps PAT token!")
            print("   Please set AZURE_DEVOPS_PAT in .env file")
            return
        
        # Set PAT for MCP server
        os.environ["AZURE_DEVOPS_EXT_PAT"] = ado_pat
        
        # Create single MCP connection for all prompts (reuse connection)
        ado_plugin = None
        
        try:
            # Execute each prompt
            for i, prompt in enumerate(example_prompts, 1):
                print(f"\n{'='*70}")
                print(f"🎯 Executing Prompt {i}/{len(example_prompts)}")
                print(f"{'='*70}")
                print(f"📝 Prompt: {prompt}\n")
                
                try:
                    result, ado_plugin = await create_test_cases_with_ai(prompt, ado_plugin)
                    print(f"✅ Result:\n{result}\n")
                except Exception as e:
                    print(f"❌ Error executing prompt: {e}\n")
                    import traceback
                    traceback.print_exc()
            
            print(f"\n{'='*70}")
            print("✅ All prompts executed!")
            print(f"{'='*70}\n")
            
        finally:
            # Properly close MCP connection
            if ado_plugin:
                print("🔌 Closing Azure DevOps MCP connection...")
                try:
                    await ado_plugin.close()
                    print("✅ Connection closed cleanly")
                except Exception as e:
                    print(f"⚠️  Connection cleanup warning: {e}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure your .env file has all required credentials.")


if __name__ == "__main__":
    asyncio.run(main())

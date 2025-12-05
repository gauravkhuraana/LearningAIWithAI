"""
🎯 Azure DevOps MCP Integration with LangChain

This demonstrates how to use LangChain (instead of Semantic Kernel) 
to connect Azure OpenAI with MCP tools for Azure DevOps automation.

LangChain provides a different approach to AI orchestration with its
own patterns for tool integration and agent workflows.
"""

# pip install langchain langchain-openai mcp

import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel import Kernel

# Load environment variables
load_dotenv()


async def create_langchain_agent_with_mcp(ado_plugin=None):
    """
    Create a LangChain LLM with Azure OpenAI and MCP tools
    
    Returns: (llm_with_tools, ado_plugin, kernel)
    """
    
    # 1. Initialize Azure OpenAI with LangChain
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = "2024-02-15-preview"
    
    if not endpoint or not api_key:
        raise ValueError("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file")
    
    llm = AzureChatOpenAI(
        azure_deployment=deployment_name,
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        temperature=0
    )
    
    # 2. Connect to MCP server (reuse existing connection if provided)
    kernel = None
    if ado_plugin is None:
        print("   🔌 Connecting to Azure DevOps MCP server...")
        
        # Use Semantic Kernel's MCPStdioPlugin for MCP connection
        kernel = Kernel()
        ado_plugin = MCPStdioPlugin(
            name="azure_devops",
            command="npx",
            args=["-y", "@azure-devops/mcp@next", os.getenv("AZURE_DEVOPS_ORG", "GauravKhurana0262")],
            description="Azure DevOps work item management",
            kernel=kernel
        )
        await ado_plugin.connect()
        
        # Check loaded functions
        if "azure_devops" in kernel.plugins:
            ado_plugin_obj = kernel.plugins["azure_devops"]
            functions = list(ado_plugin_obj.functions.keys())
            print(f"   ✅ Connected! Available Azure DevOps tools: {len(functions)}")
            if len(functions) > 0:
                print(f"      Tools: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
    else:
        # Get kernel from existing plugin
        kernel = ado_plugin.kernel if hasattr(ado_plugin, 'kernel') else None
    
    # 3. Use LangChain with tool calling enabled
    # We'll manually invoke tools through Semantic Kernel when needed
    print(f"   📦 LangChain agent ready with MCP tools")
    
    return llm, ado_plugin, kernel


async def execute_prompt_with_langchain(prompt: str, llm, ado_plugin, kernel):
    """
    Execute a prompt using LangChain LLM with MCP tools (multi-turn pattern)
    """
    try:
        from semantic_kernel.functions import KernelArguments
        
        # Build system prompt
        system_message = SystemMessage(content="""You are an Azure DevOps assistant with access to real tools.

CRITICAL: When you need information, say "TOOL_CALL: function_name(parameters)" on a new line.
Then I will execute the tool and give you results.

Available tools pattern:
- TOOL_CALL: get-workitem(id=13) - Get work item details
- TOOL_CALL: list-workitems(project=demo) - List all work items
- TOOL_CALL: create-testcase(title=X, description=Y, project=demo) - Create test case

DO NOT make assumptions. Request tools when you need data.""")
        
        # Create user message
        user_message = HumanMessage(content=prompt)
        
        # Get initial response
        print(f"   🤖 AI analyzing request...")
        response = await llm.ainvoke([system_message, user_message])
        
        print(f"   💭 AI Response: {response.content[:200]}...")
        
        # Parse for tool calls (simple pattern matching)
        tool_calls_made = False
        tool_results = []
        
        if kernel and "azure_devops" in kernel.plugins:
            ado_plugin_obj = kernel.plugins["azure_devops"]
            
            # Strategy: Automatically detect what tools to call based on prompt
            import re
            
            # Pattern 1: Extract work item ID
            work_item_ids = re.findall(r'#(\d+)|US[:\s]*#?(\d+)|ID[:\s]*(\d+)|item[:\s]*(\d+)', prompt, re.IGNORECASE)
            if work_item_ids:
                wi_id = next((id for group in work_item_ids for id in group if id), None)
                if wi_id:
                    print(f"   🔧 Detected work item #{wi_id}, fetching details...")
                    
                    # Find the right function
                    for fn_name, fn in ado_plugin_obj.functions.items():
                        fn_lower = fn_name.lower().replace('-', '').replace('_', '')
                        if 'get' in fn_lower and 'workitem' in fn_lower:
                            try:
                                args = KernelArguments(id=wi_id, project="demo")
                                result = await fn.invoke(kernel, args)
                                tool_results.append(f"Work Item #{wi_id} Details:\n{result}")
                                print(f"   ✅ Retrieved work item data")
                                tool_calls_made = True
                                break
                            except Exception as e:
                                print(f"   ⚠️  Error calling {fn_name}: {e}")
            
            # Pattern 2: List work items
            if 'list' in prompt.lower() and 'work' in prompt.lower():
                print(f"   🔧 Listing work items in project demo...")
                
                for fn_name, fn in ado_plugin_obj.functions.items():
                    fn_lower = fn_name.lower().replace('-', '').replace('_', '')
                    if 'list' in fn_lower and 'workitem' in fn_lower:
                        try:
                            args = KernelArguments(project="demo")
                            result = await fn.invoke(kernel, args)
                            tool_results.append(f"Work Items List:\n{result}")
                            print(f"   ✅ Retrieved work items list")
                            tool_calls_made = True
                            break
                        except Exception as e:
                            print(f"   ⚠️  Error calling {fn_name}: {e}")
            
            # Pattern 3: Create test case
            if 'create' in prompt.lower() and 'test' in prompt.lower():
                # First, we need work item details if ID is mentioned
                # Then AI can create test cases
                if not tool_results:
                    print(f"   ⚠️  Need work item data before creating test cases")
        
        # Send tool results back for final answer
        if tool_calls_made and tool_results:
            print(f"   🔄 Sending tool results back to AI...")
            final_prompt = f"""Original request: {prompt}

Real data from Azure DevOps tools:
{chr(10).join(tool_results)}

Now respond to the original request using this REAL data. 
If asked to create test cases, list them with titles and steps.
If asked to create bugs, describe what would be created."""
            
            final_msg = HumanMessage(content=final_prompt)
            final_response = await llm.ainvoke([system_message, final_msg])
            return final_response.content
        else:
            # No tools called, return original response
            if "retrieve" in response.content.lower() or "fetch" in response.content.lower():
                return response.content + "\n\n⚠️  (Note: Tools available but not auto-executed)"
            return response.content
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {e}"


print("""
╔═══════════════════════════════════════════════════════════════════╗
║              LangChain + MCP + Azure DevOps Demo                  ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  This demonstrates using LangChain instead of Semantic Kernel     ║
║  for AI orchestration with MCP tools.                             ║
║                                                                   ║
║  LangChain provides:                                              ║
║  - Different agent patterns (ReAct, OpenAI Functions)             ║
║  - Rich ecosystem of integrations                                 ║
║  - Memory and conversation management                             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


async def main():
    """
    Main execution with LangChain agent
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("🚀 LangChain + MCP + Azure DevOps Demo\n")
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
        print("\n🔧 Initializing LangChain + MCP setup...\n")
        
        # Validate environment variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        ado_pat = os.getenv("AZURE_DEVOPS_PAT")
        
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
        
        # Create LangChain agent with MCP tools (reuse connection)
        ado_plugin = None
        llm = None
        kernel = None
        
        try:
            # Execute each prompt
            for i, prompt in enumerate(example_prompts, 1):
                print(f"\n{'='*70}")
                print(f"🎯 Executing Prompt {i}/{len(example_prompts)}")
                print(f"{'='*70}")
                print(f"📝 Prompt: {prompt}\n")
                
                try:
                    # Create agent on first run, reuse for subsequent runs
                    if llm is None:
                        llm, ado_plugin, kernel = await create_langchain_agent_with_mcp(ado_plugin)
                    
                    result = await execute_prompt_with_langchain(prompt, llm, ado_plugin, kernel)
                    print(f"\n✅ Result:\n{result}\n")
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

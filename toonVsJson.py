"""
TOON vs JSON Comparison Demo
Single file demonstrating format conversion and token analysis with Azure OpenAI
"""

import os
import json
import tiktoken
from dotenv import load_dotenv
from openai import AzureOpenAI
from toon_format import encode, decode

# Load environment variables
load_dotenv()


# Sample Data Examples
EXAMPLES = {
    "simple": {
        "name": "Alice Johnson",
        "age": 30,
        "email": "alice@example.com",
        "active": True
    },
    
    "medium": {
        "user": {
            "id": 12345,
            "profile": {
                "name": "Bob Smith",
                "location": "San Francisco",
                "skills": ["Python", "JavaScript", "Go"]
            }
        },
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Mouse", "price": 29.99},
            {"id": 3, "name": "Keyboard", "price": 79.99}
        ]
    },
    
    "complex": {
        "status": "success",
        "data": {
            "employees": [
                {"emp_id": "E001", "name": "John Doe", "dept": "Engineering", "salary": 95000},
                {"emp_id": "E002", "name": "Jane Smith", "dept": "Marketing", "salary": 85000},
                {"emp_id": "E003", "name": "Mike Johnson", "dept": "Engineering", "salary": 92000},
                {"emp_id": "E004", "name": "Sarah Williams", "dept": "HR", "salary": 78000}
            ],
            "total_count": 4,
            "page": 1
        },
        "timestamp": "2024-11-24T10:30:00Z"
    }
}


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def demo_conversion():
    """Demonstrate JSON to TOON conversion"""
    print("\n" + "=" * 80)
    print("  TOON vs JSON - Format Conversion Demo")
    print("=" * 80)
    
    for name, data in EXAMPLES.items():
        print(f"\n📦 {name.upper()} Example")
        print("-" * 80)
        
        # Convert to both formats
        json_str = json.dumps(data, indent=2)
        json_compact = json.dumps(data, separators=(',', ':'))
        toon_str = encode(data)
        
        # Count tokens
        json_tokens = count_tokens(json_compact)
        toon_tokens = count_tokens(toon_str)
        savings = ((json_tokens - toon_tokens) / json_tokens) * 100
        
        # Show formats
        print("\n📄 JSON (compact):")
        print(json_compact[:150] + "..." if len(json_compact) > 150 else json_compact)
        
        print("\n🎨 TOON:")
        print(toon_str[:150] + "..." if len(toon_str) > 150 else toon_str)
        
        # Show comparison
        print(f"\n📊 Comparison:")
        print(f"   JSON:    {json_tokens} tokens, {len(json_compact)} chars")
        print(f"   TOON:    {toon_tokens} tokens, {len(toon_str)} chars")
        print(f"   Savings: {json_tokens - toon_tokens} tokens ({savings:.1f}%)")
        
        # Verify round-trip
        decoded = decode(toon_str)
        print(f"   Round-trip: {'✅ Success' if data == decoded else '❌ Failed'}")


def demo_azure_openai():
    """Demonstrate with Azure OpenAI API"""
    print("\n" + "=" * 80)
    print("  Azure OpenAI Integration Test")
    print("=" * 80)
    
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("\n⚠️  Azure OpenAI not configured (skipping API test)")
        print("   To enable: Set credentials in .env file")
        return
    
    try:
        # Setup client
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        data = EXAMPLES["medium"]
        
        # Prepare prompts
        json_str = json.dumps(data, indent=2)
        toon_str = encode(data)
        
        json_prompt = f"Here is data in JSON:\n\n{json_str}\n\nAcknowledge receipt."
        toon_prompt = f"Here is data in TOON:\n\n{toon_str}\n\nAcknowledge receipt."
        
        print(f"\n⚠️  Making 2 API calls to {deployment}...")
        
        # Call API with JSON
        print("📤 Calling with JSON...")
        json_response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": json_prompt}],
            max_tokens=50
        )
        
        # Call API with TOON
        print("📤 Calling with TOON...")
        toon_response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": toon_prompt}],
            max_tokens=50
        )
        
        # Show results
        json_tokens = json_response.usage.prompt_tokens
        toon_tokens = toon_response.usage.prompt_tokens
        savings = json_tokens - toon_tokens
        savings_pct = (savings / json_tokens) * 100
        
        print(f"\n📊 API Results:")
        print(f"   JSON: {json_tokens} tokens")
        print(f"   TOON: {toon_tokens} tokens")
        print(f"   Savings: {savings} tokens ({savings_pct:.1f}%)")
        
        print(f"\n💰 Cost Impact (at $30/1M tokens):")
        for scale in [1000, 10000, 100000]:
            cost_saved = (savings * scale / 1_000_000) * 30
            print(f"   {scale:,} requests: ${cost_saved:.2f} saved")
        
        print("\n✅ Azure OpenAI test complete!")
        
    except Exception as e:
        print(f"\n⚠️  Azure OpenAI error: {e}")
        print("   Check your .env configuration")


def main():
    """Main demo"""
    print("\n" + "=" * 80)
    print("  TOON vs JSON Comparison")
    print("  Token-optimized format for LLM applications")
    print("=" * 80)
    
    # Run demos
    demo_conversion()
    demo_azure_openai()
    
    # Summary
    print("\n" + "=" * 80)
    print("✨ Summary:")
    print("   • TOON reduces tokens by 20-60% vs JSON")
    print("   • Best for tabular/uniform data structures")
    print("   • Perfect round-trip conversion (lossless)")
    print("   • Direct cost savings on LLM API calls")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

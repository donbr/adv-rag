#!/usr/bin/env python3
"""Test parameter validation to confirm schemas work correctly"""
import asyncio
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp import Client
from src.mcp.server import mcp

async def test_parameter_validation():
    """Test that parameter validation works correctly"""
    print("🧪 Testing parameter validation...")
    
    async with Client(mcp) as client:
        # Test with wrong parameter name
        try:
            result = await client.call_tool('naive_retriever', {'query': 'test'})
            print('❌ Wrong param "query" was accepted - this should not happen!')
            return False
        except Exception as e:
            print(f'✅ Correct rejection of wrong param "query": {str(e)[:80]}...')
        
        # Test with correct parameter name
        try:
            result = await client.call_tool('naive_retriever', {'question': 'What makes a good action movie?'})
            print('✅ Correct param "question" was accepted')
            
            # DETAILED STRUCTURE ANALYSIS
            print("\n🔍 DETAILED RESULT STRUCTURE:")
            print(f"   result type: {type(result)}")
            print(f"   result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if result and len(result) > 0:
                first_element = result[0]
                print(f"   result[0] type: {type(first_element)}")
                print(f"   result[0] attributes: {[attr for attr in dir(first_element) if not attr.startswith('_')]}")
                
                if hasattr(first_element, 'text'):
                    raw_text = first_element.text
                    print(f"   result[0].text type: {type(raw_text)}")
                    print(f"   result[0].text preview: {raw_text[:100]}...")
                    
                    # Parse the JSON
                    try:
                        parsed_json = json.loads(raw_text)
                        print(f"   json.loads(result[0].text) type: {type(parsed_json)}")
                        print(f"   json.loads(result[0].text) keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
                        
                        if isinstance(parsed_json, dict) and 'answer' in parsed_json:
                            answer = parsed_json['answer']
                            print(f"   json.loads(result[0].text)['answer'] type: {type(answer)}")
                            
                            print("\n🎯 COMPLETE NAVIGATION PATH:")
                            print("   result                                    -> list")
                            print("   result[0]                                -> TextContent object")
                            print("   result[0].text                           -> JSON string")
                            print("   json.loads(result[0].text)               -> dict")
                            print("   json.loads(result[0].text)['answer']     -> final answer string")
                            
                            print(f"\n📝 Final Answer (first 200 chars): {answer[:200]}...")
                            print(f"   📊 Answer length: {len(answer)} characters")
                        else:
                            print(f"   ⚠️  No 'answer' key found in parsed JSON")
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Failed to parse JSON: {e}")
                else:
                    print(f"   ❌ result[0] has no 'text' attribute")
            else:
                print(f"   ❌ Empty or invalid result")
            
            return True
        except Exception as e:
            print(f'❌ Error with correct param "question": {str(e)[:80]}...')
            print(f"🔍 Full error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_parameter_validation())
    print(f"\n{'✅ VALIDATION PASSED' if success else '❌ VALIDATION FAILED'}") 
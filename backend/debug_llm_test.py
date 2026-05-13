#!/usr/bin/env python3
"""
Debug LLM test function directly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_settings_service import test_llm_connection

async def debug_llm_test():
    """Debug LLM test function directly"""
    print("Debugging LLM Test Function...")
    print("=" * 50)
    
    try:
        result = await test_llm_connection(
            "groq",
            "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"
        )
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_llm_test())

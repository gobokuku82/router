"""Test resume functionality"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

# Set environment variable before importing
os.environ["NO_INPUT_MODE"] = "true"

from app.services.docs_agent.create_document_agent import CreateDocumentAgent

print("Testing resume in API mode...")
agent = CreateDocumentAgent()

# Step 1: Initial run
result1 = agent.run("Create sales visit report")
print(f"\nStep 1 Result: {result1}")

if result1.get("interrupted"):
    thread_id = result1.get("thread_id")
    print(f"\nStep 2: Resuming with thread_id: {thread_id}")
    
    # Step 2: Resume with verification
    result2 = agent.resume(thread_id, "y", "verification_reply")
    print(f"\nStep 2 Result: {result2}")
    
    if result2.get("interrupted"):
        print("\nStep 3: Providing full information...")
        
        # Step 3: Resume with full info
        full_info = "Visit date 2024-01-25, Client: Yumi Medical, Contact: Dr. Kim"
        result3 = agent.resume(thread_id, full_info, "user_reply")
        print(f"\nStep 3 Result: {result3}")
        
        if result3.get("success"):
            print("\nSUCCESS: Document created!")
        else:
            print(f"\nFinal result: {result3}")

# Clean up
os.environ.pop("NO_INPUT_MODE", None)
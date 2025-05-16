"""
Example script demonstrating how to use the contact form tool.

This script shows how to:
1. Import and use the contact_form_tool
2. Handle success and error responses
3. Validate input before submission

Usage:
    uv run python examples/contact_form_example.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from py_src.lets_talk.tools.contact_tool import contact_form_tool, is_valid_email

def example_contact_form_usage():
    """
    Example function demonstrating the use of the contact form tool.
    """
    print("=== Contact Form Example ===")
    
    # Example 1: Valid submission
    print("\nExample 1: Valid submission")
    name = "Jane Doe"
    email = "jane.doe@example.com"
    subject = "Question about RAG Evaluation"
    message = "I'm interested in your RAG evaluation methods. Can you provide more information?"
    
    # Call the contact form tool
    response = contact_form_tool(name, email, subject, message)
    print(f"Response: {response}")
    
    # Example 2: Invalid email
    print("\nExample 2: Invalid email")
    name = "John Smith"
    email = "invalid-email"  # Invalid email format
    subject = "Collaboration Request"
    message = "I'd like to discuss a potential collaboration on an AI project."
    
    # Manual validation
    if not is_valid_email(email):
        print("Validation Error: Please provide a valid email address.")
    else:
        # Call the contact form tool (this would fail validation internally)
        response = contact_form_tool(name, email, subject, message)
        print(f"Response: {response}")
    
    # Example 3: Missing required fields
    print("\nExample 3: Missing required fields")
    name = ""  # Missing name
    email = "john@example.com"
    subject = "Feedback"
    message = "Great blog posts! Very informative."
    
    # Manual validation
    if not name:
        print("Validation Error: Name is required.")
    else:
        # Call the contact form tool (this would fail validation internally)
        response = contact_form_tool(name, email, subject, message)
        print(f"Response: {response}")

if __name__ == "__main__":
    example_contact_form_usage()

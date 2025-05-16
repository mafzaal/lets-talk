"""
Contact Us tool implementation.
"""

import logging
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Set up logging
logger = logging.getLogger(__name__)

@tool
def contact_form_tool(name: str, email: str, subject: str, message: str) -> str:
    """
    Send a contact form message to TheDataGuy.
    This tool can be used when someone wants to:
    - Reach out with questions about blog content
    - Request a collaboration opportunity 
    - Share feedback about blog posts
    - Ask for consulting services or speaking engagements
    - Report issues with the blog or chat application
    
    Args:
        name: Name of the person making contact
        email: Email address to reply to
        subject: Subject line of the contact message
        message: The main message content
        
    Returns:
        A confirmation message if successful, or an error message if the contact form submission failed
    """
    try:
        # Validate inputs
        validation_errors = []
        
        if not name or name.strip() == "":
            validation_errors.append("Name is required")
            
        if not email or email.strip() == "":
            validation_errors.append("Email is required")
        elif not is_valid_email(email):
            validation_errors.append("Please provide a valid email address")
            
        if not subject or subject.strip() == "":
            validation_errors.append("Subject is required")
            
        if not message or message.strip() == "":
            validation_errors.append("Message is required")
        elif len(message) < 10:
            validation_errors.append("Message is too short. Please provide a more detailed message")
        
        # If there are validation errors, return them
        if validation_errors:
            return "Please correct the following issues:\n- " + "\n- ".join(validation_errors)
            
        # Log the contact form submission
        logger.info(f"Contact form submission from {name} ({email})")
        
        # Save the contact request to a local file for demonstration
        # In a production environment, this would typically use an email API or database
        contact_data = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "subject": subject,
            "message": message
        }
        
        # Create a directory for storing contact submissions if it doesn't exist
        os.makedirs("./data/contact_submissions", exist_ok=True)
        
        # Generate a unique filename based on timestamp
        filename = f"./db/contact_submissions/contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Save the contact data to a JSON file
        with open(filename, 'w') as f:
            json.dump(contact_data, f, indent=2)
            
        logger.info(f"Contact form data saved to {filename}")
        
        return f"Thank you, {name}! Your message has been sent to TheDataGuy. You will receive a response at {email} soon."
    
    except Exception as e:
        error_msg = f"Error processing contact form: {str(e)}"
        logger.error(error_msg)
        return f"There was an error processing your contact request. Please try again later or reach out directly via LinkedIn."


def is_valid_email(email: str) -> bool:
    """
    Basic validation for email format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if the email format appears valid, False otherwise
    """
    import re
    
    # More comprehensive email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Check if the email matches the pattern
    return bool(re.match(email_pattern, email))

"""Contact form tool for external API use."""
import logging
import os
import json
import re
from typing import Any, Dict
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


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
        A confirmation message if successful, or an error message if failed
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
        
        if validation_errors:
            return f"Contact form validation failed: {', '.join(validation_errors)}"
        
        # Create contact submission data
        submission = {
            "name": name.strip(),
            "email": email.strip().lower(),
            "subject": subject.strip(),
            "message": message.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_agent": "AI Chat Assistant",
            "ip_address": "internal",
            "status": "pending"
        }
        
        # Save to file
        contact_dir = Path("db/contact_submissions")
        contact_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"contact_{timestamp}.json"
        file_path = contact_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(submission, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Contact form submission saved: {filename}")
        
        # Return success message
        return (
            f"Thank you {name}! Your message has been received successfully. "
            f"We'll get back to you at {email} regarding '{subject}'. "
            f"Your submission reference is: {timestamp}"
        )
        
    except Exception as e:
        error_msg = f"Failed to submit contact form: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_pending_contacts(limit: int = 10) -> list:
    """Get pending contact submissions."""
    try:
        contact_dir = Path("db/contact_submissions")
        if not contact_dir.exists():
            return []
        
        submissions = []
        for file_path in contact_dir.glob("contact_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    submission = json.load(f)
                    submission['file'] = file_path.name
                    submissions.append(submission)
            except Exception as e:
                logger.error(f"Error reading contact file {file_path}: {e}")
        
        # Sort by timestamp (newest first)
        submissions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return submissions[:limit]
        
    except Exception as e:
        logger.error(f"Error getting pending contacts: {e}")
        return []


def mark_contact_as_processed(filename: str) -> bool:
    """Mark a contact submission as processed."""
    try:
        contact_dir = Path("db/contact_submissions")
        file_path = contact_dir / filename
        
        if not file_path.exists():
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            submission = json.load(f)
        
        submission['status'] = 'processed'
        submission['processed_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(submission, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error marking contact as processed: {e}")
        return False

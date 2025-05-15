"""
Blog Posts API tool implementation.
"""

import json
import logging
import requests
from typing import Optional


# Set up logging
logger = logging.getLogger(__name__)


def get_blog_posts_tool(
    max_posts: Optional[int] = None,
    category: Optional[str] = None,
    ) -> str:
    """
        Fetches the latest blog posts from TheDataGuy's tech blog API. 
        Use this tool when you need information about recent posts, their categories, reading time, or URLs.
        Supports optional parameters: max:N to limit results, category:NAME to filter by category.
        Example: 'max:3 category:ragas' will return up to 3 posts in the Ragas category.
    """

    logger.info(f"Running BlogPostsTool with max_posts: {max_posts}, category: {category}")

    api_url = "https://thedataguy.pro/api/posts.json"

    try:
        # Fetch data from the API using the instance attribute
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response
        posts = response.json()
        
        # Validate the data structure
        if not isinstance(posts, list):
            return "Error: Invalid data format from API. Expected a list of posts."
        
        # Filter by category if provided
        if category:
            posts = [post for post in posts if category.lower() in [cat.lower() for cat in post.get("categories", [])]]
        
        # Sort by date (newest first) and limit results
        posts.sort(key=lambda x: x.get("date", ""), reverse=True)
        posts = posts[:max_posts]
        
        # Format the results
        if not posts:
            return "No blog posts found with the specified criteria."
        
        result = f"Found {len(posts)} recent blog posts from TheDataGuy:\n\n"
        
        for post in posts:
            # Extract required fields
            title = post.get("title", "Untitled")
            date = post.get("date", "Unknown date")
            description = post.get("description", "No description available")
            categories = ", ".join(post.get("categories", []))
            reading_time = post.get("readingTime", 0)
            url = post.get("url", "")
            
            # Format post information
            result += f"📝 {title}\n"
            result += f"📅 Published: {date}\n"
            result += f"⏱️ Reading time: {reading_time} minutes\n"
            result += f"🏷️ Categories: {categories}\n"
            result += f"📌 URL: {url}\n"
            result += f"📋 Description: {description}\n\n"
        
        result += "You can ask for more details about any of these posts or filter by category."
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching blog posts: {str(e)}")
        return f"Error fetching blog posts: {str(e)}"
    except json.JSONDecodeError:
        logger.error("Error decoding JSON response from the API.")
        return "Error: Invalid JSON data received from the API."
    except Exception as e:
        logger.error(f"Unexpected error retrieving blog posts: {str(e)}")
        return f"Unexpected error retrieving blog posts: {str(e)}"



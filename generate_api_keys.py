#!/usr/bin/env python3
"""
Generate secure API keys for the LangGraph API access control.
"""

import secrets
import string
import sys
from typing import List


def generate_api_key(length: int = 32, prefix: str = "ltk") -> str:
    """
    Generate a secure API key.
    
    Args:
        length: Length of the random part (default: 32)
        prefix: Prefix for the key (default: "ltk" for lets-talk-key)
    
    Returns:
        A secure API key string
    """
    # Characters to use in the key (alphanumeric)
    alphabet = string.ascii_letters + string.digits
    
    # Generate random part
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Combine prefix and random part
    return f"{prefix}_{random_part}"


def generate_multiple_keys(count: int = 3) -> List[str]:
    """Generate multiple API keys."""
    return [generate_api_key() for _ in range(count)]


def update_env_auth_file(keys: List[str], filename: str = ".env.auth") -> None:
    """
    Update the .env.auth file with new API keys.
    
    Args:
        keys: List of API keys to add
        filename: Path to the .env.auth file
    """
    try:
        # Read existing content
        try:
            with open(filename, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = "# API Keys for accessing private endpoints\n"
        
        # Add new keys
        new_content = content + "\n# Generated API Keys\n"
        for i, key in enumerate(keys, 1):
            new_content += f"API_KEY_{i}={key}\n"
        
        # Write back to file
        with open(filename, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated {filename} with {len(keys)} new API keys")
        
    except Exception as e:
        print(f"❌ Error updating {filename}: {e}")


def update_nginx_config(keys: List[str], filename: str = "nginx.conf") -> None:
    """
    Print instructions for updating nginx.conf with new API keys.
    
    Args:
        keys: List of API keys to add
        filename: Path to the nginx.conf file
    """
    print(f"\n📝 To update {filename}, replace the map section with:")
    print("\nmap $http_x_api_key $api_key_valid {")
    print("    default 0;")
    for key in keys:
        print(f'    "{key}" 1;')
    print("}")
    print(f"\nThen restart nginx: docker-compose restart nginx-proxy")


def main():
    """Main function."""
    print("🔐 LangGraph API Key Generator")
    print("=" * 40)
    
    # Get number of keys to generate
    try:
        if len(sys.argv) > 1:
            count = int(sys.argv[1])
        else:
            count = int(input("How many API keys to generate? [3]: ") or "3")
    except ValueError:
        print("❌ Invalid number. Using default of 3.")
        count = 3
    
    # Generate keys
    print(f"\n🔑 Generating {count} API keys...")
    keys = generate_multiple_keys(count)
    
    # Display keys
    print("\n✨ Generated API Keys:")
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {key}")
    
    # Ask if user wants to update files
    update_files = input("\n📁 Update .env.auth file? [y/N]: ").lower().startswith('y')
    
    if update_files:
        update_env_auth_file(keys)
    
    # Always show nginx instructions
    update_nginx_config(keys)
    
    print("\n✅ Done! Remember to:")
    print("  1. Update nginx.conf with the new keys")
    print("  2. Restart the services: docker-compose restart nginx-proxy")
    print("  3. Test the API with the new keys")
    print("  4. Keep your API keys secure!")


if __name__ == "__main__":
    main()

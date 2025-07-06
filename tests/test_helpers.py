import uuid
import random
import string
from typing import Dict, Any

def generate_random_user() -> Dict[str, str]:
    """Generate a random user with unique username and password"""
    # Create unique username with timestamp-like suffix
    random_suffix = ''.join(random.choices(string.digits, k=6))
    username = f"user_{uuid.uuid4().hex[:8]}_{random_suffix}"

    # Generate random password
    password = f"pass_{uuid.uuid4().hex[:12]}"

    return {
        "username": username,
        "password": password
    }

def generate_random_task(title_prefix: str = "Task") -> Dict[str, Any]:
    """Generate a random task with unique title"""
    random_id = uuid.uuid4().hex[:8]
    return {
        "title": f"{title_prefix}_{random_id}",
        "description": f"Test description for {title_prefix}_{random_id}",
        "status": random.choice(["pending", "completed"])
    }

class UserManager:
    """Manages test users to avoid conflicts"""

    def __init__(self):
        self.created_users = []

    def create_user(self, prefix: str = "testuser") -> Dict[str, str]:
        """Create a unique test user"""
        user = {
            "username": f"{prefix}_{uuid.uuid4().hex[:8]}",
            "password": f"testpass_{uuid.uuid4().hex[:8]}"
        }
        self.created_users.append(user)
        return user

    def get_random_user(self) -> Dict[str, str]:
        """Get a completely random user"""
        return generate_random_user()

    def cleanup(self):
        """Clear created users list"""
        self.created_users.clear()

# Global instance for convenience
user_manager = UserManager()  
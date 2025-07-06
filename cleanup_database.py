import os
import asyncio
from pathlib import Path

async def cleanup_database():
    """Clean up database and test artifacts"""
    print("🧹 Cleaning up database and test artifacts...")

    # Remove database files
    db_files = [
        "tasks.db",
        "test.db",
        "tasks.db-journal",
        "test.db-journal"
    ]

    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   ✅ Removed {db_file}")

    # Remove cache directories
    cache_dirs = [
        ".pytest_cache",
        "__pycache__",
        "tests/__pycache__",
        "app/__pycache__",
        ".coverage"
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            if os.path.isfile(cache_dir):
                os.remove(cache_dir)
                print(f"   ✅ Removed {cache_dir}")
            else:
                import shutil
                shutil.rmtree(cache_dir)
                print(f"   ✅ Removed directory {cache_dir}")

    # Remove .pyc files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                pyc_file = os.path.join(root, file)
                os.remove(pyc_file)
                print(f"   ✅ Removed {pyc_file}")

    print("✨ Cleanup complete! Database and cache cleared.")
    print("🧪 You can now run tests with a fresh state.")

if __name__ == "__main__":
    asyncio.run(cleanup_database())
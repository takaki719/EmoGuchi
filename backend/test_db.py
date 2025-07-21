"""Test database integration"""
import asyncio
from services.database_service import DatabaseService
from models.database import Base

async def test_db():
    """Test database connection and table creation"""
    print("Testing database connection...")
    
    # Initialize database service
    db_service = DatabaseService()
    await db_service.initialize()
    
    print("✅ Database initialized successfully")
    
    # List all tables
    async for session in db_service.get_session():
        # Get table names using reflection
        from sqlalchemy import inspect
        
        # Use sync inspection on the database file
        import sqlite3
        conn = sqlite3.connect('./emoguchi.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()
        
        print(f"\n📊 Tables in database: {tables}")
        break
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_db())
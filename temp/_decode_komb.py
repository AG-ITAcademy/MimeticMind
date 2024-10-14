import pickle
import base64
from sqlalchemy import create_engine, text
from config import Config

# Create a database connection
engine = create_engine('postgresql://postgres:the bad zone@localhost/celery_queue')

# SQL query to fetch messages from kombu_message table
query = text("SELECT * FROM kombu_message ORDER BY timestamp DESC LIMIT 10")

def decode_message(payload):
    try:
        # First, try decoding with base64
        decoded = base64.b64decode(payload)
    except:
        # If base64 decoding fails, use the payload as is
        decoded = payload
    
    try:
        # Now try to unpickle the decoded data
        return pickle.loads(decoded)
    except:
        # If unpickling fails, return the decoded data as is
        return decoded

with engine.connect() as connection:
    result = connection.execute(query)
    for row in result:
        print(f"Message ID: {row.id}")
        print(f"Timestamp: {row.timestamp}")
        
        try:
            decoded_payload = decode_message(row.payload)
            print("Decoded Payload:")
            print(decoded_payload)
        except Exception as e:
            print(f"Error decoding payload: {str(e)}")
            print("Raw Payload:")
            print(row.payload)
        
        print("\n" + "="*50 + "\n")
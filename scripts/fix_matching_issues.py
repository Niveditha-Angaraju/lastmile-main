"""
Diagnostic script to check why matches aren't being created.
Helps debug matching service issues.
"""
import sys
import os
import json
import time
import pika

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

def check_queues():
    """Check RabbitMQ queue status."""
    print("Checking RabbitMQ queues...")
    try:
        conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        ch = conn.channel()
        
        queues = ["rider.requests", "driver.near_station", "match.found", "trip.updated"]
        
        for queue in queues:
            try:
                method = ch.queue_declare(queue=queue, durable=True, passive=True)
                message_count = method.method.message_count
                consumer_count = method.method.consumer_count
                print(f"  {queue:20s} - Messages: {message_count:3d}, Consumers: {consumer_count}")
            except Exception as e:
                print(f"  {queue:20s} - Error: {e}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Cannot connect to RabbitMQ: {e}")
        return False

def peek_queue_messages(queue_name, limit=5):
    """Peek at messages in a queue without consuming them."""
    try:
        conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        ch = conn.channel()
        ch.queue_declare(queue=queue_name, durable=True)
        
        messages = []
        for _ in range(limit):
            method, props, body = ch.basic_get(queue_name, auto_ack=False)
            if not method:
                break
            
            try:
                msg = json.loads(body)
                messages.append(msg)
            except:
                messages.append(body.decode()[:100])
            
            # Re-queue
            ch.basic_nack(method.delivery_tag, requeue=True)
        
        conn.close()
        return messages
    except Exception as e:
        print(f"Error peeking {queue_name}: {e}")
        return []

def main():
    print("="*60)
    print("Matching Service Diagnostic")
    print("="*60)
    print()
    
    # Check queues
    if not check_queues():
        print("\n⚠️  RabbitMQ not accessible. Make sure port forwarding is active.")
        return
    
    print()
    print("Recent messages in queues:")
    print()
    
    # Check rider.requests
    print("rider.requests:")
    rider_msgs = peek_queue_messages("rider.requests", 3)
    for i, msg in enumerate(rider_msgs, 1):
        print(f"  {i}. {json.dumps(msg, indent=2)}")
    if not rider_msgs:
        print("  (no messages)")
    
    print()
    print("driver.near_station:")
    driver_msgs = peek_queue_messages("driver.near_station", 3)
    for i, msg in enumerate(driver_msgs, 1):
        print(f"  {i}. {json.dumps(msg, indent=2)}")
    if not driver_msgs:
        print("  (no messages)")
    
    print()
    print("match.found:")
    match_msgs = peek_queue_messages("match.found", 3)
    for i, msg in enumerate(match_msgs, 1):
        print(f"  {i}. {json.dumps(msg, indent=2)}")
    if not match_msgs:
        print("  (no messages)")
    
    print()
    print("="*60)
    print("Recommendations:")
    print("="*60)
    
    if not rider_msgs and not driver_msgs:
        print("⚠️  No messages in queues. Run a simulation first:")
        print("   python3 scripts/demo_simulation.py")
    elif rider_msgs and driver_msgs:
        print("✅ Messages found in both queues")
        print("⚠️  Check matching service logs:")
        print("   kubectl -n lastmile logs -l app=matching-service --tail=50")
    elif rider_msgs and not driver_msgs:
        print("⚠️  Rider requests found but no driver proximity events")
        print("   Make sure drivers are publishing proximity events")
    elif driver_msgs and not rider_msgs:
        print("⚠️  Driver proximity found but no rider requests")
        print("   Make sure riders are requesting pickups")

if __name__ == "__main__":
    main()


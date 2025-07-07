from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB (local instance, works with Compass)
mongo_client = MongoClient("mongodb://localhost:27017")

# Use database and collection
database = mongo_client["github_events"]
events_collection = database["events"]

@app.route('/')
def home():
    return "Webhook Server is Running!"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Get the type of GitHub event
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json

    try:
        if event_type == "push":
            author_name = payload["pusher"]["name"]
            target_branch = payload["ref"].split("/")[-1]
            timestamp = payload["head_commit"]["timestamp"]

            # Insert PUSH event
            event_document = {
                "action_type": "PUSH",
                "author": author_name,
                "from_branch": None,
                "to_branch": target_branch,
                "timestamp": timestamp
            }
            events_collection.insert_one(event_document)

        elif event_type == "pull_request":
            action_status = payload["action"]
            pull_request = payload["pull_request"]

            author_name = pull_request["user"]["login"]
            from_branch = pull_request["head"]["ref"]
            to_branch = pull_request["base"]["ref"]
            timestamp = pull_request["created_at"]

            # Insert PULL_REQUEST event
            if action_status == "opened":
                event_document = {
                    "action_type": "PULL_REQUEST",
                    "author": author_name,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": timestamp
                }
                events_collection.insert_one(event_document)

            # Insert MERGE event (if PR is closed and merged)
            elif action_status == "closed" and pull_request.get("merged"):
                timestamp = pull_request["merged_at"]

                event_document = {
                    "action_type": "MERGE",
                    "author": author_name,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": timestamp
                }
                events_collection.insert_one(event_document)

        return jsonify({"status": "Event saved"}), 200

    except Exception as error:
        print("Error while processing webhook:", error)
        return jsonify({"error": "Something went wrong"}), 400

@app.route('/events', methods=['GET'])
def fetch_latest_events():
    # Fetch the 10 most recent events
    latest_events = list(events_collection.find().sort("timestamp", -1).limit(10))

    # Convert ObjectId to string for JSON serialization
    for event in latest_events:
        event["_id"] = str(event["_id"])

    return jsonify(latest_events)

if __name__ == "__main__":
    app.run(port=5000)


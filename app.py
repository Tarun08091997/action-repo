from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Replace with your MongoDB Atlas connection string
client = MongoClient("mongodb://localhost:27017")

# Use database and collection
db = client["github_events"]
collection = db["events"]

@app.route('/')
def home():
    return "Webhook Server is Running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    event_type = request.headers.get('X-GitHub-Event')
    data = request.json

    try:
        if event_type == "push":
            author = data["pusher"]["name"]
            branch = data["ref"].split("/")[-1]
            timestamp = data["head_commit"]["timestamp"]
            collection.insert_one({
                "action_type": "PUSH",
                "author": author,
                "from_branch": None,
                "to_branch": branch,
                "timestamp": timestamp
            })

        elif event_type == "pull_request":
            action = data["action"]
            pr = data["pull_request"]
            author = pr["user"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            timestamp = pr["created_at"]

            if action == "opened":
                collection.insert_one({
                    "action_type": "PULL_REQUEST",
                    "author": author,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": timestamp
                })

            elif action == "closed" and pr["merged"]:
                collection.insert_one({
                    "action_type": "MERGE",
                    "author": author,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": pr["merged_at"]
                })

        return jsonify({"status": "Event saved"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong"}), 400

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(10))
    for e in events:
        e["_id"] = str(e["_id"])  # Convert MongoDB ObjectID to string
    return jsonify(events)

if __name__ == "__main__":
    app.run(port=5000)

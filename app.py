import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.cloud.firestore

# --- Firestore Database Setup ---
# This is the modern, cloud-based approach to replace your local MySQL DB.
# It's essential for making your app work on the web, not just your computer.

# IMPORTANT: To make this work, you need to:
# 1. Create a Firebase project at https://console.firebase.google.com/
# 2. Go to Project settings > Service accounts.
# 3. Click "Generate new private key" and download the JSON file.
# 4. Save this file as 'service-account-key.json' in the same folder as this app.py file.
# 5. Set an environment variable so the code can find this key.
#    On Windows (Command Prompt): set GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
#    On Mac/Linux (Terminal): export GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
db = google.cloud.firestore.Client(project='todo-list-ac817') # <-- IMPORTANT: Replace with your actual Project ID from Firebase
tasks_collection = db.collection('tasks')

# --- Flask App Initialization ---
app = Flask(__name__)
# CORS is a security feature that allows your frontend (running in the browser)
# to make requests to your backend (this Flask server).
CORS(app)

# --- API Endpoints ---
# An API endpoint is a specific URL that your frontend can send requests to.
# This is how the frontend and backend communicate.

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    API endpoint to get all tasks from the Firestore database.
    Called when the webpage first loads.
    """
    try:
        all_tasks = []
        # .stream() gets all documents from the 'tasks' collection
        # We order by 'createdAt' to ensure tasks are shown in the order they were added.
        for doc in tasks_collection.order_by('createdAt', direction='ASCENDING').stream():
            task_data = doc.to_dict()
            task_data['id'] = doc.id # Include the document ID
            all_tasks.append(task_data)
        # jsonify converts the Python list of tasks into a JSON format
        # that JavaScript can understand.
        return jsonify(all_tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    """
    API endpoint to add a new task.
    Called when the user submits the 'Add Task' form.
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Task text is required"}), 400

        new_task_data = {
            'text': data['text'],
            'status': 'Not Done',
            'createdAt': google.cloud.firestore.SERVER_TIMESTAMP # This special value tells Firestore to add the timestamp on its end.
        }
        
        # Add the new task and get its reference
        update_time, doc_ref = tasks_collection.add(new_task_data)
        
        # *** FIX ***
        # We fetch the document we just created. This resolves the SERVER_TIMESTAMP 
        # into an actual, JSON-serializable datetime object.
        created_doc = doc_ref.get()
        if created_doc.exists:
            response_data = created_doc.to_dict()
            response_data['id'] = created_doc.id
            return jsonify(response_data), 201 # 201 means "Created"
        else:
            return jsonify({"error": "Failed to retrieve created task"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tasks/<string:task_id>', methods=['PUT'])
def update_task_status(task_id):
    """
    API endpoint to update a task's status (e.g., mark as 'Done').
    The <string:task_id> in the URL is a variable.
    Called when the user clicks the status button on a task.
    """
    try:
        data = request.json
        if not data or 'status' not in data:
            return jsonify({"error": "New status is required"}), 400
        
        # Get a reference to the specific document we want to update.
        task_ref = tasks_collection.document(task_id)
        # .update() changes the fields of the document.
        task_ref.update({'status': data['status']})
        
        return jsonify({"success": True, "message": "Task updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    API endpoint to delete a task.
    Called when the user clicks the delete button.
    """
    try:
        task_ref = tasks_collection.document(task_id)
        task_ref.delete()
        return jsonify({"success": True, "message": "Task deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # This makes the app run. debug=True allows for auto-reloading when you save changes.
    # The app will be accessible at http://127.0.0.1:5000
    app.run(debug=True)


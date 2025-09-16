from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/set_climb', methods=['POST'])
def set_climb():
    """
    Receives climb data from the frontend and triggers the automation script.
    """
    climb_data = request.json
    
    print("Received climb data. Triggering automation worker...")
    
    try:
        # We pass the climb data as a JSON string to the worker script
        climb_data_str = json.dumps(climb_data)
        
        # Execute the automation worker script as a separate process
        subprocess.run(['python3', 'automation_worker.py', climb_data_str], check=True)
        
        return jsonify({"status": "success", "message": "Automation script completed successfully."})
    except subprocess.CalledProcessError as e:
        print(f"Automation script failed with error: {e}")
        return jsonify({"status": "error", "message": "Automation script failed."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500

if __name__ == '__main__':
    # Running on 0.0.0.0 makes the server accessible from your local network
    app.run(host='0.0.0.0', port=5001, debug=True)

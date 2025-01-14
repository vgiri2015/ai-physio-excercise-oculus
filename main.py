import os
from dotenv import load_dotenv
from data_ingestion import IMUDataProcessor
from agents import AgentSystem
import json

def load_js_data(file_path):
    """Load data from a JavaScript file that starts with 'data='."""
    with open(file_path, "r") as f:
        content = f.read()
        # Extract the array part
        start = content.find("[")
        end = content.rfind("]")
        if start == -1 or end == -1:
            raise ValueError(f"Could not find array in {file_path}")
        
        # Get the array content
        array_content = content[start+1:end]
        
        # Split into individual JSON objects
        json_objects = []
        for line in array_content.split("\n"):
            line = line.strip()
            if line.startswith(","):
                line = line[1:]
            if line and not line.isspace():
                try:
                    obj = json.loads(line)
                    json_objects.append(obj)
                except json.JSONDecodeError:
                    continue
        
        return json_objects

def main():
    """Main function to process IMU data and generate exercise routines."""
    # Load environment variables
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY in .env file")

    print("Loading IMU data...")
    
    # Load IMU data from both hands
    left_hand_data = load_js_data("imu-data/left_updown.js")
    right_hand_data = load_js_data("imu-data/right_updown.js")
    
    # Combine data from both hands
    motion_data = {
        "timestamp": "2025-01-14T08:37:04",
        "left_hand": left_hand_data,
        "right_hand": right_hand_data
    }

    print("Initializing agent system...")
    agent_system = AgentSystem(openai_api_key)

    print("Setting up vector store...")
    agent_system.setup_vector_store()
    print("Saving vector store...")
    agent_system.vector_store.save_local("vector_store/imu_vectors")

    print("Processing motion data...")
    results = agent_system.process_motion_data(
        motion_data=json.dumps(motion_data)
    )

    print("Generating reports...")
    # Create exercise_summary.md
    with open("exercise_summary.md", "w") as f:
        f.write(results["exercise_summary"])

    # Create game_implementation.md
    with open("game_implementation.md", "w") as f:
        f.write(results["game_implementation"])

    print("Done! Reports have been generated in exercise_summary.md and game_implementation.md")

if __name__ == "__main__":
    main()

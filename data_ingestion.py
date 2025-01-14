import os
import json
from typing import List, Dict
import numpy as np
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding

class IMUDataProcessor:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.embed_model = OpenAIEmbedding()

    def load_imu_data(self) -> List[Dict]:
        """Load IMU data from files."""
        all_data = []
        
        # Get all .js files in the data directory
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.js'):
                file_path = os.path.join(self.data_dir, filename)
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Extract the array from the JavaScript file
                    # Remove 'data=' from the beginning
                    content = content.replace('data=', '').strip()
                    
                    # Split into lines and process each line
                    lines = content.split('\n')
                    json_lines = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith('['):
                            line = line[1:]  # Remove opening bracket
                        elif line.endswith(']'):
                            line = line[:-1]  # Remove closing bracket
                        
                        # Skip empty lines and lines with only commas
                        if line and not line.strip().startswith(','):
                            # Remove leading comma if present
                            if line.startswith(','):
                                line = line[1:].strip()
                            try:
                                data_point = json.loads(line)
                                json_lines.append(data_point)
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                continue
                    
                    all_data.extend(json_lines)
        
        return all_data

    def create_documents(self, imu_data: List[Dict]) -> List[Document]:
        """Create Document objects from IMU data."""
        documents = []
        
        for i, data_point in enumerate(imu_data):
            # Create a descriptive text representation of the IMU data
            text = f"""Motion data point {i}:
Position: Pitch={data_point['pos']['pitch']:.2f}°, Roll={data_point['pos']['roll']:.2f}°, Yaw={data_point['pos']['yaw']:.2f}°
Gyroscope: X={data_point['gyro']['x']:.2f}, Y={data_point['gyro']['y']:.2f}, Z={data_point['gyro']['z']:.2f}
Compass: X={data_point['compass']['x']:.2f}, Y={data_point['compass']['y']:.2f}, Z={data_point['compass']['z']:.2f}
Temperature: {data_point['temp']:.2f}°C"""
            
            # Create Document with metadata
            doc = Document(
                text=text,
                metadata={
                    "raw_data": data_point,
                    "timestamp": i,  # Using index as timestamp since actual timestamps aren't provided
                }
            )
            documents.append(doc)
        
        return documents

    def get_embeddings(self, documents: List[Document]) -> np.ndarray:
        """Generate embeddings for the documents using OpenAI."""
        embeddings = []
        
        for doc in documents:
            # Use OpenAI to get embeddings
            embedding = self.embed_model.get_text_embedding(doc.text)
            embeddings.append(embedding)
        
        return np.array(embeddings)

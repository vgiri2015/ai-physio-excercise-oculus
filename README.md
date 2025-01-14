# AI-Oculus IMU Data Processing System

This project implements an intelligent system for processing and analyzing IMU (Inertial Measurement Unit) data using LlamaIndex, LangGraph, and FAISS vector store. The system includes specialized agents for physiotherapy analysis, data analysis, and VR game design.

## Project Structure

- `data_ingestion.py`: Handles IMU data loading and processing using LlamaIndex
- `agents.py`: Implements specialized agents using LangGraph
- `main.py`: Main application that coordinates data processing and agent workflow
- `imu-data/`: Directory containing IMU data files

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Components

### Data Ingestion Layer
- Processes IMU data from JSON files
- Converts data into LlamaIndex documents
- Generates embeddings using OpenAI

### Agent Layer
- Physiotherapist Agent: Analyzes motion patterns and suggests exercises
- Data Analyst Agent: Detects trends and anomalies in motion data
- VR Game Designer Agent: Creates gamified exercise routines

### Vector Store
- Uses FAISS for efficient similarity search
- Stores IMU data embeddings for quick retrieval

## Usage

Run the main application:
```bash
python main.py
```

The system will:
1. Load and process IMU data
2. Initialize the agent system
3. Run the workflow through all agents
4. Output exercise suggestions, analysis results, and game design recommendations

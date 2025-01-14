from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from typing import List, Dict, TypedDict, Annotated
import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END, START

class AgentState(TypedDict):
    """State for the agent system."""
    motion_data: str
    analysis: str
    exercise_suggestions: str
    game_design: str
    exercise_routine: str
    exercise_summary: str
    game_implementation: str

class AgentSystem:
    def __init__(self, openai_api_key: str):
        """Initialize the agent system."""
        self.llm = ChatOpenAI(model="gpt-4", openai_api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = None
        self.workflow = self._create_workflow()

    def setup_vector_store(self):
        """Set up the vector store with embeddings."""
        self.vector_store = FAISS.from_texts(
            ["IMU data analysis system"], 
            self.embeddings
        )

    def _create_workflow(self) -> StateGraph:
        """Create the agent workflow using langgraph."""
        # Create the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes for each analysis step
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_exercises", self._generate_exercises)
        workflow.add_node("design_game", self._design_game)
        workflow.add_node("plan_routine", self._plan_routine)
        workflow.add_node("generate_report", self._generate_report)
        workflow.add_node("generate_implementation", self._generate_implementation)

        # Define the workflow edges
        workflow.add_edge(START, "analyze_data")
        workflow.add_edge("analyze_data", "generate_exercises")
        workflow.add_edge("generate_exercises", "design_game")
        workflow.add_edge("design_game", "plan_routine")
        workflow.add_edge("plan_routine", "generate_report")
        workflow.add_edge("generate_report", "generate_implementation")
        workflow.add_edge("generate_implementation", END)

        # Compile the workflow
        return workflow.compile()

    def _analyze_data(self, state: AgentState) -> AgentState:
        """Analyze motion data using data analyst chain."""
        chain = self.create_data_analyst_chain()
        state["analysis"] = chain.invoke({"motion_data": state["motion_data"]}).content
        return state

    def _generate_exercises(self, state: AgentState) -> AgentState:
        """Generate exercise suggestions using physiotherapist chain."""
        chain = self.create_physiotherapist_chain()
        state["exercise_suggestions"] = chain.invoke({"analysis": state["analysis"]}).content
        return state

    def _design_game(self, state: AgentState) -> AgentState:
        """Design game mechanics using game designer chain."""
        chain = self.create_game_designer_chain()
        state["game_design"] = chain.invoke({"exercise_suggestions": state["exercise_suggestions"]}).content
        return state

    def _plan_routine(self, state: AgentState) -> AgentState:
        """Plan exercise routine using exercise planner chain."""
        chain = self.create_exercise_planner_chain()
        state["exercise_routine"] = chain.invoke({
            "analysis": state["analysis"],
            "exercise_suggestions": state["exercise_suggestions"],
            "game_design": state["game_design"]
        }).content
        return state

    def _generate_report(self, state: AgentState) -> AgentState:
        """Generate exercise summary using report generator chain."""
        chain = self.create_report_generator_chain()
        state["exercise_summary"] = chain.invoke({
            "analysis": state["analysis"],
            "exercise_suggestions": state["exercise_suggestions"],
            "game_design": state["game_design"],
            "exercise_routine": state["exercise_routine"]
        }).content
        return state

    def _generate_implementation(self, state: AgentState) -> AgentState:
        """Generate implementation details using implementation chain."""
        chain = self.create_implementation_generator_chain()
        state["game_implementation"] = chain.invoke({
            "game_design": state["game_design"],
            "exercise_routine": state["exercise_routine"]
        }).content
        return state

    def process_motion_data(self, motion_data: str) -> Dict:
        """Process motion data through the agent workflow."""
        # Parse and sample the motion data
        data = json.loads(motion_data)
        sampled_data = {
            "timestamp": data["timestamp"],
            "left_hand": data["left_hand"][::10],
            "right_hand": data["right_hand"][::10]
        }

        # Initialize the workflow state
        initial_state: AgentState = {
            "motion_data": json.dumps(sampled_data),
            "analysis": "",
            "exercise_suggestions": "",
            "game_design": "",
            "exercise_routine": "",
            "exercise_summary": "",
            "game_implementation": ""
        }

        # Run the workflow
        final_state = self.workflow.invoke(initial_state)

        # Return the results
        return {
            "analysis": final_state["analysis"],
            "exercise_suggestions": final_state["exercise_suggestions"],
            "game_design": final_state["game_design"],
            "exercise_routine": final_state["exercise_routine"],
            "exercise_summary": final_state["exercise_summary"],
            "game_implementation": final_state["game_implementation"]
        }

    def create_data_analyst_chain(self):
        """Create a chain for motion data analysis."""
        template = """You are an AI Data Analyst specializing in IMU (Inertial Measurement Unit) data analysis for VR exercise applications. Analyze the following IMU data from both hands performing up-down movements:

{motion_data}

Focus your analysis on these specific aspects:

1. Bilateral Movement Analysis:
   - Compare the timing and synchronization between left and right hands
   - Analyze differences in range of motion between hands
   - Identify any asymmetries in movement patterns
   - Evaluate smoothness and consistency of up-down motions

2. Movement Parameters for Each Hand:
   - Range of motion in vertical direction (pitch)
   - Movement speed and acceleration patterns
   - Stability during movement (roll and yaw variations)
   - Movement rhythm and timing

3. Movement Quality Indicators:
   - Smoothness of acceleration/deceleration
   - Consistency of movement patterns
   - Presence of tremors or jerky movements
   - Coordination between hands

4. Specific Up-Down Motion Analysis:
   - Maximum and minimum heights reached
   - Time taken for upward vs downward movement
   - Pauses or holds at top/bottom positions
   - Variation in movement speed throughout range

Your analysis should:
1. Be quantitative where possible (include specific angles, speeds, timing differences)
2. Compare left vs right hand performance
3. Identify any potential issues or areas for improvement
4. Focus specifically on the vertical (up-down) movement patterns

Format your analysis as a clear, structured report with specific sections for each aspect analyzed."""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

    def create_physiotherapist_chain(self):
        """Create a chain for exercise recommendations."""
        template = """You are an AI Exercise Routine Planner specializing in VR-based rehabilitation and exercise programs. Based on the following motion analysis:

{analysis}

Create a comprehensive 10-day exercise routine that focuses on improving bilateral hand coordination and up-down movement patterns. Follow this EXACT format:

### Exercise Routine Table

| **Data Observed** | **Data Pattern** | **Phase** | **Exercise/Routine Name** | **Day Duration** | **VR Game Script** |
|-------------------|------------------|-----------|---------------------------|------------------|--------------------|
[Fill with one row per day, exactly 10 rows]

Guidelines for each column:

1. **Data Observed**:
   - Include specific IMU measurements (e.g., "Pitch range: 45°-80°")
   - Note bilateral differences (e.g., "Left hand lags by 0.2s")
   - Mention stability metrics (e.g., "Roll deviation: ±5°")

2. **Data Pattern**:
   - Describe movement characteristics (e.g., "Smooth acceleration, jerky deceleration")
   - Note timing patterns (e.g., "2s up, 1.5s down")
   - Highlight coordination aspects (e.g., "Asymmetric peak heights")

3. **Phase**:
   Choose from:
   - "Baseline Assessment"
   - "Coordination Training"
   - "Strength Building"
   - "Speed Development"
   - "Endurance Training"
   - "Recovery/Light"
   - "Advanced Integration"

4. **Exercise/Routine Name**:
   Create specific names like:
   - "Synchronized Hand Raises"
   - "Tempo-Based Lifts"
   - "Mirror Motion Training"
   - "Peak Hold Challenge"

5. **Day Duration**:
   - Specify exact minutes (20-45 range)
   - Include warm-up/cool-down
   - Account for rest periods

6. **VR Game Script**:
   Write detailed game mechanics:
   - Specific objectives (e.g., "Catch falling stars with both hands simultaneously")
   - Scoring system (e.g., "Points awarded for synchronization within 0.1s")
   - Progression rules (e.g., "Speed increases every 5 successful catches")
   - Visual/audio cues (e.g., "Glowing path shows optimal movement trajectory")

### Final Summary

[Write a detailed 1-paragraph summary describing:
- Key focus areas and progression strategy
- Expected improvements in coordination, strength, and speed
- Specific metrics for success (e.g., "Target: <0.1s hand synchronization")
- Recommendations for continued practice]

IMPORTANT:
1. MUST use EXACT table format
2. MUST create EXACTLY 10 rows
3. MUST include detailed game mechanics
4. MUST progress difficulty logically
5. MUST focus on bilateral coordination
6. MUST emphasize up-down movements
7. DO NOT add extra sections

Example Row:
| Pitch range: 45-80°, Left hand lags 0.2s | Smooth up (2s), jerky down (1.5s) | Coordination Training | Synchronized Star Catch | 25 minutes | Players catch falling stars, matching LED path timing. Score based on hand sync (<0.1s). Speed increases every 5 catches |"""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

    def create_game_designer_chain(self):
        """Create a chain for VR game design."""
        template = """You are an AI VR Game Designer specializing in therapeutic exercise games. Based on the following exercise recommendations:

{exercise_suggestions}

Design VR games that focus on:
1. Bilateral Coordination
   - Synchronized hand movements
   - Complementary actions
   - Hand-eye coordination

2. Exercise Integration
   - Natural movement patterns
   - Therapeutic progression
   - Form feedback

3. Engagement Mechanics
   - Achievement systems
   - Visual feedback
   - Progress tracking

4. Adaptive Difficulty
   - Dynamic scaling
   - Performance-based adjustments
   - Recovery periods

Design multiple game modes:
1. Rhythm Games
   - Synchronized hand movements
   - Timing-based challenges
   - Musical feedback

2. Object Manipulation
   - Grabbing and releasing
   - Transfer between hands
   - Spatial awareness

3. Pattern Matching
   - Mirror movements
   - Sequential actions
   - Memory challenges

4. Movement Flow
   - Continuous motion
   - Smooth transitions
   - Balance challenges

For each game mode, specify:
1. Core Mechanics:
   - Primary actions
   - Control schemes
   - Movement patterns

2. Progression System:
   - Difficulty levels
   - Unlock criteria
   - Achievement metrics

3. Feedback Systems:
   - Visual cues
   - Haptic feedback
   - Performance metrics

4. Technical Requirements:
   - Motion tracking
   - Hand synchronization
   - Form validation

Your design should create an engaging and therapeutically effective VR experience."""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

    def create_exercise_planner_chain(self):
        """Create a chain for exercise routine planning."""
        template = """You are an AI Exercise Routine Planner specializing in VR-based bilateral exercises. Create a comprehensive routine based on:

Analysis: {analysis}
Exercise Suggestions: {exercise_suggestions}
Game Design: {game_design}

Create a 10-day exercise program that focuses on:
1. Bilateral Coordination
   - Synchronized movements
   - Hand-eye coordination
   - Movement symmetry

2. Progressive Overload
   - Gradual intensity increase
   - Complexity progression
   - Duration adjustments

3. Exercise Variety
   - Different game modes
   - Movement patterns
   - Challenge types

4. Recovery Integration
   - Rest periods
   - Alternating focus
   - Deload sessions

Structure the program as follows:

## Week 1: Foundation
### Day 1-3: Basic Coordination
- Focus: Establishing movement patterns
- Game Modes: Rhythm and Pattern Matching
- Duration: 20-30 minutes

### Day 4-5: Movement Flow
- Focus: Smooth transitions
- Game Modes: Object Manipulation
- Duration: 25-35 minutes

## Week 2: Progression
### Day 6-8: Advanced Coordination
- Focus: Complex patterns
- Game Modes: All modes with increased difficulty
- Duration: 30-40 minutes

### Day 9-10: Performance
- Focus: Speed and accuracy
- Game Modes: Challenge modes
- Duration: 35-45 minutes

For each day, specify:
1. Warm-up routine
2. Main exercises
3. Cool-down activities
4. Progress tracking metrics

Include specific details about:
1. Exercise selection
2. Sets and repetitions
3. Rest periods
4. Form cues
5. Success criteria

Your routine should be progressive, engaging, and focused on improving bilateral coordination."""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

    def create_report_generator_chain(self):
        """Create a chain for generating reports."""
        template = """You are an AI Report Generator specializing in creating comprehensive exercise summaries. Based on the following information:

Analysis: {analysis}
Exercise Suggestions: {exercise_suggestions}
Game Design: {game_design}
Exercise Routine: {exercise_routine}

Create a detailed exercise summary in markdown format with the following structure:

# Exercise Program Summary

## Motion Analysis Overview
[Summarize key findings from the motion analysis, focusing on bilateral coordination and movement patterns]

## 10-Day Exercise Program

| Day | Data Observed | Data Pattern | Phase | Exercise/Routine Name | Day Duration | VR Game Script |
|-----|--------------|--------------|-------|---------------------|--------------|----------------|
| 1   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 2   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 3   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 4   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 5   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 6   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 7   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 8   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 9   | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |
| 10  | [Data] | [Pattern] | [Phase] | [Name] | [Duration] | [Script] |

Fill in the table with the exercise data, ensuring:
1. Each row represents one day of the program
2. All 10 days are included
3. Data is properly aligned in columns
4. Cells contain appropriate detailed information
5. Table formatting is preserved

## Progress Tracking
- Initial Metrics
- Target Metrics
- Success Criteria
- Progression Rules

## Exercise Instructions
[For each unique exercise/game, provide detailed instructions including:
- Setup and starting position
- Movement execution
- Common mistakes to avoid
- Progression indicators]

## Safety Guidelines
- Warm-up requirements
- Rest period recommendations
- Signs to watch for
- When to modify or stop

## Next Steps
[Include the physiotherapist's recommendations for continued practice and next phase]

IMPORTANT:
1. The table MUST include all 10 days
2. Each row MUST be properly aligned
3. All cells MUST contain appropriate detailed information
4. Table formatting MUST be preserved exactly as shown
5. DO NOT modify the column structure
6. DO NOT omit any days"""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

    def create_implementation_generator_chain(self):
        """Create a chain for generating implementation details."""
        template = """You are a VR development technical lead.
Create a comprehensive implementation guide for the VR exercise game in markdown format.

Game Design: {game_design}
Exercise Routine: {exercise_routine}

Include detailed sections on:

1. System Requirements
- Hardware specifications
- Software dependencies
- Development environment setup

2. Game Mechanics Implementation
- Core mechanics for each exercise
- Input handling approach
- Motion tracking requirements
- Scoring system design
- Progression logic
- Visual/audio feedback

3. Data Processing Pipeline
- IMU data collection
- Motion analysis algorithms
- Performance metrics

4. User Interface Design
- Menu structure
- Exercise selection interface
- Progress tracking displays
- Visual feedback elements

5. Testing Procedures
- Unit testing approach
- Integration testing plan
- User testing protocol
- Performance benchmarks

6. Game Implementation Details
Create a detailed table with implementation specifics for each game mode:

| Game Mode | Core Mechanics | Input Requirements | Scoring Logic | Progression System | Technical Requirements |
|-----------|---------------|-------------------|---------------|-------------------|----------------------|
[Fill with game modes from Game Design]

7. Deployment Guidelines
- Build process
- Platform-specific considerations
- Quality assurance checklist
- Maintenance considerations"""

        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm

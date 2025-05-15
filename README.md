# JAY.AI - Personal Growth Assistant 🚀

## Overview
JAY.AI is an intelligent personal growth assistant that combines specialized AI agents with a comprehensive growth tracking system. It delivers wisdom, creative assistance, and personalized development plans using a unique, engaging communication style.

## System Architecture 🏗️

JAY.AI consists of three core components:

1. **Agent System** - Specialized AI agents with distinct expertise areas
2. **Growth Engine** - Comprehensive personal development tracking system
3. **Interaction Management** - Conversation handling and user session management

### Key Components

#### 1. Growth Engine 📈

The `GrowthEngine` class manages user growth across 8 life domains:
- Cognitive, Creative, Physical, Emotional
- Social, Professional, Financial, Spiritual

Features:
- XP and leveling mechanics for each domain
- Streak tracking for consistency (3, 7, 14, 30-day milestones)
- Goal management with progress tracking
- Personalized challenges based on user's profile
- Insight generation from growth patterns

```python
# Core data structure for user growth
self.growth_data = {
    "users": {
        "user_id": {
            "domains": {domain: {"level": 1, "xp": 0} for domain in self.growth_domains},
            "streaks": {"current": 0, "longest": 0, "last_activity": None},
            "activity_log": []
        }
    }
}
```

#### 2. JAY Agent System 🤖

The `JAYAgent` class extends the AWS BedrockLLMAgent with:
- Personality traits and custom language style
- Context-aware processing
- Domain-specific expertise
- Collaboration capabilities

Agent types:
- Wisdom, Creative, Tech, Research
- Strategy, Wellness, Relationship, Financial

```python
# Example of specialized agent processing
async def process_with_context(self, user_input, user_id, session_id, agent_type):
    # Get conversation history and user growth profile
    # Apply personality traits and language style
    # Process input and track growth
```

#### 3. Collaboration System 🤝

Enables multiple agents to work together through:
- General collaboration for complex queries
- Specialized collaboration patterns:
  - Life Planning (Strategy + Wisdom + Wellness)
  - Business Ventures (Strategy + Financial + Tech)
  - Personal Growth (Wisdom + Wellness + Relationship)
  - Creative Projects (Creative + Tech + Strategy)
  - Financial Wellness (Financial + Wellness + Wisdom)

```python
# Collaboration detection
if any(keyword in user_input.lower() for keyword in ["complex", "collaborate", "team"]):
    # Route to collaborative processing
```

## Data Flow Diagram

```
User Input → Agent Routing → Processing → Response
     ↑                         ↓
     └─── Growth Engine ←── Activity Logging
```

## Key Features ✨

1. **Personalized Growth Plans** - Tailored development plans based on user's current levels

2. **Challenge System** - Adaptive challenges targeting growth areas

3. **Goal Tracking** - Milestone-based goal management with progress visualization

4. **Streak Mechanics** - Consistency tracking with achievement levels

5. **Multi-Agent Collaboration** - Combined expertise for complex problems

6. **Growth Analytics** - Pattern identification and personalized insights

7. **Natural Language Style** - Engaging, authentic communication style

## Persistence

JAY.AI maintains several data stores:
- `jay_growth_data.json` - Domain levels, XP, streaks
- `jay_user_goals.json` - Goal tracking and progress
- `jay_user_insights.json` - Generated insights and recommendations
- `jay_history.json` - Interaction history
- `jay_sessions.txt` - Session logs

## AWS Integration 🔄

JAY.AI leverages AWS services:
- **Bedrock Runtime** - Hosts Claude 3 Sonnet models
- **Agent Squad** - Orchestrates multiple agent interactions

```python
bedrock_client = boto3.client('bedrock-runtime', config=Config(
    connect_timeout=300,
    read_timeout=300,
    retries={'max_attempts': 3}
))
```

## Extension Points 🔌

JAY.AI can be extended through:
1. Adding new specialized agents
2. Creating additional collaboration patterns
3. Expanding growth domains
4. Adding new visualization methods
5. Implementing external integrations (calendars, task managers)

## Setup and Installation

### Prerequisites
- Python 3.8+
- AWS account with Bedrock access
- Agent Squad library

### Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure AWS credentials
4. Run the application: `python src/jay_ai.py`

## Usage

```
python src/jay_ai.py
```

The application provides a text-based interface with the following options:
- Life Wisdom
- Creative Assistance
- Personal Challenges
- Growth Dashboard
- and more...

## License
[MIT License](LICENSE) 
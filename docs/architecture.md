# JAY.AI System Architecture 🏗️

This document provides a detailed explanation of JAY.AI's architecture, components, and data flows.

## System Components

### 1. Agent System

The agent system is built on AWS Bedrock's Claude models, organized into specialized domains:

```
AgentSquad
├── Tech Agent
├── Creative Agent
├── Wisdom Agent
├── Research Agent
├── Strategy Agent
├── Wellness Agent
├── Relationship Agent
└── Financial Agent
```

Each agent is implemented as a custom `JAYAgent` class that extends the base `BedrockLLMAgent` class from the Agent Squad library.

#### JAYAgent Class

The `JAYAgent` class adds several enhancements to the base agent:

1. **Personality System**
   - Each agent has defined personality traits
   - Custom prompt templates establish a consistent voice
   - Natural language style maintains the JAY.AI brand

2. **Context Management**
   - Conversation history integration
   - Growth profile data incorporation
   - Dynamic prompt construction

3. **Specialized Methods**
   - `generate_personalized_growth_plan()`
   - `generate_challenge()`
   - `analyze_user_growth()`
   - `generate_rap_verse()`

4. **Collaboration Capabilities**
   - Two-pass collaboration process
   - Specialized collaboration patterns
   - Cross-domain expertise integration

### 2. Growth Engine

The `GrowthEngine` class provides a comprehensive personal development tracking system:

```
GrowthEngine
├── Domain Tracking
│   ├── XP Calculation
│   └── Level Progression
├── Streak Management
├── Goal System
├── Challenge Generation
└── Insight Creation
```

#### Growth Domains

Each user has progress tracked across 8 core domains:

| Domain      | Description                                    |
|-------------|------------------------------------------------|
| Cognitive   | Mental abilities, learning, problem-solving    |
| Creative    | Artistic expression, innovation                |
| Physical    | Health, fitness, physical well-being           |
| Emotional   | Emotional intelligence, regulation             |
| Social      | Relationships, communication                   |
| Professional| Career growth, skills, achievements            |
| Financial   | Money management, investments                  |
| Spiritual   | Purpose, meaning, values alignment             |

#### Data Management

The Growth Engine maintains several data stores:
- User growth data (levels, XP, streaks)
- Goals (active, completed, abandoned)
- Insights (recommendations, achievements)
- Activity logs (interaction history)

### 3. Interaction Management

The interaction system handles:
- User authentication
- Session management
- Conversation context
- Menu navigation
- Response formatting

## Data Flow

### 1. User Input Processing

```
User Input → Menu System → Agent Routing → Specialized Processing → Response
```

### 2. Growth Data Flow

```
User Action → Activity Logging → Domain XP Update → Level Check → Insight Generation
```

### 3. Collaboration Flow

```
Complex Query → Agent Selection → Perspective Collection → Synthesis → Response
```

## Extension Architecture

JAY.AI is designed for extension through:

1. **New Agents** - Add new domain expertise by creating new agents
2. **New Domains** - Expand growth tracking with additional life domains
3. **New Collaboration Patterns** - Define new specialized agent combinations
4. **New Visualization Methods** - Add ways to represent growth data
5. **External Integrations** - Connect with other services and APIs

## AWS Integration Details

JAY.AI relies on several AWS services:

1. **Bedrock Runtime**
   - Claude 3 Sonnet model hosting
   - Natural language processing
   - Context management

2. **Agent Squad**
   - Agent organization
   - Collaboration facilitation
   - Request routing

## Performance Considerations

- **Response Time** - Optimized with efficient prompt design
- **Memory Usage** - Managed by selective context inclusion
- **Storage** - File-based for simplicity, can be extended to databases

## Security Architecture

- **Authentication** - Basic username/password system
- **Data Isolation** - User data is stored separately
- **AWS Security** - Leverages AWS security best practices 
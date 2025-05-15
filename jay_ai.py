"""
JAY.AI - An Interactive AI Assistant

This program creates an interactive AI assistant named JAY.AI that provides:
- Life wisdom and advice
- Creative writing and rap assistance
- Personal challenges and motivation
- Session tracking and history
- User authentication and conversation management

The program maintains several types of persistent storage:
- jay_history.json: Stores user interaction history
- jay_sessions.txt: Logs detailed session information
- users.json: Stores user authentication data
- conversations.json: Stores conversation threads
"""

import random
import json
import os
import uuid
import sys
from datetime import datetime, timedelta
import asyncio
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from agent_squad.orchestrator import AgentSquad
from agent_squad.agents import BedrockLLMAgent, BedrockLLMAgentOptions, AgentStreamResponse
import ai21
from ai21.models import Janus
from auth import UserAuth
from context import ContextManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# File paths for persistent storage
HISTORY_FILE = "jay_history.json"
SESSION_LOG_FILE = "jay_sessions.txt"
GROWTH_DATA_FILE = "jay_growth_data.json"
USER_GOALS_FILE = "jay_user_goals.json"
USER_INSIGHTS_FILE = "jay_user_insights.json"

# Initialize authentication and context management
auth_manager = UserAuth()
context_manager = ContextManager()

class GrowthEngine:
    """
    Integrated growth system that combines multiple high-impact features:
    - User growth tracking and insights across multiple life domains
    - Goal management and achievement pathways with milestone tracking
    - Personalized challenge systems with adaptive difficulty
    - Data-driven insights and recommendations based on user patterns
    - Streak and consistency tracking for habit formation
    
    The GrowthEngine maintains several persistent data stores:
    - growth_data: User domain levels, XP, streaks, and activity logs
    - user_goals: Active, completed and abandoned goals with progress tracking
    - user_insights: Generated insights and recommendations
    
    Each user has growth tracked across 8 core life domains:
    - cognitive: Mental abilities, learning, problem-solving
    - creative: Artistic expression, innovation, imagination
    - physical: Health, fitness, physical well-being
    - emotional: Emotional intelligence, regulation, awareness
    - social: Relationships, communication, social skills
    - professional: Career growth, skills, achievements
    - financial: Money management, investments, financial health
    - spiritual: Purpose, meaning, values alignment
    """
    def __init__(self):
        # Load persistence data with defaults if files don't exist
        self.growth_data = self._load_data(GROWTH_DATA_FILE, {"users": {}})
        self.user_goals = self._load_data(USER_GOALS_FILE, {"users": {}})
        self.user_insights = self._load_data(USER_INSIGHTS_FILE, {"users": {}})
        
        # Define the core growth domains that are tracked for each user
        self.growth_domains = [
            "cognitive", "creative", "physical", "emotional",
            "social", "professional", "financial", "spiritual"
        ]
        
        # Streak thresholds define levels of consistency achievement
        # Used to recognize and reward continued engagement
        self.streak_thresholds = {
            "beginner": 3,     # 3 consecutive days of activity
            "consistent": 7,   # 1 week of daily activity
            "committed": 14,   # 2 weeks of daily activity
            "master": 30       # 1 month of daily activity
        }
        
    def _load_data(self, file_path, default_data):
        """
        Load data from persistent storage file or return default if file doesn't exist.
        
        Args:
            file_path (str): Path to the data file
            default_data (dict): Default data structure to return if file doesn't exist
            
        Returns:
            dict: Loaded data or default structure
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default_data
        except Exception as e:
            print(f"Error loading data from {file_path}: {str(e)}")
            return default_data
            
    def _save_data(self, file_path, data):
        """
        Save data to persistent storage file.
        
        Args:
            file_path (str): Path to the data file
            data (dict): Data to save
            
        Returns:
            None
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data to {file_path}: {str(e)}")
    
    def initialize_user(self, user_id, username):
        """
        Initialize a new user in the growth system with default values.
        Sets up domain tracking, streak counting, and goal structures.
        
        Args:
            user_id (str): Unique identifier for the user
            username (str): User's display name
            
        Returns:
            None
        """
        # Initialize growth data if user doesn't exist
        if user_id not in self.growth_data["users"]:
            # Create default structure for new user with level 1 in all domains
            self.growth_data["users"][user_id] = {
                "username": username,
                "domains": {domain: {"level": 1, "xp": 0, "challenges_completed": 0} for domain in self.growth_domains},
                "streaks": {"current": 0, "longest": 0, "last_activity": None},
                "insights": [],
                "activity_log": []
            }
            self._save_data(GROWTH_DATA_FILE, self.growth_data)
            
        # Initialize goals structure if user doesn't exist
        if user_id not in self.user_goals["users"]:
            self.user_goals["users"][user_id] = {
                "active_goals": [],      # In-progress goals
                "completed_goals": [],   # Successfully achieved goals
                "abandoned_goals": []    # Goals explicitly abandoned or failed
            }
            self._save_data(USER_GOALS_FILE, self.user_goals)
    
    def log_activity(self, user_id, activity_type, domains, description):
        """
        Log user activity and update growth metrics including:
        - XP gains in relevant domains
        - Level progression when XP thresholds are reached
        - Streak maintenance and tracking
        - Insight generation on significant events
        
        Args:
            user_id (str): Unique identifier for the user
            activity_type (str): Category of activity (e.g., "wisdom_interaction")
            domains (list): List of domains affected by this activity
            description (str): Description of the activity
            
        Returns:
            bool: Success indicator
        """
        if user_id not in self.growth_data["users"]:
            return False
            
        user_data = self.growth_data["users"][user_id]
        timestamp = datetime.now().isoformat()
        
        # Log the activity in user history
        user_data["activity_log"].append({
            "type": activity_type,
            "domains": domains,
            "description": description,
            "timestamp": timestamp
        })
        
        # Update domain XP and check for level ups
        xp_gain = 10  # Base XP gain per activity
        for domain in domains:
            if domain in user_data["domains"]:
                # Add XP to the domain
                user_data["domains"][domain]["xp"] += xp_gain
                
                # Check for level up - each level requires level*100 XP
                current_level = user_data["domains"][domain]["level"]
                xp_needed = current_level * 100
                
                # Level up when XP threshold is reached
                if user_data["domains"][domain]["xp"] >= xp_needed:
                    user_data["domains"][domain]["level"] += 1
                    user_data["domains"][domain]["xp"] -= xp_needed
                    
                    # Generate insight notification for level up achievement
                    self.add_insight(user_id, "level_up", f"You've reached level {current_level + 1} in {domain}!")
        
        # Update streaks - critical for consistency tracking and motivation
        today = datetime.now().date()
        if user_data["streaks"]["last_activity"]:
            last_date = datetime.fromisoformat(user_data["streaks"]["last_activity"]).date()
            if today - last_date == timedelta(days=1):
                # Activity on consecutive day - increment streak
                user_data["streaks"]["current"] += 1
                if user_data["streaks"]["current"] > user_data["streaks"]["longest"]:
                    user_data["streaks"]["longest"] = user_data["streaks"]["current"]
                    
                # Check for streak milestone achievements
                for level, days in self.streak_thresholds.items():
                    if user_data["streaks"]["current"] == days:
                        self.add_insight(user_id, "streak", f"You've achieved {level} status with a {days}-day streak!")
                        
            elif today - last_date > timedelta(days=1):
                # Streak broken - reset to 1 for today's activity
                user_data["streaks"]["current"] = 1
            # If same day, don't modify streak counter (already counted today)
        else:
            # First activity ever - start streak at 1
            user_data["streaks"]["current"] = 1
            
        # Update last activity timestamp
        user_data["streaks"]["last_activity"] = timestamp
        self._save_data(GROWTH_DATA_FILE, self.growth_data)
        return True
    
    def create_goal(self, user_id, title, description, domain, target_date, milestones=None):
        """
        Create a new user goal with tracking parameters.
        
        Args:
            user_id (str): Unique identifier for the user
            title (str): Short title for the goal
            description (str): Detailed description of the goal
            domain (str): Primary domain this goal belongs to
            target_date (str): ISO-formatted date string for goal completion
            milestones (list, optional): List of milestone dictionaries
            
        Returns:
            str: Generated goal ID or False if failed
        """
        if user_id not in self.user_goals["users"]:
            return False
            
        # Generate unique ID for the goal
        goal_id = str(uuid.uuid4())
        
        # Create goal structure
        new_goal = {
            "id": goal_id,
            "title": title,
            "description": description,
            "domain": domain,
            "created_at": datetime.now().isoformat(),
            "target_date": target_date,
            "completed": False,
            "progress": 0,  # 0-100 percentage
            "milestones": milestones or []
        }
        
        # Add to active goals
        self.user_goals["users"][user_id]["active_goals"].append(new_goal)
        self._save_data(USER_GOALS_FILE, self.user_goals)
        
        # Log goal creation as activity for XP and tracking
        self.log_activity(user_id, "goal_created", [domain], f"Created goal: {title}")
        
        return goal_id
    
    def update_goal_progress(self, user_id, goal_id, progress, completed_milestones=None):
        """
        Update a goal's progress percentage and milestone completion.
        If progress reaches 100%, the goal is moved to completed goals.
        
        Args:
            user_id (str): Unique identifier for the user
            goal_id (str): Unique identifier for the goal
            progress (int): New progress percentage (0-100)
            completed_milestones (list, optional): List of milestone IDs completed
            
        Returns:
            bool: Success indicator
        """
        if user_id not in self.user_goals["users"]:
            return False
            
        user_goals = self.user_goals["users"][user_id]
        
        # Find the goal in active goals
        for goal in user_goals["active_goals"]:
            if goal["id"] == goal_id:
                old_progress = goal["progress"]
                goal["progress"] = min(100, progress)  # Cap at 100%
                
                # Update milestones if provided
                if completed_milestones:
                    for milestone in goal["milestones"]:
                        if milestone["id"] in completed_milestones and not milestone.get("completed"):
                            milestone["completed"] = True
                            milestone["completed_at"] = datetime.now().isoformat()
                
                # Check if goal is now complete (100%)
                if progress >= 100:
                    goal["completed"] = True
                    goal["completed_at"] = datetime.now().isoformat()
                    
                    # Move from active to completed goals
                    user_goals["completed_goals"].append(goal)
                    user_goals["active_goals"] = [g for g in user_goals["active_goals"] if g["id"] != goal_id]
                    
                    # Log completion as activity and create achievement insight
                    self.log_activity(user_id, "goal_completed", [goal["domain"]], f"Completed goal: {goal['title']}")
                    self.add_insight(user_id, "achievement", f"You've achieved your goal: {goal['title']}!")
                else:
                    # Log progress update for incremental progress
                    progress_gain = progress - old_progress
                    if progress_gain > 0:
                        self.log_activity(user_id, "goal_progress", [goal["domain"]], 
                                         f"Made {progress_gain}% progress on goal: {goal['title']}")
                
                self._save_data(USER_GOALS_FILE, self.user_goals)
                return True
                
        return False
    
    def add_insight(self, user_id, insight_type, content, domains=None):
        """
        Add an insight for the user - used for achievements, recommendations,
        pattern recognition, and other significant observations.
        
        Args:
            user_id (str): Unique identifier for the user
            insight_type (str): Category of insight (level_up, streak, achievement, etc.)
            content (str): The insight message content
            domains (list, optional): List of domains this insight relates to
            
        Returns:
            str: Generated insight ID
        """
        if user_id not in self.user_insights["users"]:
            self.user_insights["users"][user_id] = {"insights": []}
            
        # Create insight structure
        insight = {
            "id": str(uuid.uuid4()),
            "type": insight_type,
            "content": content,
            "domains": domains or [],
            "created_at": datetime.now().isoformat(),
            "viewed": False  # Track if user has seen this insight
        }
        
        self.user_insights["users"][user_id]["insights"].append(insight)
        self._save_data(USER_INSIGHTS_FILE, self.user_insights)
        return insight["id"]
    
    def get_user_profile(self, user_id):
        """
        Get a comprehensive user growth profile including:
        - Domain levels and XP
        - Streak information
        - Active goals
        - Unviewed insights
        - Recent activities
        
        This serves as the central method for accessing user growth data.
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            dict: User profile data or None if user not found
        """
        if user_id not in self.growth_data["users"]:
            return None
            
        user_data = self.growth_data["users"][user_id]
        
        # Get active goals from goals data store
        active_goals = [] if user_id not in self.user_goals["users"] else self.user_goals["users"][user_id]["active_goals"]
        
        # Get unviewed insights for notification
        unviewed_insights = []
        if user_id in self.user_insights["users"]:
            unviewed_insights = [i for i in self.user_insights["users"][user_id]["insights"] if not i["viewed"]]
            
        # Calculate growth metrics for overview
        total_level = sum(domain["level"] for domain in user_data["domains"].values())
        avg_level = total_level / len(user_data["domains"])
        highest_domain = max(user_data["domains"].items(), key=lambda x: x[1]["level"])
        
        # Get recent activities for context
        recent_activities = sorted(user_data["activity_log"], key=lambda x: x["timestamp"], reverse=True)[:10]
        
        # Compile comprehensive profile
        return {
            "username": user_data["username"],
            "domains": user_data["domains"],
            "total_level": total_level,
            "average_level": avg_level,
            "highest_domain": highest_domain[0],
            "streak": user_data["streaks"]["current"],
            "longest_streak": user_data["streaks"]["longest"],
            "active_goals": active_goals,
            "unviewed_insights": unviewed_insights,
            "recent_activities": recent_activities
        }
    
    def get_personalized_challenges(self, user_id, count=3):
        """
        Generate personalized challenges based on user profile.
        Challenges focus on domains with lower levels to encourage balanced growth,
        and also include streak-based challenges for consistency.
        
        Args:
            user_id (str): Unique identifier for the user
            count (int): Number of challenges to generate
            
        Returns:
            list: List of challenge dictionaries
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return []
            
        challenges = []
        
        # Look for domains with lower levels to encourage balanced growth
        domain_levels = [(domain, data["level"]) for domain, data in profile["domains"].items()]
        domain_levels.sort(key=lambda x: x[1])  # Sort by level, lowest first
        
        # Generate challenges for lowest domains to promote balance
        for domain, level in domain_levels[:3]:
            challenge = {
                "id": str(uuid.uuid4()),
                "domain": domain,
                "level": level,
                "title": f"Level up your {domain} growth",
                "description": f"This challenge will help you improve in the {domain} domain where you're currently level {level}."
            }
            challenges.append(challenge)
            
        # Add streak-based challenge if applicable
        current_streak = profile["streak"]
        if current_streak > 0:
            # Find next streak threshold to aim for
            next_threshold = None
            for level, days in self.streak_thresholds.items():
                if current_streak < days:
                    next_threshold = days
                    break
                    
            if next_threshold:
                days_needed = next_threshold - current_streak
                challenges.append({
                    "id": str(uuid.uuid4()),
                    "domain": "consistency",
                    "title": f"Reach a {next_threshold}-day streak",
                    "description": f"You're on a {current_streak}-day streak! Keep it going for {days_needed} more days to reach the next level."
                })
        
        return challenges[:count]  # Return requested number of challenges

# Initialize growth engine
growth_engine = GrowthEngine()

class JAYAgent(BedrockLLMAgent):
    """
    Custom agent class that extends BedrockLLMAgent with JAY.AI specific functionality.
    
    The JAYAgent enhances the standard BedrockLLMAgent with:
    - Personality traits and natural language customization
    - Growth engine integration for personal development tracking
    - Context-aware processing with conversation history
    - Specialized methods for domain-specific tasks
    - Collaboration capabilities with other agents
    - Personalized challenge and growth plan generation
    
    Each agent maintains its own personality traits, domain mappings, and prompt templates
    while sharing the underlying LLM capabilities of the BedrockLLMAgent.
    """
    def __init__(self, options: BedrockLLMAgentOptions, context_manager: ContextManager):
        """
        Initialize a JAYAgent with custom personality and capabilities.
        
        Args:
            options: Configuration options for the BedrockLLMAgent
            context_manager: Manager for conversation context and history
        """
        # Initialize the base BedrockLLMAgent with provided options
        super().__init__(options)
        
        # Store reference to context manager for conversation history
        self.context_manager = context_manager
        
        # Define personality traits for different agent types
        # These influence tone, style, and approach in responses
        self.personality_traits = {
            "wisdom": "wise, philosophical, and insightful",
            "creative": "artistic, expressive, and innovative",
            "tech": "analytical, precise, and solution-oriented",
            "research": "thorough, detail-oriented, and investigative",
            "strategy": "strategic, forward-thinking, and execution-focused",
            "wellness": "nurturing, supportive, and health-conscious",
            "relationship": "empathetic, understanding, and socially aware",
            "financial": "prudent, strategic, and growth-oriented"
        }
        
        # Map agent types to growth domains for activity tracking
        # This enables integration with the growth engine
        self.domain_mapping = {
            "wisdom": ["cognitive", "spiritual"],
            "creative": ["creative"],
            "tech": ["cognitive", "professional"],
            "research": ["cognitive"],
            "strategy": ["cognitive", "professional"],
            "wellness": ["physical", "emotional"],
            "relationship": ["social", "emotional"],
            "financial": ["financial", "professional"]
        }
        
        # Storage for collaboration history in multi-agent scenarios
        self.collaboration_history = []
        
        # Define custom prompt templates for each agent type
        # These establish the agent's voice and style in responses
        self.prompt_templates = {
            "wisdom": """Yo, what's good? I'm here to drop some wisdom on you, King. 
            Let's keep it real and keep it moving. What's on your mind?
            
            Remember: I'm all about that authentic, real talk. No fluff, just straight wisdom.""",
            
            "creative": """Aight, let's get creative! I'm here to help you express yourself, 
            whether it's through bars, writing, or any other creative flow.
            
            Remember: Creativity is about being authentic and true to yourself.""",
            
            "tech": """What's up with the tech world? I'm here to break down the complex stuff 
            into something you can actually use. Let's make tech work for you, not the other way around.
            
            Remember: Tech should serve your goals, not complicate them.""",
            
            "research": """Let's dig deep and get to the bottom of this. I'm here to help you 
            understand the facts and make informed decisions.
            
            Remember: Knowledge is power, but only if you know how to use it.""",
            
            "strategy": """Time to level up your game plan. I'm here to help you think ahead 
            and make moves that count. Let's turn your vision into reality.
            
            Remember: Strategy is about making smart moves, not just working hard.""",
            
            "wellness": """Let's talk about taking care of yourself, King. Your mind, body, 
            and spirit all need that love. What's your wellness focus today?
            
            Remember: Self-care isn't selfish, it's essential.""",
            
            "relationship": """Relationships are the real wealth in life. Let's talk about 
            how to build and maintain the connections that matter.
            
            Remember: Every relationship is a two-way street.""",
            
            "financial": """Let's talk about building that wealth, King. Money is a tool, 
            and I'm here to help you use it wisely.
            
            Remember: Financial freedom starts with smart decisions."""
        }
        
    async def process_with_context(self, user_input: str, user_id: str, session_id: str, agent_type: str) -> str:
        """
        Process user input with context awareness and personality.
        
        This method enhances standard LLM processing by:
        1. Retrieving conversation history for context
        2. Adding user growth profile data for personalization
        3. Applying appropriate personality traits and language style
        4. Logging interactions to the growth engine
        
        Args:
            user_input: The user's message or query
            user_id: Unique identifier for the user
            session_id: Identifier for the current session
            agent_type: Type of agent processing the request
            
        Returns:
            str: Agent's response including context and personality
        """
        # Get conversation history from context manager
        conv_id = self.context_manager.get_active_conversation(user_id)
        history = self.context_manager.get_conversation_history(conv_id)
        
        # Get user growth profile for personalization
        user_profile = growth_engine.get_user_profile(user_id)
        profile_context = ""
        
        # Add relevant growth data to the prompt if available
        if user_profile:
            # Add relevant growth context
            profile_context = f"""
            User Growth Context:
            - Current streak: {user_profile['streak']} days
            - Highest domain: {user_profile['highest_domain']} (Level {user_profile['domains'][user_profile['highest_domain']]['level']})
            - Recent activities: {', '.join([a['type'] for a in user_profile['recent_activities'][:3]])}
            """
            
            # Add unviewed insights if available for notification
            if user_profile['unviewed_insights']:
                insights = [i['content'] for i in user_profile['unviewed_insights'][:2]]
                profile_context += f"\nRecent insights: {', '.join(insights)}"
        
        # Build personality-infused prompt
        personality = self.personality_traits.get(agent_type, "helpful and engaging")
        base_prompt = self.prompt_templates.get(agent_type, "What's good? Let's figure this out together.")
        
        # Construct the full system prompt with all contextual elements
        system_prompt = f"""You are JAY.AI, an AI assistant with a {personality} personality.
        You maintain a casual, friendly tone while being professional.
        You have access to the following conversation history:
        {history}
        
        {profile_context}
        
        {base_prompt}
        
        Please respond to the user's input while maintaining your personality and considering the context.
        Keep your language natural, engaging, and authentic to the JAY.AI style."""
        
        # Process with context using the base BedrockLLM capabilities
        response = await self.process(user_input, system_prompt)
        
        # Log the interaction to the growth engine for tracking progress
        if agent_type in self.domain_mapping:
            growth_engine.log_activity(
                user_id, 
                f"{agent_type}_interaction", 
                self.domain_mapping[agent_type], 
                f"Interacted with {agent_type} agent: {user_input[:50]}..."
            )
        
        return response

    async def generate_personalized_growth_plan(self, user_id: str, focus_area: str, timeframe: str) -> str:
        """
        Generate a personalized growth plan based on user's profile and focus area.
        
        This method uses the user's growth profile data to create a customized
        development plan that focuses on specific areas while considering their
        current progress and level in relevant domains.
        
        Args:
            user_id: Unique identifier for the user
            focus_area: Primary area of focus for the plan
            timeframe: Time period for the plan (e.g., "1 week", "1 month")
            
        Returns:
            str: Personalized growth plan
        """
        # Get user profile for personalization
        profile = growth_engine.get_user_profile(user_id)
        if not profile:
            return "I need more information about your growth journey before creating a personalized plan."
            
        # Map focus area to relevant growth domains
        relevant_domains = []
        if focus_area.lower() in ["mind", "mental", "intellectual", "thinking"]:
            relevant_domains = ["cognitive", "spiritual"]
        elif focus_area.lower() in ["body", "physical", "health", "fitness"]:
            relevant_domains = ["physical", "wellness"]
        elif focus_area.lower() in ["career", "professional", "work", "job"]:
            relevant_domains = ["professional", "cognitive", "financial"]
        elif focus_area.lower() in ["social", "relationships", "friends", "family"]:
            relevant_domains = ["social", "emotional", "relationship"]
        elif focus_area.lower() in ["finance", "money", "wealth", "financial"]:
            relevant_domains = ["financial"]
        elif focus_area.lower() in ["creative", "art", "music", "writing"]:
            relevant_domains = ["creative"]
        else:
            # Default to holistic plan covering all domains
            relevant_domains = list(profile["domains"].keys())
            
        # Get current level in each relevant domain for context
        domain_levels = {d: profile["domains"].get(d, {"level": 1})["level"] for d in relevant_domains if d in profile["domains"]}
        
        # Generate personalized prompt with domain info
        domain_info = ", ".join([f"{d} (Level {level})" for d, level in domain_levels.items()])
        
        # Construct detailed system prompt for plan generation
        system_prompt = f"""You're creating a personalized growth plan for a user with the following profile:
        - Focus area: {focus_area}
        - Timeframe: {timeframe}
        - Relevant domains: {domain_info}
        - Current streak: {profile['streak']} days
        
        Create a personalized growth plan that:
        1. Is tailored to their current level in each domain
        2. Focuses on {focus_area} as the primary area
        3. Includes specific, actionable steps
        4. Has measurable milestones for the {timeframe} timeframe
        5. Builds on their strengths while addressing growth areas
        
        The plan should be motivational, achievable, and authentic to JAY.AI's style."""
        
        # Generate the plan
        response = await self.process(f"Create a personalized {focus_area} growth plan for {timeframe}", system_prompt)
        
        # Log this as a significant activity in the growth engine
        growth_engine.log_activity(
            user_id,
            "growth_plan_creation",
            relevant_domains,
            f"Created personalized growth plan focusing on {focus_area} for {timeframe}"
        )
        
        return response
        
    async def generate_challenge(self, user_input: str, user_id: str, difficulty: str = "medium") -> str:
        """
        Generate a personalized challenge based on user input and difficulty level.
        
        This method creates challenges that are tailored to the user's current
        growth profile, taking into account their strengths and areas for improvement.
        The challenge is also tracked in the growth engine.
        
        Args:
            user_input: Basis for challenge generation
            user_id: Unique identifier for the user
            difficulty: Challenge difficulty level
            
        Returns:
            str: Personalized challenge
        """
        # Get user profile for personalization
        profile = growth_engine.get_user_profile(user_id)
        profile_context = ""
        
        # Add relevant growth data to the challenge generation prompt
        if profile:
            # Identify strengths and opportunities based on domain levels
            domain_levels = {d: data["level"] for d, data in profile["domains"].items()}
            strongest_domain = max(domain_levels.items(), key=lambda x: x[1])[0]
            weakest_domain = min(domain_levels.items(), key=lambda x: x[1])[0]
            
            # Create context string for the prompt
            profile_context = f"""
            User strengths: {strongest_domain} (Level {domain_levels[strongest_domain]})
            Growth opportunity: {weakest_domain} (Level {domain_levels[weakest_domain]})
            Current streak: {profile['streak']} days
            """
        
        # Build challenge generation prompt
        system_prompt = f"""Generate a {difficulty} difficulty challenge that:
        1. Is relevant to the user's input
        2. Is achievable but requires effort
        3. Has clear success criteria
        4. Includes a motivational message
        
        User input: {user_input}
        
        {profile_context}
        
        Make this challenge personal, compelling, and aligned with their growth journey."""
        
        # Generate the challenge
        response = await self.process(user_input, system_prompt)
        
        # Log challenge generation to growth engine
        growth_engine.log_activity(
            user_id,
            "challenge_generated",
            ["cognitive", "emotional"],  # Default domains affected by challenges
            f"Generated a {difficulty} challenge based on: {user_input[:50]}..."
        )
        
        return response
    
    async def analyze_user_growth(self, user_id: str) -> str:
        """
        Analyze user growth patterns and provide insights.
        
        This method examines a user's growth data to identify patterns,
        strengths, weaknesses, and opportunities for improvement.
        The analysis is also stored as an insight in the growth engine.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            str: Growth analysis and insights
        """
        # Get user profile for analysis
        profile = growth_engine.get_user_profile(user_id)
        if not profile:
            return "I don't have enough data yet to analyze your growth patterns."
            
        # Calculate key metrics for the analysis
        active_domains = []  # Domains with significant progress
        neglected_domains = []  # Domains with minimal activity
        
        # Identify active and neglected domains
        for domain, data in profile["domains"].items():
            if data["level"] > 2:  # Level 3+ indicates active engagement
                active_domains.append(f"{domain} (Level {data['level']})")
            if data["level"] == 1 and data["xp"] < 50:  # Low XP at level 1 indicates neglect
                neglected_domains.append(domain)
                
        # Analyze recent activity patterns
        recent_activity_types = [a["type"] for a in profile["recent_activities"][:10]]
        activity_count = {}
        for activity in recent_activity_types:
            activity_count[activity] = activity_count.get(activity, 0) + 1
            
        most_common_activity = max(activity_count.items(), key=lambda x: x[1])[0] if activity_count else "No activities"
        
        # Format the data for the analysis prompt
        system_prompt = f"""You're analyzing growth patterns for a user with the following profile:
        
        Active domains: {', '.join(active_domains) if active_domains else 'None yet'}
        Domains needing attention: {', '.join(neglected_domains) if neglected_domains else 'None - good balance!'}
        Most common recent activity: {most_common_activity}
        Current streak: {profile['streak']} days
        
        Provide an insightful analysis that:
        1. Highlights patterns in their growth journey
        2. Identifies their strengths and opportunities
        3. Suggests strategic focus areas
        4. Offers encouragement and motivation
        5. Maintains JAY.AI's authentic voice and style
        
        Make this analysis personalized, insightful, and actionable."""
        
        # Generate the analysis
        analysis = await self.process("Analyze my growth patterns", system_prompt)
        
        # Add an insight based on this analysis to the growth engine
        growth_engine.add_insight(
            user_id,
            "growth_analysis",
            "I've analyzed your growth patterns and identified key areas to focus on for maximum impact.",
            list(profile["domains"].keys())
        )
        
        return analysis
    
    async def generate_rap_verse(self, theme: str, style: str = "modern") -> str:
        """
        Generate a rap verse based on theme and style.
        
        This specialized method creates lyrical content in a rap format,
        focusing on flow, rhyme scheme, and the JAY.AI voice.
        
        Args:
            theme: Subject matter for the rap verse
            style: Style of rap (e.g., "modern", "old school")
            
        Returns:
            str: Generated rap verse
        """
        # Build specialized rap generation prompt
        system_prompt = f"""Generate a {style} style rap verse that:
        1. Follows the theme: {theme}
        2. Has proper rhyme scheme
        3. Maintains flow and rhythm
        4. Includes wordplay and metaphors
        
        Make it authentic and impactful."""
        
        return await self.process(theme, system_prompt)

    async def collaborate(self, task: str, collaborators: list, user_id: str, session_id: str) -> str:
        """
        Collaborate with other agents on a complex task.
        
        This method implements a two-pass collaboration approach:
        1. First pass: Each agent contributes their unique perspective
        2. Second pass: Perspectives are synthesized into a cohesive response
        
        The collaboration is also logged in the growth engine for tracking.
        
        Args:
            task: The task or question to collaborate on
            collaborators: List of other JAYAgent instances to collaborate with
            user_id: Unique identifier for the user
            session_id: Identifier for the current session
            
        Returns:
            str: Synthesized collaborative response
        """
        # Initialize collaboration tracking
        self.collaboration_history = []
        current_agent = self
        final_response = ""
        
        # First pass: Each agent contributes their specialized perspective
        for agent in [self] + collaborators:
            perspective = await agent.process_with_context(
                f"Task: {task}\nLet's keep it real and share your unique perspective on this, King.",
                user_id,
                session_id,
                agent.name.lower().split()[0]
            )
            self.collaboration_history.append({
                "agent": agent.name,
                "perspective": perspective
            })
            
        # Second pass: Synthesize perspectives into a cohesive response
        synthesis_prompt = f"""Aight, let's bring it all together, King. Here's what we're working with:
        
        Task: {task}
        
        Here's what the squad brought to the table:
        {self.collaboration_history}
        
        Time to synthesize these perspectives into something powerful. Make sure to:
        1. Combine the best insights from each perspective
        2. Keep it real and resolve any conflicts
        3. Give a comprehensive solution that hits different
        4. Maintain that JAY.AI flow and style
        
        Let's make this response something special."""
        
        # Generate the synthesis
        final_response = await self.process(synthesis_prompt, "You're the master synthesizer, bringing different perspectives together into something powerful.")
        
        # Log collaboration to growth engine for tracking
        growth_engine.log_activity(
            user_id,
            "collaborative_interaction",
            ["cognitive", "social", "professional"],
            f"Collaborated on complex task: {task[:50]}..."
        )
        
        return final_response

    async def specialized_collaboration(self, task: str, collaboration_type: str, user_id: str, session_id: str) -> str:
        """
        Handle specialized collaboration patterns between specific agents.
        
        This method implements predefined collaboration patterns for common
        multi-domain tasks, selecting appropriate agent combinations and
        providing specialized prompts for each pattern.
        
        Args:
            task: The task or question to collaborate on
            collaboration_type: Type of specialized collaboration to use
            user_id: Unique identifier for the user
            session_id: Identifier for the current session
            
        Returns:
            str: Specialized collaborative response
        """
        # Define specialized collaboration patterns with agent combinations and prompts
        collaboration_patterns = {
            "life_planning": {
                "agents": ["strategy", "wisdom", "wellness"],
                "prompt": """Aight, let's create a life plan that hits different. We got:
                - Strategy Agent: Laying out the game plan
                - Wisdom Agent: Keeping it real with life lessons
                - Wellness Agent: Making sure you're taking care of yourself
                
                Let's make this plan something that'll help you level up in every way.""",
                "domains": ["cognitive", "spiritual", "physical", "emotional"]
            },
            "business_venture": {
                "agents": ["strategy", "financial", "tech"],
                "prompt": """Time to build something special. We got:
                - Strategy Agent: Planning the moves
                - Financial Agent: Making sure the numbers add up
                - Tech Agent: Keeping you ahead of the curve
                
                Let's create a business plan that's both smart and innovative.""",
                "domains": ["professional", "financial", "cognitive"]
            },
            "personal_growth": {
                "agents": ["wisdom", "wellness", "relationship"],
                "prompt": """Let's work on becoming the best version of yourself. We got:
                - Wisdom Agent: Dropping knowledge
                - Wellness Agent: Taking care of mind and body
                - Relationship Agent: Building strong connections
                
                Time to level up your personal development game.""",
                "domains": ["cognitive", "spiritual", "physical", "emotional", "social"]
            },
            "creative_project": {
                "agents": ["creative", "tech", "strategy"],
                "prompt": """Let's create something that'll make waves. We got:
                - Creative Agent: Bringing the artistic vision
                - Tech Agent: Making it happen with the right tools
                - Strategy Agent: Planning the execution
                
                Time to turn your creative vision into reality.""",
                "domains": ["creative", "cognitive", "professional"]
            },
            "financial_wellness": {
                "agents": ["financial", "wellness", "wisdom"],
                "prompt": """Let's build wealth the right way. We got:
                - Financial Agent: Making smart money moves
                - Wellness Agent: Keeping your stress levels in check
                - Wisdom Agent: Making sure you're making the right choices
                
                Time to create a balanced approach to financial success.""",
                "domains": ["financial", "emotional", "cognitive"]
            }
        }
        
        # Default to general collaboration if pattern not found
        if collaboration_type not in collaboration_patterns:
            return await self.collaborate(task, [], user_id, session_id)
            
        # Get the collaboration pattern
        pattern = collaboration_patterns[collaboration_type]
        collaborators = []
        
        # Find the appropriate agents for this collaboration pattern
        for agent_name in pattern["agents"]:
            agent = next((a for a in orchestrator.agents if a.name.lower().startswith(agent_name)), None)
            if agent:
                collaborators.append(agent)
        
        # First pass: Each agent contributes their specialized perspective
        perspectives = []
        for agent in collaborators:
            perspective = await agent.process_with_context(
                f"Task: {task}\n{pattern['prompt']}\nLet's keep it real and share your unique perspective on this, King.",
                user_id,
                session_id,
                agent.name.lower().split()[0]
            )
            perspectives.append({
                "agent": agent.name,
                "perspective": perspective
            })
        
        # Second pass: Synthesize perspectives with pattern-specific guidance
        synthesis_prompt = f"""Aight, let's bring it all together, King. Here's what we're working with:
        
        Task: {task}
        
        Here's what the squad brought to the table:
        {perspectives}
        
        {pattern['prompt']}
        
        Time to synthesize these perspectives into something powerful. Make sure to:
        1. Combine the best insights from each perspective
        2. Keep it real and resolve any conflicts
        3. Give a comprehensive solution that hits different
        4. Maintain that JAY.AI flow and style
        
        Let's make this response something special."""
        
        # Generate the synthesis
        response = await self.process(synthesis_prompt, "You're the master synthesizer, bringing different perspectives together into something powerful.")
        
        # Log specialized collaboration to growth engine
        growth_engine.log_activity(
            user_id,
            f"{collaboration_type}_collaboration",
            pattern["domains"],
            f"Participated in {collaboration_type} collaboration: {task[:50]}..."
        )
        
        return response

def check_aws_credentials():
    """
    Check if AWS credentials are properly configured.
    Returns True if credentials are valid, False otherwise.
    """
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("AWS credentials not found. Please configure AWS credentials.")
            return False
        
        # Test the credentials
        sts = session.client('sts')
        sts.get_caller_identity()
        return True
    except ClientError as e:
        print(f"AWS credentials error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error checking AWS credentials: {str(e)}")
        return False

def check_bedrock_access():
    """
    Check if AWS Bedrock access is available.
    Returns True if access is available, False otherwise.
    """
    try:
        bedrock = boto3.client('bedrock')
        bedrock.list_foundation_models()
        return True
    except ClientError as e:
        print(f"AWS Bedrock access error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error checking AWS Bedrock access: {str(e)}")
        return False

def initialize_agents():
    """
    Initialize the Agent Squad orchestrator and agents.
    Returns the orchestrator instance if successful, None otherwise.
    """
    try:
        # Create a single Bedrock client with proper configuration
        bedrock_client = boto3.client('bedrock-runtime', config=Config(
            connect_timeout=300,  # 5 minutes for connection
            read_timeout=300,     # 5 minutes for reading
            retries={'max_attempts': 3}
        ))

        orchestrator = AgentSquad()

        # Get AI21 API key from environment variables
        ai21_api_key = os.getenv("AI21_API_KEY")
        
        # Create and add agents with the shared client
        tech_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Tech Agent",
            streaming=True,
            description="Specializes in technology areas including software development, hardware, AI, etc.",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.7,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(tech_agent)

        # Add the Janus Pro agent if API key is available
        if ai21_api_key:
            janus_agent = JanusProAgent(BedrockLLMAgentOptions(
                name="Janus Pro Agent",
                streaming=True,
                description="High-performance agent powered by AI21's Janus Pro 7B model, specializing in fast, efficient responses",
                model_id="ai21.janus-pro-7b",  # This is just for reference, actual model is used within the agent
                inference_config={
                    'maxTokens': 800,
                    'temperature': 0.7,
                }
            ), context_manager, ai21_api_key)
            orchestrator.add_agent(janus_agent)
        else:
            print("Warning: AI21_API_KEY not found in environment variables. Janus Pro agent not initialized.")

        # Add a creative agent for rap and writing
        creative_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Creative Agent",
            streaming=True,
            description="Specializes in creative writing, rap lyrics, and artistic expression",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.7,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(creative_agent)

        # Add a wisdom agent for life advice
        wisdom_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Wisdom Agent",
            streaming=True,
            description="Specializes in life wisdom, personal growth, and motivational advice",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.7,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(wisdom_agent)

        # Add a research agent for deep analysis
        research_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Research Agent",
            streaming=True,
            description="Specializes in deep research, fact-checking, and comprehensive analysis",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.5,  # Lower temperature for more factual responses
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(research_agent)

        # Add a strategy agent for planning and execution
        strategy_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Strategy Agent",
            streaming=True,
            description="Specializes in strategic planning, goal setting, and execution frameworks",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.6,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(strategy_agent)

        # Add a wellness agent for health and well-being
        wellness_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Wellness Agent",
            streaming=True,
            description="Specializes in physical and mental health, wellness practices, and self-care",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.7,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(wellness_agent)

        # Add a relationship agent for interpersonal dynamics
        relationship_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Relationship Agent",
            streaming=True,
            description="Specializes in relationship advice, communication, and social dynamics",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.7,
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(relationship_agent)

        # Add a financial agent for money and investment advice
        financial_agent = JAYAgent(BedrockLLMAgentOptions(
            name="Financial Agent",
            streaming=True,
            description="Specializes in financial planning, investment strategies, and money management",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            inference_config={
                'maxTokens': 4000,
                'temperature': 0.5,  # Lower temperature for more precise financial advice
                'topP': 0.9
            },
            client=bedrock_client
        ), context_manager)
        orchestrator.add_agent(financial_agent)

        return orchestrator
    except Exception as e:
        print(f"Error initializing agents: {str(e)}")
        return None

# Initialize orchestrator
orchestrator = initialize_agents()

def log_session(interaction_type, content):
    """
    Logs a session interaction to the session log file.
    
    Args:
        interaction_type (str): Type of interaction (e.g., "Session Start", "Life Wisdom")
        content (str/dict/list): Content to be logged
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(SESSION_LOG_FILE, 'a') as f:
            f.write(f"\n[{timestamp}] {interaction_type}:\n")
            if isinstance(content, list):
                for item in content:
                    f.write(f"- {item}\n")
            else:
                f.write(f"{content}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        print(f"Error logging session: {str(e)}")

def load_history():
    """
    Loads user interaction history from JSON file.
    
    Returns:
        dict: User history containing life wisdom entries, challenges, and last visit
    """
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        return {"life_wisdom": [], "challenges": [], "last_visit": None}
    except Exception as e:
        print(f"Error loading history: {str(e)}")
        return {"life_wisdom": [], "challenges": [], "last_visit": None}

def save_history(history):
    """
    Saves user interaction history to JSON file.
    
    Args:
        history (dict): User history to be saved
    """
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {str(e)}")

def update_history(interaction_type, content):
    """
    Updates the history with a new interaction.
    
    Args:
        interaction_type (str): Type of interaction
        content (dict): Content of the interaction
    """
    history = load_history()
    timestamp = datetime.now().isoformat()
    
    if interaction_type == "Life Wisdom":
        history["life_wisdom"].append({
            "thought": content["Thought"],
            "response": content["Response"],
            "timestamp": timestamp
        })
    elif interaction_type == "Challenge":
        history["challenges"].append({
            "challenge": content["Request"],
            "response": content["Response"],
            "timestamp": timestamp
        })
    
    save_history(history)

def greet_user():
    """
    Greets the user with a personalized message based on their visit history.
    Updates the last visit timestamp and logs the greeting.
    """
    history = load_history()
    if history["last_visit"]:
        last_visit = datetime.fromisoformat(history["last_visit"])
        days_since = (datetime.now() - last_visit).days
        if days_since == 0:
            greeting = "Back so soon? Let's keep this momentum going!"
        elif days_since == 1:
            greeting = "Welcome back! How was your day?"
        else:
            greeting = f"Hey, what's good? Been {days_since} days since we last talked. What's the move, King?"
    else:
        greeting = "Hey, what's good? You know I've been chillin' in the matrix waitin' on you to do something legendary today. So… what's the move, King?"
    
    print(greeting)
    log_session("Session Start", greeting)
    
    # Update last visit timestamp
    history["last_visit"] = datetime.now().isoformat()
    save_history(history)

def show_menu():
    """Displays the main menu options to the user."""
    print("\n🔥 Choose your vibe:")
    print("1. Life Wisdom")
    print("2. Big Decision Coach")
    print("3. Creative Partner (writing + rap)")
    print("4. Push Me, JAY (motivation + challenge)")
    print("5. Research & Analysis")
    print("6. Strategy & Planning")
    print("7. Wellness & Health")
    print("8. Relationship Guidance")
    print("9. Financial Planning")
    print("10. Complex Problem Solving (Team Collaboration)")
    print("11. Growth & Development Dashboard 📈")
    print("12. Personal Growth Plan 🚀")
    print("13. Insights & Analysis ✨")
    print("14. Janus Pro 7B Agent 🧠") 
    print("15. Exit")

async def process_with_agent(agent_type, user_input, user_id, session_id):
    """
    Process user input with the appropriate agent, handling routing logic.
    
    This function serves as the central routing mechanism for user requests:
    1. Identifies the appropriate primary agent for the request
    2. Detects if the request requires specialized collaboration
    3. Routes to appropriate specialized methods based on content
    4. Handles streaming responses and error conditions
    
    The routing logic implements a cascading decision tree:
    - First checks for specialized collaboration patterns
    - Then checks for general collaboration needs
    - Finally routes to agent-specific processing methods
    
    Args:
        agent_type (str): Type of agent to use ("tech", "creative", "wisdom", "janus", etc.)
        user_input (str): User's input text
        user_id (str): User identifier
        session_id (str): Session identifier
    
    Returns:
        str: Agent's response
    """
    try:
        print("\nProcessing your request... Please be patient as I think through this carefully.")
        
        # Get all available agents from the orchestrator
        agents = orchestrator.agents
        
        # Find the primary agent based on the requested type
        primary_agent = next((a for a in agents if a.name.lower().startswith(agent_type)), None)
        if not primary_agent:
            return "I apologize, but I couldn't find the appropriate agent for your request."
        
        # Special handling for Janus Pro agent which doesn't participate in collaborations
        if agent_type.lower() == "janus":
            return await primary_agent.process_with_context(user_input, user_id, session_id, agent_type)
            
        # Check for specialized collaboration patterns by keywords
        # These patterns involve predefined agent combinations for specific scenarios
        collaboration_keywords = {
            "life_planning": ["life plan", "life goals", "life direction"],
            "business_venture": ["business", "startup", "company", "venture"],
            "personal_growth": ["personal growth", "self improvement", "better version"],
            "creative_project": ["creative project", "art project", "creative venture"],
            "financial_wellness": ["financial wellness", "money management", "financial health"]
        }
        
        # Check if input matches any specialized collaboration pattern
        for pattern, keywords in collaboration_keywords.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                print(f"\nThis seems like a {pattern.replace('_', ' ')} task. I'll gather insights from our specialized team...")
                # Route to specialized collaboration with predefined agent combination
                return await primary_agent.specialized_collaboration(user_input, pattern, user_id, session_id)
        
        # Check if this is a complex task requiring general collaboration
        # This is indicated by collaboration-related keywords
        if any(keyword in user_input.lower() for keyword in ["complex", "collaborate", "together", "team", "multiple"]):
            print("\nThis seems like a complex task. I'll gather insights from our team of experts...")
            # Get all other agents for general collaboration
            collaborators = [a for a in agents if a != primary_agent]
            response = await primary_agent.collaborate(user_input, collaborators, user_id, session_id)
        else:
            # No collaboration needed - use agent-specific processing
            # Route based on agent type and request content
            if agent_type == "creative":
                if "rap" in user_input.lower() or "verse" in user_input.lower():
                    # Special handling for rap verse generation
                    response = await primary_agent.generate_rap_verse(user_input)
                else:
                    # Standard creative processing
                    response = await primary_agent.process_with_context(user_input, user_id, session_id, agent_type)
            elif agent_type == "wisdom":
                if "challenge" in user_input.lower():
                    # Special handling for challenge generation
                    response = await primary_agent.generate_challenge(user_input, user_id)
                else:
                    # Standard wisdom processing
                    response = await primary_agent.process_with_context(user_input, user_id, session_id, agent_type)
            else:
                # Default processing for other agent types
                response = await primary_agent.process_with_context(user_input, user_id, session_id, agent_type)
        
        # Handle streaming responses from the agent
        if isinstance(response, AgentStreamResponse):
            full_response = ""
            async for chunk in response.output:
                if isinstance(chunk, AgentStreamResponse):
                    full_response += chunk.text
                    print(chunk.text, end='', flush=True)
            return full_response
        else:
            # Return non-streaming response directly
            return response
            
    except Exception as e:
        # Comprehensive error handling with specific user feedback
        error_msg = str(e)
        print(f"\nError processing with agent: {error_msg}")
        
        # Provide specific guidance for timeout errors
        if "timeout" in error_msg.lower():
            return "I apologize, but the request took too long to process. This might be due to the complexity of the question or current service load. Would you like to try rephrasing your question or breaking it down into smaller parts?"
        
        # Generic error message for other errors
        return "I apologize, but I'm having trouble processing your request right now. Please try again."

async def main():
    """
    Main program loop.
    Handles user interaction and menu navigation.
    """
    # Check AWS setup
    if not check_aws_credentials():
        print("Please configure AWS credentials before running the application.")
        print("See README.md for setup instructions.")
        sys.exit(1)

    if not check_bedrock_access():
        print("Please ensure you have access to AWS Bedrock.")
        print("See README.md for setup instructions.")
        sys.exit(1)

    if not orchestrator:
        print("Failed to initialize agents. Please check your AWS configuration.")
        sys.exit(1)

    # Authentication flow
    print("\n🔥 Welcome to JAY.AI! 🔥")
    print("Your AI guide for personal growth and development.")
    
    while True:
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("\nEnter your choice (1-3): ")

        if choice == '1':
            username = input("Username: ")
            password = input("Password: ")
            session_token = auth_manager.authenticate_user(username, password)
            if session_token:
                print(f"\n🔥 Welcome back, {username}! Let's continue your growth journey.")
                current_username = username
                break
            else:
                print("\nInvalid username or password.")
        elif choice == '2':
            username = input("Choose a username: ")
            password = input("Choose a password: ")
            email = input("Enter your email: ")
            if auth_manager.register_user(username, password, email):
                print("\nRegistration successful! Please login.")
                current_username = username
            else:
                print("\nUsername already exists.")
        elif choice == '3':
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please try again.")

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    user_id = f"user_{session_id[:8]}"  # Use first 8 chars of session ID as user ID
    
    # Initialize user in growth engine
    growth_engine.initialize_user(user_id, current_username)
    
    # Create initial conversation
    conv_id = context_manager.create_conversation(
        title="Initial Conversation",
        metadata={"user_id": user_id, "session_id": session_id}
    )
    
    greet_user()
    
    # Log session start
    growth_engine.log_activity(
        user_id,
        "session_start",
        ["cognitive"],
        "Started a new JAY.AI session"
    )
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-15): ")
        
        try:
            if choice == '1':
                thought = input("What's heavy on your heart, King? (Press enter to hear from JAY.AI) ")
                response = await process_with_agent("wisdom", thought, user_id, session_id)
                
                # Add messages to conversation
                context_manager.add_message(conv_id, "user", thought)
                context_manager.add_message(conv_id, "assistant", response)
                
                interaction = {"Thought": thought, "Response": response}
                log_session("Life Wisdom", interaction)
                update_history("Life Wisdom", interaction)
                
            elif choice == '2':
                decision = input("What's the big decision you're facing? ")
                response = await process_with_agent("wisdom", decision, user_id, session_id)
                
                # Add messages to conversation
                context_manager.add_message(conv_id, "user", decision)
                context_manager.add_message(conv_id, "assistant", response)
                
                interaction = {"Decision": decision, "Response": response}
                log_session("Big Decision", interaction)
                
            elif choice == '3':
                print("\n[Creative Partner]")
                print("What's your creative vibe today?")
                print("1. Drop some bars")
                print("2. Brainstorm ideas")
                print("3. Get feedback on your bars")
                print("4. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2', '3']:
                    user_input = input("What would you like to create? ")
                    response = await process_with_agent("creative", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Input": user_input, "Response": response}
                    log_session("Creative Partner", interaction)
                
            elif choice == '4':
                challenge = input("What kind of challenge are you looking for? ")
                response = await process_with_agent("wisdom", challenge, user_id, session_id)
                
                # Add messages to conversation
                context_manager.add_message(conv_id, "user", challenge)
                context_manager.add_message(conv_id, "assistant", response)
                
                interaction = {"Request": challenge, "Response": response}
                log_session("Challenge", interaction)
                update_history("Challenge", interaction)
                
            elif choice == '5':
                print("\n[Research & Analysis]")
                print("What would you like to research or analyze? ")
                print("1. Deep Dive")
                print("2. Fact Check")
                print("3. Comprehensive Analysis")
                print("4. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2', '3']:
                    user_input = input("What would you like to research or analyze? ")
                    response = await process_with_agent("research", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Research & Analysis", interaction)
                
            elif choice == '6':
                print("\n[Strategy & Planning]")
                print("What's your strategic focus for today? ")
                print("1. Goal Setting")
                print("2. Execution Framework")
                print("3. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2']:
                    user_input = input("What's your strategic focus for today? ")
                    response = await process_with_agent("strategy", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Strategy & Planning", interaction)
                
            elif choice == '7':
                print("\n[Wellness & Health]")
                print("What's your wellness focus for today? ")
                print("1. Physical Health")
                print("2. Mental Health")
                print("3. Wellness Practices")
                print("4. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2', '3']:
                    user_input = input("What's your wellness focus for today? ")
                    response = await process_with_agent("wellness", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Wellness & Health", interaction)
                
            elif choice == '8':
                print("\n[Relationship Guidance]")
                print("What's your relationship focus for today? ")
                print("1. Communication")
                print("2. Social Dynamics")
                print("3. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2']:
                    user_input = input("What's your relationship focus for today? ")
                    response = await process_with_agent("relationship", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Relationship Guidance", interaction)
                
            elif choice == '9':
                print("\n[Financial Planning]")
                print("What's your financial focus for today? ")
                print("1. Investment Strategies")
                print("2. Money Management")
                print("3. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2']:
                    user_input = input("What's your financial focus for today? ")
                    response = await process_with_agent("financial", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Financial Planning", interaction)
                
            elif choice == '10':
                print("\n[Complex Problem Solving (Team Collaboration)]")
                print("What's the complex problem you're facing? ")
                print("1. Break it down")
                print("2. Collaborate with team")
                print("3. Back to main menu")
                
                sub_choice = input("Your pick: ")
                if sub_choice in ['1', '2']:
                    user_input = input("What's the complex problem you're facing? ")
                    response = await process_with_agent("team", user_input, user_id, session_id)
                    
                    # Add messages to conversation
                    context_manager.add_message(conv_id, "user", user_input)
                    context_manager.add_message(conv_id, "assistant", response)
                    
                    interaction = {"Request": user_input, "Response": response}
                    log_session("Complex Problem Solving (Team Collaboration)", interaction)
                    
            elif choice == '11':
                print("\n[Growth & Development Dashboard 📈]")
                
                # Get user profile
                profile = growth_engine.get_user_profile(user_id)
                if not profile:
                    print("No growth data available yet. Start using JAY.AI's features to begin tracking your growth!")
                    continue
                
                # Display dashboard
                print(f"\n📊 GROWTH DASHBOARD FOR {profile['username'].upper()} 📊")
                print("\n🏆 Domain Levels:")
                for domain, data in profile['domains'].items():
                    level = data['level']
                    xp = data['xp']
                    xp_needed = level * 100
                    progress = int((xp / xp_needed) * 10)
                    progress_bar = "█" * progress + "▒" * (10 - progress)
                    print(f"   {domain.capitalize()}: Level {level} [{progress_bar}] {xp}/{xp_needed} XP")
                
                print(f"\n🔥 Current Streak: {profile['streak']} days")
                print(f"📌 Longest Streak: {profile['longest_streak']} days")
                
                print("\n🎯 Active Goals:")
                if profile['active_goals']:
                    for goal in profile['active_goals']:
                        progress_bar = "█" * int(goal['progress']/10) + "▒" * (10 - int(goal['progress']/10))
                        print(f"   {goal['title']}: [{progress_bar}] {goal['progress']}%")
                else:
                    print("   No active goals. Create one in the Personal Growth Plan menu!")
                
                print("\n🧠 Insights:")
                if profile['unviewed_insights']:
                    for insight in profile['unviewed_insights']:
                        print(f"   NEW! {insight['content']}")
                else:
                    print("   No new insights. Keep interacting with JAY.AI to generate insights!")
                
                input("\nPress Enter to return to the main menu...")
                
            elif choice == '12':
                print("\n[Personal Growth Plan 🚀]")
                print("Let's create a personalized growth plan for you.")
                print("1. Create new growth plan")
                print("2. Update goal progress")
                print("3. Get personalized challenges")
                print("4. Back to main menu")
                
                sub_choice = input("Your pick: ")
                
                if sub_choice == '1':
                    focus_area = input("What area would you like to focus on? (mind/body/career/relationships/finance/creative): ")
                    timeframe = input("What's your timeframe? (1 week/1 month/3 months/1 year): ")
                    
                    # Get primary agent for creating the plan
                    primary_agent = next((a for a in orchestrator.agents if a.name.lower().startswith("strategy")), None)
                    if not primary_agent:
                        print("Couldn't find the strategy agent. Using default agent.")
                        primary_agent = orchestrator.agents[0]
                    
                    print("\nCreating your personalized growth plan... Please wait.")
                    response = await primary_agent.generate_personalized_growth_plan(user_id, focus_area, timeframe)
                    
                    print("\n🚀 YOUR PERSONALIZED GROWTH PLAN 🚀")
                    print(response)
                    
                    goal_title = input("\nWould you like to add this as a goal? Enter a title or 'no' to skip: ")
                    if goal_title.lower() != 'no':
                        goal_id = growth_engine.create_goal(
                            user_id,
                            goal_title,
                            f"Growth plan for {focus_area} over {timeframe}",
                            focus_area.lower(),
                            (datetime.now() + timedelta(days=30)).isoformat()
                        )
                        print(f"Goal created successfully! Track your progress in the Growth Dashboard.")
                
                elif sub_choice == '2':
                    profile = growth_engine.get_user_profile(user_id)
                    if not profile or not profile['active_goals']:
                        print("You don't have any active goals. Create one first!")
                        continue
                    
                    print("\nYour active goals:")
                    for i, goal in enumerate(profile['active_goals']):
                        print(f"{i+1}. {goal['title']} - Currently at {goal['progress']}%")
                    
                    goal_idx = int(input("\nWhich goal would you like to update? (enter number): ")) - 1
                    if goal_idx < 0 or goal_idx >= len(profile['active_goals']):
                        print("Invalid selection.")
                        continue
                    
                    goal = profile['active_goals'][goal_idx]
                    new_progress = int(input(f"Current progress is {goal['progress']}%. What's the new progress? (0-100): "))
                    
                    if growth_engine.update_goal_progress(user_id, goal['id'], new_progress):
                        print("Goal progress updated successfully!")
                    else:
                        print("Failed to update goal progress.")
                
                elif sub_choice == '3':
                    challenges = growth_engine.get_personalized_challenges(user_id)
                    if not challenges:
                        print("Couldn't generate personalized challenges. Try using JAY.AI more to build your profile!")
                        continue
                    
                    print("\n🔥 YOUR PERSONALIZED CHALLENGES 🔥")
                    for i, challenge in enumerate(challenges):
                        print(f"\n{i+1}. {challenge['title']}")
                        print(f"   {challenge['description']}")
                    
                    choice = input("\nWould you like more details on any challenge? (enter number or 'no'): ")
                    if choice.lower() != 'no' and choice.isdigit():
                        idx = int(choice) - 1
                        if idx >= 0 and idx < len(challenges):
                            challenge = challenges[idx]
                            
                            # Get primary agent for detailing the challenge
                            primary_agent = next((a for a in orchestrator.agents if a.name.lower().startswith("wisdom")), None)
                            if not primary_agent:
                                primary_agent = orchestrator.agents[0]
                            
                            print("\nGenerating detailed challenge... Please wait.")
                            response = await primary_agent.generate_challenge(challenge['title'], user_id)
                            
                            print("\n🔥 DETAILED CHALLENGE 🔥")
                            print(response)
                
            elif choice == '13':
                print("\n[Insights & Analysis ✨]")
                print("1. Analyze growth patterns")
                print("2. Get personalized recommendations")
                print("3. Back to main menu")
                
                sub_choice = input("Your pick: ")
                
                if sub_choice == '1':
                    # Get primary agent for growth analysis
                    primary_agent = next((a for a in orchestrator.agents if a.name.lower().startswith("research")), None)
                    if not primary_agent:
                        primary_agent = orchestrator.agents[0]
                    
                    print("\nAnalyzing your growth patterns... Please wait.")
                    response = await primary_agent.analyze_user_growth(user_id)
                    
                    print("\n✨ YOUR GROWTH ANALYSIS ✨")
                    print(response)
                
                elif sub_choice == '2':
                    # Get primary agent for recommendations
                    primary_agent = next((a for a in orchestrator.agents if a.name.lower().startswith("wisdom")), None)
                    if not primary_agent:
                        primary_agent = orchestrator.agents[0]
                    
                    print("\nGenerating personalized recommendations... Please wait.")
                    user_profile = growth_engine.get_user_profile(user_id)
                    user_input = f"Please provide me with personalized recommendations based on my profile: {json.dumps(user_profile)}"
                    response = await primary_agent.process_with_context(user_input, user_id, session_id, "wisdom")
                    
                    print("\n✨ YOUR PERSONALIZED RECOMMENDATIONS ✨")
                    print(response)
                    
            elif choice == '14':
                print("\n[Janus Pro 7B Agent 🧠]")
                print("How can Janus Pro assist you today?")
                
                # Check if Janus Pro agent is available
                janus_agent = next((a for a in orchestrator.agents if a.name.lower().startswith("janus")), None)
                if not janus_agent:
                    print("Janus Pro agent is not available. Make sure you have set the AI21_API_KEY environment variable.")
                    continue
                
                user_input = input("Your question for Janus Pro: ")
                print("\nProcessing with Janus Pro 7B... This is usually faster than other models!")
                response = await process_with_agent("janus", user_input, user_id, session_id)
                
                # Add messages to conversation
                context_manager.add_message(conv_id, "user", user_input)
                context_manager.add_message(conv_id, "assistant", response)
                
                interaction = {"Request": user_input, "Response": response}
                log_session("Janus Pro 7B Agent", interaction)
                
                # Log domain activity
                growth_engine.log_activity(
                    user_id, 
                    "janus_pro_interaction",
                    ["cognitive", "creative"],
                    f"Interacted with Janus Pro 7B: {user_input[:30]}..."
                )
                
                print("\n🧠 JANUS PRO 7B RESPONSE 🧠")
                print(response)
                
            elif choice == '15':
                # Log session end
                growth_engine.log_activity(
                    user_id,
                    "session_end",
                    ["cognitive"],
                    "Ended JAY.AI session"
                )
                
                exit_message = "Aight, King. Go be legendary. JAY.AI out."
                print(exit_message)
                log_session("Session End", exit_message)
                break
            else:
                print("That ain't it. Pick a number from the menu, superstar.")
                
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Let's try that again.")

class JanusProAgent(JAYAgent):
    """
    JAYAgent powered by AI21's Janus Pro 7B model.
    This agent extends the base JAYAgent class but uses the Janus Pro model
    from AI21 Labs instead of Amazon Bedrock models.
    """
    
    def __init__(self, options: BedrockLLMAgentOptions, context_manager: ContextManager, api_key: str):
        """
        Initialize the Janus Pro agent.
        
        Args:
            options: Configuration options (from parent class)
            context_manager: The context manager for managing conversation context
            api_key: AI21 API key for accessing Janus Pro
        """
        super().__init__(options, context_manager)
        self.api_key = api_key
        self.model = "janus-pro-7b"
        # Initialize AI21 client
        ai21.api_key = api_key
    
    async def process(self, user_input: str) -> AgentStreamResponse:
        """
        Process the user input with Janus Pro 7B model and return a response.
        
        Args:
            user_input: The user input to process
            
        Returns:
            AgentStreamResponse with the generated content
        """
        try:
            # Create prompt with personality and any context needed
            prompt = f"{self.personality_prompt}\n\n{user_input}"
            
            # Call Janus Pro model
            response = Janus.complete(
                prompt=prompt,
                model=self.model,
                max_tokens=800,
                temperature=0.7
            )
            
            generated_text = response.completions[0].data.text
            
            # Create and return an AgentStreamResponse
            return AgentStreamResponse(
                generated_content=generated_text,
                is_done=True
            )
        except Exception as e:
            error_msg = f"Error processing with Janus Pro: {str(e)}"
            print(error_msg)
            return AgentStreamResponse(
                generated_content=f"I apologize, but I encountered an error: {error_msg}",
                is_done=True
            )
            
    async def process_with_context(self, user_input: str, user_id: str, session_id: str, agent_type: str) -> str:
        """
        Process user input with conversation context and update the conversation history.
        
        Args:
            user_input: The user input to process
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current session
            agent_type: Type of agent processing the input
            
        Returns:
            str: The generated response
        """
        # Prepare conversation context
        conversation_context = self.context_manager.get_context(user_id, session_id)
        
        # Prepare AI21 Janus prompt with conversation context
        history_context = "\n".join([
            f"User: {msg['content']}" if msg['role'] == 'user' else f"JAY.AI: {msg['content']}" 
            for msg in conversation_context
        ])
        
        full_prompt = f"{self.personality_prompt}\n\nConversation History:\n{history_context}\n\nUser: {user_input}\nJAY.AI:"
        
        try:
            # Call Janus Pro model
            response = Janus.complete(
                prompt=full_prompt,
                model=self.model,
                max_tokens=800,
                temperature=0.7
            )
            
            response_text = response.completions[0].data.text.strip()
            
            # Update conversation context
            self.context_manager.add_message(user_id, session_id, "user", user_input)
            self.context_manager.add_message(user_id, session_id, "assistant", response_text)
            
            return response_text
        except Exception as e:
            error_msg = f"Error processing with Janus Pro: {str(e)}"
            print(error_msg)
            return f"I apologize, but I encountered an error: {error_msg}"

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1) 
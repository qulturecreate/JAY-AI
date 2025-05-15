# JAY.AI - Interactive AI Assistant

An interactive AI assistant that provides life wisdom, creative writing assistance, and motivational challenges using AWS Bedrock, AI21's Janus Pro 7B model, and Agent Squad.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **AWS Setup**
   - Create an AWS account if you don't have one
   - Install and configure AWS CLI:
     ```bash
     pip install awscli
     aws configure
     ```
   - Enter your AWS credentials when prompted:
     - AWS Access Key ID
     - AWS Secret Access Key
     - Default region (e.g., us-east-1)
     - Default output format (json)

3. **AWS Bedrock Access**
   - Go to AWS Console
   - Navigate to Amazon Bedrock
   - Request access to the following models:
     - Anthropic Claude 3 Sonnet
     - Other models you plan to use

4. **AI21 Janus Pro 7B Setup (Optional)**
   - Create an account at [AI21 Studio](https://studio.ai21.com/)
   - Generate an API key in your account settings
   - Create a `.env` file in the root directory (see `env.example`)
   - Add your AI21 API key to the `.env` file:
     ```
     AI21_API_KEY=your_api_key_here
     ```

5. **Run the Application**
   ```bash
   python jay_ai.py
   ```

## Features

- Life Wisdom: Get personalized advice and wisdom
- Big Decision Coach: Help with making important decisions
- Creative Partner: Generate rap lyrics and creative content
- Push Me, JAY: Get motivational challenges
- Janus Pro 7B Agent: Fast, efficient responses powered by AI21's Janus Pro model

## File Structure

- `jay_ai.py`: Main application file
- `jay_history.json`: Stores user interaction history
- `jay_sessions.txt`: Logs detailed session information
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (API keys, etc.)

## Troubleshooting

1. **AWS Credentials Issues**
   - Verify AWS credentials are properly configured
   - Check if you have access to AWS Bedrock
   - Ensure your region supports the required models

2. **Model Access Issues**
   - Request access to required models in AWS Bedrock
   - Verify model IDs in the code match available models

3. **Dependency Issues**
   - Ensure all requirements are installed
   - Check Python version (3.11+ recommended)

4. **Janus Pro 7B Issues**
   - Verify your AI21 API key is correctly set in the `.env` file
   - Check if you have remaining credits in your AI21 account
   - Ensure you have proper internet connectivity to access the AI21 API

## Support

For issues or questions, please open an issue in the repository. 
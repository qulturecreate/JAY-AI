
# Jay.ai – Your AI Twin & Personal Powerhouse  
**Project Type:** Personal AI Assistant Prototype  
**Language:** Python  
**Environment:** Cursor IDE  
**Status:** In Development  
**Version:** 0.2

---

## Overview

**Jay.ai** (Justified Adaptive You – Artificial Intelligence) is a culturally adaptive AI assistant designed to reflect the unique voice and creative logic of its creator, Jason Arrington, Jr. It’s built to guide, challenge, and co-create—while evolving as a digital twin with emotional intelligence, tone awareness, and cultural fluency.

---

## Core Features

- 🧠 Dynamic menu system for life advice, creative ideation, decision coaching, and motivation  
- 🧩 Modular AWS Lambda-based “Agent Squads” to handle specific cognitive tasks  
- 🌍 Tone switching engine fluent in modern English, Geechie, and Ebonics  
- 🗣️ Interactive response delivery with evolving conversational logic  
- 🔄 Integration of **Janus Pro 7B** for enhanced dialogue flow, contextual reasoning, and adaptive personality modeling

---

## Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/qulturecreate/jay-ai.git
   cd jay-ai
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the main script:
   ```bash
   python src/menu_system.py
   ```

5. Customize the assistant by editing files in the `src/` directory.

---

## Feature Roadmap 🚧

| Feature                        | Status      | Notes                                              |
|-------------------------------|-------------|----------------------------------------------------|
| Janus Pro 7B integration       | In Progress | Enhancing reasoning and tone detection             |
| Voice interface via Gradio     | Planned     | Voice interaction module using open source tools   |
| Personality mood tracker       | Planned     | Adjusts tone/response based on user interaction    |
| Plugin-style “Agent Squad” API | In Design   | Dynamic task agents for scalable intelligence      |
| Testing suite (unit + logic)   | In Progress | Test core AI logic and system responses            |

---

## Testing

A testing framework using `pytest` will be implemented to verify:
- Decision flow logic
- NLP response formatting
- Agent Squad task delegation
- Error handling and fallback systems

*To run tests (coming soon):*
```bash
pytest tests/
```

---

## Community & Contribution 🤝

We welcome thoughtful ideas and collaborative energy!

- **Open an issue** for bugs, feature requests, or language improvements
- **Fork and submit pull requests** for improvements or experimentation
- **Share feedback** on tone adaptation and cultural language logic

Start here: [https://github.com/qulturecreate/jay-ai/issues](https://github.com/qulturecreate/jay-ai/issues)

---

## Tech Stack

- **Languages:** Python  
- **AI & NLP:** Janus Pro 7B (in progress), OpenAI API  
- **Infrastructure:** AWS Lambda, EventBridge  
- **Interface/Dev Tools:** Cursor IDE, Flask, Git  
- **Future Additions:** Gradio, LangChain, whisper  

---

## About the Creator

**Jason Arrington, Jr.**  
Certified IBM AI Developer | Multimillion-Dollar Sales Pro | Full-Stack Problem Solver  
Explore the project and follow the journey: [github.com/qulturecreate/jay-ai](https://github.com/qulturecreate/jay-ai)

---

## License  
MIT License – See LICENSE file for details

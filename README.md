# AI-Driven Survey Platform

Provides businesses, marketers, and decision-makers with AI-generated virtual populations modeled to reflect real-world demographics and behaviors. The platform enables users to define and execute surveys, tapping into detailed, personality-rich profiles for meaningful insights. Whether you're a marketing professional, startup founder, product manager, or policy maker, this platform is designed to help you understand customer needs, analyze market trends, and predict public responses. With built-in survey templates and flexible data export options, it makes market research and predictive analysis accessible and actionable.

## Key Features

- **AI-Generated Virtual Populations**: Create surveys with a statistically representative population, tailored to specific demographics and psychographics.
- **Customizable Surveys**: Define custom surveys or use pre-built templates for different fields, including marketing, product development, and public policy.
- **Rich Persona Profiles**: Each virtual profile includes demographics, personality traits, and detailed daily habits to mirror real-world behaviors.
- **Flexible Data Export**: Export survey results in flat CSV format for further analysis and integration with other tools.

## Technology Stack

- **Backend**: Python and Flask
- **Storage**: PostgreSQL for permanent data storage
- **Queue Management**: Redis and Celery for managing survey processing
- **RAG Framework**: LlamaIndex, connecting with NVIDIA NIM as the default endpoint for AI-assisted survey creation and execution (`survey_builder.py`, `profile.py`). Optionally, users can configure MistralAI or OpenAI inference endpoints.

## Code Structure

- **Backend Configuration**: The main configuration is set up in `app.py`, which initializes core extensions, registers blueprints, and defines global routes for the platform.
  
- **Survey Management**:
  - **Survey Creation and Execution**: `survey_builder.py` handles CRUD operations, AI-based survey generation, and template management. It contains survey-building logic and associated routes.
  - **Survey Analysis**: `survey_analysis.py` provides data visualization and filtering tools for analyzing survey responses with various analytical methods.

- **Data Processing**:
  - **Queue Management**: Redis and Celery manage the history and state of survey processing tasks.
  - **Data Export**: `survey_analysis.py` includes mechanisms to export results in CSV format, enabling easy data interaction and operability.

- **User and Subscription Management**:
  - **User Access and Security**: `access_control` and `subscription_routes` modules handle login, user permissions, and subscription functionalities to ensure secure access and transaction processing.

- **Dashboard and Analytics**:
  - **Population Exploration**: The `population_explorer.py` blueprint supports visualization of population demographics, providing insights into potential survey segments.

## Getting Started

This repository is part of a developer contest requirement. For a live demonstration and to experience the app in a production environment, create an account at [www.mimeticmind.com](http://www.mimeticmind.com) and explore its features firsthand.

## License

This project is licensed under the GPLv3 License. See the [LICENSE](./LICENSE) file for more information.

---

This app aims to make advanced, AI-driven market research available to everyone, helping you make data-backed, informed decisions effortlessly.

# Audience Forecasting Tool

A full-stack application that uses AI to analyze marketing messages across different audience personas.

## Features

- Modern, responsive UI built with React and Tailwind CSS
- Flask backend with OpenAI integration
- Multiple preset audience personas
- Real-time analysis of marketing messages
- Detailed persona responses with causal reasoning

## Prerequisites

- Python 3.8+
- Node.js 14+
- OpenAI API key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd audience-forecasting-tool
```

2. Set up the Python environment:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Flask backend:
```bash
# From the root directory
python src/app.py
```

2. Start the React frontend:
```bash
# From the frontend directory
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## Usage

1. Enter your marketing message in the text area
2. Select one or more audience personas from the dropdown
3. Click "Analyze Message" to get AI-generated responses for each persona
4. Review the detailed analysis and causal reasoning for each persona

## Project Structure

```
├── frontend/              # React frontend
│   ├── src/              # Source files
│   ├── package.json      # Frontend dependencies
│   └── tailwind.config.js # Tailwind configuration
├── src/                  # Backend source code
│   └── app.py           # Flask application
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## License

MIT License - see LICENSE file for details
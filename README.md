# Audience Engine

This project provides a Flask-based API for analyzing marketing messages using persona simulations.

## Configuration

Create a `.env` file in the project root to hold any secrets or settings.  The
application uses `python-dotenv` so values in this file are loaded
automatically.  At minimum specify your OpenAI key:

```bash
cp .env.example .env
echo "OPENAI_API_KEY=your-openai-key" >> .env
```

Additional configuration options such as `DEBUG`, `HOST`, `PORT`,
`CORS_ORIGINS`, and model defaults are defined in `src/config.py`.

## Running the Application

Install the dependencies listed in `requirements.txt` and start the Flask app:

```bash
pip install -r requirements.txt
python src/app.py
```

By default this launches the development configuration.  For a production
deployment switch `config['default']` in `src/config.py` to use
`ProductionConfig` and run the server with a WSGI container such as
`gunicorn`.

## Running Tests

Pytest is used for automated testing. After installing the dependencies you can run all tests with:

```bash
pytest
```

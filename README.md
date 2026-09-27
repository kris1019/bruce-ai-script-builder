# Bruce AI Script Builder

Free local AI-assisted builder for Bruce Firmware BadUSB, BadBLE, and BruceJS scripts.

## Features
- Local Ollama AI generation
- BadUSB / BadBLE DuckyScript text output
- BruceJS output
- Live editor and preview
- Basic safety validation
- Export to .txt or .js
- No cloud API key required

## Run
`python app.py`

Make sure Ollama is running at `http://127.0.0.1:11434`.

## Safety
The built-in prompt is designed for benign automation/testing and blocks destructive or credential-stealing payload patterns.

## License
MIT

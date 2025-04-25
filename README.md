# GridGen

GridGen is a sophisticated power grid scenario generation and validation tool that combines power system analysis with modern web technologies. It helps engineers and researchers create, validate, and manage electrical grid scenarios while ensuring they meet physical and operational constraints.

## Features

- **Scenario Generation**: Create complex power grid scenarios with multiple buses, generators, and loads
- **Physics Validation**: Automatic validation of scenarios against physical constraints and power flow calculations
- **Web Interface**: Modern frontend for easy scenario management and visualization
- **OpenDSS Integration**: Utilizes OpenDSS for power system analysis
- **API Backend**: FastAPI-based backend for efficient scenario processing

## Prerequisites

- Python 3.8+
- Node.js 14+
- OpenDSS

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GridGen.git
cd GridGen
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Project Structure

- `/app` - Backend application code
- `/frontend` - Frontend React application
- `/models` - Machine learning models and utilities
- `/data` - Data storage and sample scenarios
- `/scripts` - Utility scripts for maintenance and deployment

## Key Dependencies

### Backend
- FastAPI - Web framework
- OpenDSS Direct - Power system simulation
- PyTorch - Machine learning capabilities
- Pandapower - Power system analysis
- Sentence Transformers - NLP functionality

### Frontend
- React
- Node.js packages (see package.json for details)

## Usage

1. Start the backend server:
```bash
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Access the web interface at `http://localhost:3000`

## Scenario Validation

The system validates scenarios based on several criteria:
- Voltage values (0.95-1.05 p.u.)
- Line capacity and power flow
- System balance (generation vs. load)
- Physical constraints

For detailed validation information, see `VALIDATION_README.md`.

## Development

- Use `black` for Python code formatting
- Run tests with `pytest`
- Follow PEP 8 style guidelines
- Use `flake8` for linting

## Testing

Run the test suite:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Contact

[Add your contact information here] 
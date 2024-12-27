# Whale Tracker

A data collection and analysis system for tracking cryptocurrency whale transactions on AssetDash.

## Features

- Real-time whale transaction monitoring
- Historical data collection and storage
- Pattern analysis and signal detection
- Performance metrics and reporting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sekanson/whale-tracker.git
cd whale-tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scriptsctivate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

## Usage

1. Start the data collector:
```bash
python -m whale_tracker.collector
```

2. Run analysis:
```bash
python -m whale_tracker.analysis
```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run tests:
```bash
pytest
```
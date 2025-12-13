# 💳 Credit Card Spend Dashboard

A Streamlit-powered dashboard for analyzing and visualizing credit card spending patterns from PDF statements.

## Features

- 📄 **PDF Parsing**: Automatically extract transactions from credit card statement PDFs
- 📊 **Interactive Visualizations**: View spending trends with dynamic charts using Plotly
- 🏷️ **Smart Categorization**: Automatically categorize transactions by merchant
- 💰 **Budget Tracking**: Monitor spending against your monthly budget
- 📈 **Multi-Card Support**: Analyze multiple credit cards simultaneously

## Project Structure

```
credit_cards/
├── app.py              # Main Streamlit application
├── parser.py           # PDF parsing and transaction extraction
├── categorizer.py      # Transaction categorization logic
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/madhuqmar/credit_cards_tracker.git
   cd credit_cards_tracker
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Upload your credit card statements**
   - Click "Browse files" to upload one or more PDF statements
   - The app will automatically parse and categorize transactions

3. **Explore your spending**
   - View total spending vs. budget
   - Analyze spending by category and subcategory
   - See transaction details in an interactive table

## Configuration

### Budget Settings
Edit the `BUDGET` variable in `app.py` to set your monthly spending limit:
```python
BUDGET = 2300  # Change this to your budget
```

### Transaction Categories
Customize categories in `categorizer.py` by adding merchant patterns:
```python
# Add new categories or modify existing ones
if "your_merchant" in m:
    return "Category", "Subcategory"
```

## Dependencies

- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **pdfplumber**: PDF parsing and text extraction
- **plotly**: Interactive visualizations
- **numpy**: Numerical computing

## How It Works

1. **PDF Parsing** (`parser.py`)
   - Extracts transaction data from PDF statements
   - Filters out payments and summary information
   - Handles multiple credit card formats

2. **Categorization** (`categorizer.py`)
   - Matches merchant names to predefined categories
   - Assigns both high-level categories and detailed subcategories
   - Supports custom categorization rules

3. **Visualization** (`app.py`)
   - Creates interactive charts and tables
   - Tracks spending against budget
   - Provides detailed transaction breakdowns

## Contributing

Feel free to submit issues or pull requests to improve the project!

## License

MIT License - feel free to use and modify for your personal finance tracking needs.

## Notes

- Keep your PDF statements secure and do not commit them to version control
- The app processes data locally - no information is sent to external servers
- Customize merchant patterns in `categorizer.py` to match your spending habits

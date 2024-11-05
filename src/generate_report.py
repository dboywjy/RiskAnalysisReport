import json
from jinja2 import Environment, FileSystemLoader

# Load your data (this can be from a JSON file, database, etc.)
data = {
    "report_title": "AFE-N2N Portfolio Analysis",
    "prepared_by": "AFE-N2N Client Service Group",
    "prepared_for": "Jane Jones",
    "report_generated": "2024-10-03",
    "analysis_as_of": "2024-10-03",
    "executive_summary": "This report helps you better understand the risks within your portfolios...",
    "asset_allocation": [
        {"name": "Portfolio", "percentage": 100, "contribution": 100, "max_drawdown": None, "volatility": None},
        {"name": "Tencent", "percentage": 20, "contribution": 110, "max_drawdown": None, "volatility": None},
        {"name": "CAD", "percentage": 70, "contribution": -5, "max_drawdown": None, "volatility": None},
        {"name": "10-year US Treasury", "percentage": 10, "contribution": -5, "max_drawdown": None, "volatility": None}
    ]
}

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('.'))  # Use '.' for current directory
template = env.get_template('portfolio_analysis02.html')  # Template name

# Render HTML with data
output = template.render(data)

# Save to HTML file
with open('client_report.html', 'w') as f:
    f.write(output)

print("Report generated: client_report.html")
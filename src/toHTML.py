import json
from jinja2 import Environment, FileSystemLoader

def load_json_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

def generate_html_report(data, currentTime, language="en"):
    # Load HTML template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(f'./risk_report_template_{language}.html')

    # Render the HTML report
    html_content = template.render(
        client_name="Jane Jones",  # Replace with actual client name
        report_date=currentTime,  # Replace with actual report date
        analysis_date=currentTime,  # Replace with actual analysis date
        assetAllocation=data['assetAllocation'],
        riskmetric=data['riskmetric'],
        marketrisk=data['marketrisk'],
        adtv=data['adtv'],
        risk_level=data['risk_level'],
        # correlation_risk=data['correlation_risk']
    )

    # Save the HTML report
    with open('risk_report.html', 'w') as html_file:
        html_file.write(html_content)

def main(currentTime = '2024-11-10', json_file='./outputJson/out.json', language="en"):
    json_data = load_json_data(json_file)  # Path to your JSON data
    generate_html_report(json_data, currentTime, language=language)

from flask import Flask, render_template, request, jsonify, send_file
from jobspy import scrape_jobs
import pandas as pd
import io
import csv
from datetime import datetime
import traceback

app = Flask(__name__)

# The personalized target roles
TARGET_ROLES = [
    "Assistant Professor (Pharmacy)",
    "Lecturer (Pharmaceutics)",
    "Faculty - Pharmaceutical Sciences",
    "Academic Content Developer (Pharmacy)",
    "Pharmacy Educator",
    "Formulation Scientist",
    "Junior Formulation Scientist",
    "Research Scientist - Pharmaceutics",
    "Drug Delivery Research Associate",
    "Nanoformulation Research Associate",
    "Pharmaceutical R&D Executive",
    "Product Development Scientist",
    "New Product Development (NPD) Executive",
    "Pharmaceutical Research Associate"
]

# Global variable to store current dataframe
current_df = None

@app.route('/')
def index():
    return render_template('index.html', roles=TARGET_ROLES)

@app.route('/api/scrape', methods=['POST'])
def scrape():
    global current_df
    data = request.json
    role = data.get('role', 'Formulation Scientist')
    
    try:
        print(f"Scraping jobs for: {role}")
        
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor", "naukri", "google"],
            search_term=role,
            location="India",
            results_wanted=15,
            country_indeed="India"
        )
        
        if jobs.empty:
            return jsonify({
                'success': False,
                'message': 'No jobs found for this profile. Try adjusting the search term!'
            })
        
        # Select columns to display
        display_cols = ['site', 'title', 'company', 'location', 'date_posted', 'job_url']
        current_df = jobs[display_cols].copy()
        
        # Convert to HTML table
        table_html = current_df.to_html(
            classes='jobs-table',
            escape=False,
            index=False,
            render_links=True
        )
        
        # Format the table to make job_url clickable
        table_html = table_html.replace(
            'http',
            '<a href="http',
            -1
        )
        table_html = table_html.replace(
            '.com">',
            '.com" target="_blank">Apply</a><',
            -1
        )
        
        return jsonify({
            'success': True,
            'count': len(current_df),
            'message': f'✅ Found {len(current_df)} jobs!',
            'table': table_html
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error scraping jobs: {str(e)}'
        }), 500

@app.route('/api/download', methods=['GET'])
def download():
    global current_df
    
    if current_df is None or current_df.empty:
        return jsonify({
            'success': False,
            'message': 'No data to download. Please scrape jobs first!'
        }), 400
    
    try:
        # Create CSV in memory
        output = io.StringIO()
        current_df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a bytes buffer
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        filename = f"pharma_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

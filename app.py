from flask import Flask, render_template, request, jsonify
from analyzer import RepositoryAnalyzer
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    repo_url = data.get('repo_url', '').strip()
    
    if not repo_url:
        return jsonify({"error": "Please provide a repository URL"}), 400
    
    try:
        analyzer = RepositoryAnalyzer(repo_url)
        result = analyzer.analyze()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

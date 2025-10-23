from flask import Flask, render_template, jsonify
import os
import datetime


app = Flask(__name__)

@app.route('/')
def home():
    deployment_tag = os.getenv('DEPLOYMENT_TAG', 'latest')
    return render_template('index.html', deployment_tag=deployment_tag)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

@app.route('/api/info')
def info():
    return jsonify({
        'application': 'EKS Demo App',
        'description': 'A simple Flask application deployed to EKS cluster',
        'technology': 'Python Flask',
        'deployment': 'Kubernetes EKS',
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)

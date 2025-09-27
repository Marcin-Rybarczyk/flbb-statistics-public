from flask import Flask, jsonify

app = Flask(__name__)

# Example of software version information
software_version_info = {
    "version": "2.0.1",
    "release_date": "2023-12-14",
    "download_url": "https://yourdomain.com/downloads/software-v2.0.1.zip",
    "release_notes": "https://yourdomain.com/release-notes/v2.0.1"
}

@app.route('/api/check_version', methods=['GET'])
def check_version():
    return jsonify(software_version_info)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
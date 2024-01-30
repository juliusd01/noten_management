from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define the base URLs for your microservices
microservice_urls = {
    'user_service': 'http://user_service:2000',
    'grade_service':'http://grade_service:7000',
    'stats_service':'http://stats_service:10000'
}

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy():
    # Extract the template parameter from the query string
    template = request.args.get('template')

    # Check if the template parameter is provided
    if not template:
        return jsonify({'error': 'Template not specified'}), 400
    
    # Map template to microservice
    service=''
    if template=='login' or template=='user':
        service='user_service'
    elif template=='grades':
        service='grade_service'
    elif template=='stats' or template=='stats/pdf':
        service='stats_service'
    # add other services using elif

    # Check if the specified template exists in the microservice URLs
    if service not in microservice_urls:
        return jsonify({'error': 'Invalid service'}), 404

    # Build the target URL by combining the base URL and the remaining path
    target_url = f"{microservice_urls[service]}/{template}"

    # Forward the request to the microservice
    response = requests.request(
        method=request.method,
        url=target_url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )

    # Build the response to send back to the client
    headers = [(name, value) for name, value in response.raw.headers.items()]
    response = app.response_class(response=response.content, status=response.status_code, headers=headers)
    return response

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(port=5000, host='0.0.0.0')

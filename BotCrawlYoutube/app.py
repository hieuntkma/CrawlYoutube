from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Biến lưu trữ dữ liệu đã nhận được
received_data = []

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.json
    received_data.append(data)  # Lưu trữ dữ liệu vào danh sách
    print("Received data:", data)
    return jsonify({"status": "success"}), 200

@app.route('/show-data', methods=['GET'])
def show_data():
    # Render dữ liệu đã nhận được trên trang web
    html_template = '''
    <h1>Data Received:</h1>
    <ul>
        {% for item in received_data %}
            <li>{{ item }}</li>
        {% endfor %}
    </ul>
    '''
    return render_template_string(html_template, received_data=received_data)

if __name__ == '__main__':
    app.run(port=8000)
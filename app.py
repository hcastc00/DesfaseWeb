from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def delete_old_images():
    # Borra todas las imágenes en el directorio de uploads, excepto currentIMG
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename != 'currentIMG':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.remove(file_path)

@app.route('/pantalla')
def index():
    # Siempre mostrar currentIMG
    current_image = os.path.join(app.config['UPLOAD_FOLDER'], 'currentIMG')
    if os.path.exists(current_image):
        return render_template('index.html', image='currentIMG')
    else:
        return render_template('index.html', image=None)

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(url_for('upload_image'))
        
        file = request.files['image']
        
        if file.filename == '':
            return redirect(url_for('upload_image'))

        if file:
            # Eliminar imágenes antiguas
            delete_old_images()
            
            # Guardar la nueva imagen como currentIMG
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'currentIMG')
            file.save(file_path)
            
            # Notificar a todos los clientes para que recarguen la página
            socketio.emit('image_uploaded', {'image': 'currentIMG'})
            return "Imagen subida", 200

    return render_template('upload.html')

@socketio.on('connect')
def test_connect():
    print('Cliente conectado')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, host='0.0.0.0', port=5000)

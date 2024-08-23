from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def move_old_images_to_date_folder():
    # Crear el nombre de la carpeta basado en la fecha actual
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], datetime.now().strftime('%Y-%m-%d'))
    
    # Crear la carpeta si no existe
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)

    # Mover las imágenes existentes a la carpeta del día
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename != 'currentIMG':
            # Extraer la extensión del archivo original
            file_extension = os.path.splitext(filename)[1]
            
            # Crear el nuevo nombre de archivo basado en la hora actual
            new_filename = datetime.now().strftime('%H-%M-%S') + file_extension
            
            # Mover el archivo a la carpeta del día con el nuevo nombre
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            new_file_path = os.path.join(date_folder, new_filename)
            os.rename(old_file_path, new_file_path)

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
            # Mover imágenes antiguas a la carpeta de la fecha actual
            move_old_images_to_date_folder()
            
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

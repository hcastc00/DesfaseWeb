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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path) and filename != 'currentIMG':
            # Extraer la extensión del archivo original
            file_extension = os.path.splitext(filename)[1]
            
            # Crear el nuevo nombre de archivo basado en la hora actual
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')[:-3]
            new_filename = f"{timestamp}{file_extension}"
            
            # Mover el archivo a la carpeta del día con el nuevo nombre
            new_file_path = os.path.join(date_folder, new_filename)
            os.rename(file_path, new_file_path)

@app.route('/pantalla')
def index():
    # Buscar el archivo currentIMG con cualquier extensión en el directorio de uploads
    upload_folder = app.config['UPLOAD_FOLDER']
    current_image_filename = None

    # Iterar a través de los archivos en el directorio de uploads
    for filename in os.listdir(upload_folder):
        if filename.startswith('currentIMG') and os.path.isfile(os.path.join(upload_folder, filename)):
            current_image_filename = filename
            break

    # Renderizar la plantilla y pasar el nombre completo del archivo
    if current_image_filename:
        return render_template('index.html', image=current_image_filename)
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
            # Mover las imágenes existentes a la carpeta de la fecha actual
            move_old_images_to_date_folder()
            
            # Guardar la nueva imagen como currentIMG
            file_extension = os.path.splitext(file.filename)[1]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'currentIMG' + file_extension)
            file.save(file_path)
            
            # Notificar a todos los clientes para que recarguen la página
            socketio.emit('image_uploaded', {'image': 'currentIMG' + file_extension})
            return "Imagen subida", 200

    return render_template('upload.html')

@socketio.on('connect')
def test_connect():
    print('Cliente conectado')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, host='0.0.0.0', port=5000)

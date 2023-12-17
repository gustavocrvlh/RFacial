import os
from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
import face_recognition
import cv2
from datetime import datetime
import os
from tempfile import NamedTemporaryFile

app = Flask(__name__)

# Configuração do SQLite
app.config['DATABASE'] = os.path.join(os.getcwd(), 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['SECRET_KEY'] = 'sua_chave_secreta'

cap = None

def criar_tabela():
    with app.app_context():
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY,
                        nome TEXT NOT NULL,
                        numero TEXT NOT NULL,
                        cpf TEXT NOT NULL,
                        imagem BLOB
                        )''')
        conn.commit()
        conn.close()

def inserir_usuario(nome, numero, cpf, imagem):
    with app.app_context():
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, numero, cpf, imagem) VALUES (?, ?, ?, ?)", (nome, numero, cpf, imagem))
        conn.commit()
        conn.close()

def buscar_usuarios():
    with app.app_context():
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        conn.close()
        return usuarios

def salvar_imagem(imagem, nome):
    if imagem:
        imagem_bin = imagem.read()
        return imagem_bin
    return None

#API

# Conectar-se ao banco de dados SQLite
conn = sqlite3.connect('database.db')  # Substitua 'example.db' pelo seu arquivo de banco de dados
c = conn.cursor()

# Consulta para buscar imagens da tabela
c.execute("SELECT imagem, nome FROM usuarios")  # Substitua 'usuarios' pelo nome da sua tabela e 'imagem' pelo nome da coluna de imagem
data = c.fetchall()

# Criar um diretório temporário para armazenar as imagens
temp_directory = 'temp_images'
if not os.path.exists(temp_directory):
    os.makedirs(temp_directory)

# Salvar imagens temporariamente no diretório temporário
known_face_encodings = []
known_face_names = []

for image_blob, image_name in data:
    temp_image_path = os.path.join(temp_directory, image_name)
    with open(temp_image_path, 'wb') as f:
        f.write(image_blob)
    image = face_recognition.load_image_file(temp_image_path)
    encoding = face_recognition.face_encodings(image)[0]  # Assumindo que há apenas um rosto em cada imagem
    known_face_encodings.append(encoding)
    known_face_names.append(image_name)

@app.route('/')
def index():
    return render_template('cadastro.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/mostrar')
def mostrar():
    usuarios = buscar_usuarios()
    global cap
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Largura desejada
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Altura desejada

    return render_template('mostrar.html', usuarios=usuarios)


@app.route('/process_cadastro', methods=['POST'])
def process_cadastro():
    nome = request.form['nome']
    numero = request.form['numero']
    cpf = request.form['cpf']
    imagem = request.files['imagem']

    if imagem.filename != '':
        imagem_bin = salvar_imagem(imagem, nome)
        inserir_usuario(nome, numero, cpf, imagem_bin)

    return redirect(url_for('mostrar'))

#API
def generate_frames():

    # Variável para rastrear correspondências já exibidas no terminal
    match_displayed = False
    # Variável para rastrear se o rosto foi detectado na iteração anterior
    face_detected_prev = False

    # Dicionário para rastrear os nomes exibidos no vídeo
    names_on_video = {}

    # Use um contador para executar a detecção a cada N quadros
    frame_count = 0
    detection_interval = 5  # Ajuste conforme necessário
    face_locations = []  # Defina a variável fora do bloco if

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % detection_interval == 0:
            # Realize o reconhecimento facial na imagem do frame
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            # Limpe os nomes que não foram detectados
            names_on_video = {name: (left, top - 10) for name, (left, top) in names_on_video.items() if any(
                face_recognition.compare_faces(known_face_encodings, face_encoding) for face_encoding in face_encodings
            )}

            # Verifique se o rosto está sendo detectado na iteração atual
            face_detected = any(face_recognition.compare_faces(known_face_encodings, face_encodings) for face_encodings in face_encodings)

            # Exiba a mensagem de detecção no terminal se o rosto foi detectado nesta iteração, mas não na anterior
            if face_detected and not face_detected_prev:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time}: Rosto correspondente detectado")
                for (top, right, bottom, left), face_encodings in zip(face_locations, face_encodings):
                    # Compare a codificação do rosto com as codificações conhecidas
                    matches = face_recognition.compare_faces(known_face_encodings, face_encodings)

                    for i, match in enumerate(matches):
                        if match:
                            name = known_face_names[i]
                            print(f"Nome: {name}")

            face_detected_prev = face_detected

            for (top, right, bottom, left), face_encodings in zip(face_locations, face_encodings):
                # Compare a codificação do rosto com as codificações conhecidas
                matches = face_recognition.compare_faces(known_face_encodings, face_encodings)

                for i, match in enumerate(matches):
                    if match:
                        name = known_face_names[i]
                        # Adicione o nome do rosto ao dicionário
                        names_on_video[name] = (left, top - 10)

        # Exibir o frame com retângulos ao redor dos rostos detectados
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Exiba os nomes dos rostos detectados no vídeo
        for name, (left, top) in names_on_video.items():
            cv2.putText(frame, name, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



    cap.release()
    cv2.destroyAllWindows()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    criar_tabela()
    app.run(debug=True)
import face_recognition
import cv2
import sqlite3
from datetime import datetime
import os
from tempfile import NamedTemporaryFile

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

# Inicialize a captura de vídeo
cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Largura desejada
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Altura desejada

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

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()

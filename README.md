# RFacial
##(currently working on a standalone app with this function)

A web application that recognizes registered users in the database from a photo, through real-time facial recognition.

Installing a few packages is needed in order for the application to run.

Here are some of these packages:

  Face Recognition:
  - Used to diferenciate the faces, so trainning a AI was not needed.

  OpenCV:
  - Used to receive the webcam video feed.

  Flask:
  - Used to make the application run with a web interface

The file FKapi.py will open the webcam feed that recognizes the faces registered in the database.db file. You can register more persons via the web application. This application is opened by the IntegratedFKapi.py file.

Final result:

![image](https://github.com/gustavocrvlh/RFacial/assets/85922093/80778cfb-b3c2-40a2-9c91-63146f8da7b4)

Use the route "/mostrar" to open this page


![image](https://github.com/gustavocrvlh/RFacial/assets/85922093/4d77c039-0c81-4362-ae81-f1db11d80763)

Terminal





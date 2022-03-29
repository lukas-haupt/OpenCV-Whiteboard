# OpenCV-Whiteboard
## Autoren
Lukas Haupt
<br>
Stefan Weisbeck

## Gliederung
- Idee
- Grundfunktionen
  - Umsetzung
- Warum Mediapipe?
- Gestenerkennung
  - Gründe für eigener Ansatz
  - Rotation
  - Beispiel(e)
- Features
  - Generelle Idee
- Kompatibilität mit NVIDIA Jetson Nano
  - Probleme mit Installation von Packages
  - Probleme mit CSI-Kamera

### Rotation

Die Implementation der Gestenerkennung basiert auf der Annahme, dass die Hand sich in einer senkrechten Position befindet. Dies ist aber ergonomisch ungünstig und erschwert die Bedienung enorm. Da die Gestenerkennung ansonsten gut funktioniert wurde beschlossen, die erkannten Landmarken der Hand zu rotieren. Auf diese Weise blieb die Gestenerkennung als solche von den Änderungen unberührt.

Da die Position im Raum für die Gestenerkennung irrelevant ist, konnte auf eine Translation zu einem Rotationszentrum verzichtet werden. Es blieb als einzige Transformation die Rotation. Aufgrund der geringen Anzahl von 42 (zum Implementationszeitpunkt 21) 2D-Punkten und der Notwendigkeit von nur einer Transformation wurde beschlossen, diese auf der CPU auszuführen.

Als Vergleichsachse wurde die Strecke zwischen der Handwurzel (Punkt 0) und den Zeigefingeransatzes (Punkt 5) gewählt. Da der Zeigefinder bei allen Gästen zum Einsatz kommt wird hier eine besonders unverfälschte Positionierung erwartet.

![Nummerrierung der Landmarken durch Mediapipe](hand_landmarks.png)

Die Berechnung der des Schnittwinkels zur Vertikalen erfolgt nach der Formel

![Formel Schnittwinkel zweier Geraden](images/intersection_angle.svg)

Da der Schnittwinkel zur Vertikalen ermittelt wird, fallen einige Teile der Berechnung weg, sodass das Programm nicht die vollständige Berechnung ausführt.
Nachdem der Schnittwinkel ermittel wurde wird noch überprüft, ob eine Rotation von über 90° und in welche Richtung diese durchgeführt wird. Da die gewählte Vergleichsachse nicht vertikal ist wird um einen Versatz von 0,5 Rad rotiert. Je nach Rotationsrichtung und Hand wird der Versatz addiert oder Subtrahiert.

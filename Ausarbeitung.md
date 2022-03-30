# OpenCV-Whiteboard
## Autoren
Lukas Haupt
<br>
Stefan Weisbeck

## Gliederung
- Idee und Lösungskomponenten
- Gestenerkennung
  - Gründe für eigenen Ansatz
  - Rotation
  - Beispiel(e)
- Grundfunktionen
- Features
  - Generelle Idee
- Kompatibilität mit NVIDIA Jetson Nano
  - Probleme mit Installation von Packages
  - Probleme mit CSI-Kamera


## Idee und Lösungskomponenten
Unser Ansatz für das Projekt ergab sich daraus, ein modernes Whiteboard, für den täglichen Einsatz, mithilfe grundlegender Funktionen nachzubilden. Im Folgenden wird der generelle Ablauf des Programmes beschrieben:

> Mithilfe einer Webcam werden die Hände des Benutzers betrachtet. Werden nun die Hände in bestimmte Positionen gebracht, so führt das Programm eine jeweils zugehörige Funktion aus. Zu den grundlegenden Funktionen gehören Zeichnen, Radieren, Farbwechsel, sowie das Speichern, Laden und Löschen von Skizzen. Das Whiteboard soll so konzipiert sein, dass alle Funktionen ausschließlich durch bestimmte Gesten ausgeführt werden.

Die Darstellung der Programmes erfolgt über OpenCV. Aufgrund der Schnittstelle ist es möglich, Inhalte innerhalb benutzerdefinierter Fenster darzustellen, sowie  diese gemäß verschiedener Funktionen und Attributen zu bearbeiten.

Für das Tracking der Finger/Hände benutzen wir Mediapipe. Mediapipe bietet plattformübergreifende Machine Learning Lösungen für dynamische Eingaben. Als "ready-to-use"-Lösung wird hierfür das "Mediapipe Hands"-Framework verwendet. Die Analyse eines Frames gibt dabei ein Objekt zurück, in dem die 21 normierten Koordinaten der jeweils erkannten Hände liegen. Diese Koordinaten befinden sich im dreidimensionalen Raum.


## Gestenerkennung
Die Gesternerkennung erfolgt durch einen alternativen, eigenen Ansatz. Nach der Berechnung der Koordinaten für die Indices des Handmodells durch Mediapipe, werden diese in einer separaten Methode auf diverse Anordnungen überprüft (Beispiel: Ist eine x- oder/und y-Koordinate größer/kleiner als eine andere?). Hier wird absichtlich die z-Koordinate ausgeschlossen. Kalkulationen dieser Art befinden sich dementsprechend im zweidimensionalen Raum. Werden nun alle Kriterien einer Geste erfüllt, so wird diese zurückgegeben.

Theoretisch wäre es möglich gewesen, die Erkennung der Handgesten mithilfe von TensorFlow zu implementieren. TensorFlow ist eine open-source Bibliothek für Machine Learning und Deep Learning und besitzt einen besonderen Fokus auf Deep Neural Networks.
Eine Implementierung mit TensorFlow wäre simpel: Nachdem ein Bild der Kamera durch Mediapipe analysiert wird, gibt man das daraus resultierende Objekt an TensorFlow weiter. Mit den zur Verfügung stehenden Methoden und Modellen wird eine Geste durch Wahrscheinlichkeitsberechnungen bestimmt. Diese wird im weiteren Programmablauf verarbeitet.

Aus Gründen der Flexibilität haben wir uns jedoch dagegen entschieden, wie im Folgenden erläutert wird.

### Gründe für eigenen Ansatz
1. Mit unserer Vorstellung, dass die Funktionen des Whiteboards bestimmte Handgesten verwenden, war eine Einbindung bereits vorgefertigter Modelle für TensorFlow ausgeschlossen. Diese bestanden entweder aus einer Vielzahl von Gesten, die sich semantisch nicht in unser Projekt einordnen ließen oder aufgrund der Größe des Modells nicht ausreichend genug waren.

2. Das Trainieren von eigenen, spezifischen Gesten bezüglich eines Modells wäre für unsere Anwendung zu aufwendig gewesen, da die Größe des Projektes den Zeitraum der Projektphase stark beschränkt hat. Des Weiteren wurden sowohl das Einlesen in die Thematik als auch eventuell damit verbundene Problembehandlungen für das Erstellen eines solchen Modells berücksichtigt.

3. Unsere Kalkulation für die Gestenerkennung is einfach zu implementieren, die sie auf grundlegenden Operationen und Vergleichen beruht.

### Rotation

Die Implementation der Gestenerkennung basiert auf der Annahme, dass die Hand sich in einer senkrechten Position befindet. Dies ist aber ergonomisch ungünstig und erschwert die Bedienung enorm. Da die Gestenerkennung ansonsten gut funktioniert wurde beschlossen, die erkannten Landmarken der Hand zu rotieren. Auf diese Weise blieb die Gestenerkennung als solche von den Änderungen unberührt.

Da die Position im Raum für die Gestenerkennung irrelevant ist, konnte auf eine Translation zu einem Rotationszentrum verzichtet werden. Es blieb als einzige Transformation die Rotation. Aufgrund der geringen Anzahl von 42 (zum Implementationszeitpunkt 21) 2D-Punkten und der Notwendigkeit von nur einer Transformation wurde beschlossen, diese auf der CPU auszuführen.

Als Vergleichsachse wurde die Strecke zwischen der Handwurzel (Punkt 0) und den Zeigefingeransatzes (Punkt 5) gewählt. Da der Zeigefinder bei allen Gästen zum Einsatz kommt wird hier eine besonders unverfälschte Positionierung erwartet.

![Nummerierung der Landmarken durch Mediapipe](images/hand_landmarks.png)

Die Berechnung der des Schnittwinkels zur Vertikalen erfolgt nach der Formel

![Formel Schnittwinkel zweier Geraden](images/intersection_angle.svg)

Da der Schnittwinkel zur Vertikalen ermittelt wird, fallen einige Teile der Berechnung weg, sodass das Programm nicht die vollständige Berechnung ausführt.
Nachdem der Schnittwinkel ermittel wurde wird noch überprüft, ob eine Rotation von über 90° und in welche Richtung diese durchgeführt wird. Da die gewählte Vergleichsachse nicht vertikal ist wird um einen Versatz von 0,5 Rad rotiert. Je nach Rotationsrichtung und Hand wird der Versatz addiert oder Subtrahiert.

### Beispiele


## Grundfunktionen

# OpenCV-Whiteboard
## Autoren
Lukas Haupt
<br>
Stefan Weisbeck

## Gliederung
- Idee und Lösungskomponenten
- Grundfunktionen
  - Umsetzung
- Gestenerkennung
  - Gründe für eigener Ansatz
  - Rotation
  - Beispiel(e)
- Features
  - Generelle Idee
- Kompatibilität mit NVIDIA Jetson Nano
  - Probleme mit Installation von Packages
  - Probleme mit CSI-Kamera

## Idee und Lösungskomponenten
Unser Ansatz für das Projekt ergab sich daraus, ein modernes Whiteboard, für den täglichen Einsatz, mithilfe grundlegender Funktionen nachzubilden. Im Folgenden wird der generelle Ablauf des Programmes beschrieben:

> Mithilfe einer Webcam werden die Hände des Benutzers betrachtet. Werden nun die Hände in bestimmte Positionen gebracht, so führt das Programm eine jeweils zugehörige Funktion aus. Zu den grundlegenden Funktionen gehören Zeichnen, Radieren, Farbwechsel, sowie das Speichern, Laden und Löschen von Skizzen. Das Whiteboard soll so konzipiert sein, dass alle Funktionen ausschließlich durch bestimmte Gesten ausgeführt werden.

Die Darstellung der Programmes erfolgt über OpenCV. Aufgrund der Schnittstelle ist es möglich, Inhalte innerhalb benutzerdefinierter Fenster darzustellen, sowie  diese gemäß verschiedener Funktionen und Attributen zu bearbeiten.

Für das Tracking der Finger/Hände benutzen wir Mediapipe. Mediapipe bietet plattformübergreifende Machine Learning Lösungen für dynamische Eingaben. Als "ready-to-use"-Lösung wird hierfür das "Mediapipe Hands"-Framework verwendet. Die Analyse eines Frames gibt dabei ein Objekt zurück, in dem die 21 normierten Koordinaten jeweils beider Hand liegen. Diese Koordinaten befinden sich im dreidimensionalen Raum.

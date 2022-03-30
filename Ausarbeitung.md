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


## Kompatibilität mit dem nVIDIA Jetson Nano

Die Entwicklung der Anwendung erfolgte wegen Problemen mit dem Mediapipe Paket zunähst auf einem x86_64 PC entwickelt. Daher war zu nicht von Anfang an klar, ob die Anwendung auf einen nVIDIA Jetson Nano portierbar war.

Die größten Probleme bereitete das Mediapipe Paket. Dieses ist als fertiges Paket weder bei den Systempaketquellen noch bei bei Pip verfügbar und. Mediapipe kann auch nicht selbst compiliert werden, da eine Projektabhängigkeit vom Bazel Pakets, welches für ARM nicht verfügbar ist, nicht erfüllt werden kann.

Als funktionierende Lösung wurden dann ein fertiges Wheel-Paket für Pip eingesetzt. Für OpenCV wurde des Installationsskript von Mediapipe verwendet, welches automatisch die korrekte Version von OpenCV installiert.

Das neuste Wheel-Paket liegt allerdings nur als ältere Version 0.8.5 vor und nicht in der auf der PC Entwicklungsumgebung verwendeten Version 0.8.9.1. Dadurch konnten einige der genutzten Funktionen in der neueren Version nicht verwendet werden.

Da der Zweihand-Modus in der Version 0.8.5 noch nicht funktioniert, musste auf die Zoomfunktion, welche zwei Händen benötigt, verzichtet werden. Auch wurde deutlich, dass die Handerkennung in der älteren Version leicht unzuverlässiger ist. Dennoch kann die Anwendung den Zweck eines Whiteboards zuverlässig erfüllen.

Auch das Programm selbst musste an den Jetson Nano angepasst werden. Aufgrund der geringen Auflösung des Bildschirms musste das UI, welches auf Auflösungen ab 1080p ausgelegt worden war, an die geringere Auflösung von 1024x600 angepasst werden.

Der Versuch die zum Jetson Nano gehörende CSI-Kamera zu verwenden konnte nicht erfolgreich abgeschlossen werden. Die dazu notwendige Pakete für Python3 konnten nicht installiert werden wodurch ein ansteuern der CSI-Kamera mit der auf Python3 aufbauenden Whiteboard Anwendung nicht möglich war. Der Einsatz mithilfe einer USB Webcam ist allerdings wie am PC ohne Einschränkungen möglich.

Abgesehen von den Einschränkungen in der Hardware und der Zoomfunktion ergibt sich auf dem Jeson Nano ein gutes Benutzererlebnis. Die geringe Auflösung der Kamera (640x480) und der Leinwand (1024x600) ermöglicht auch auf den Jetson Nano eine flüssiges und responsives Zeichnen.

![Auslastung des Jetson Nano während der Programmausführung in Jtop](images/jtop.png)

Die moderate Auslastung des Jetson Nano lässt vermuten, das auch mit einer höheren Leinwandauflösung eine akzeptable Leistungsfähigkeit der Anwendung erreicht werden kann.

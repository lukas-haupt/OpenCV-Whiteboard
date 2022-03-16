# Weitere Features implementieren und Quelltext optimieren
- [x] Ladefuntion
- [x] Speichern mit custom filename sowie über Hand-Geste (Quicksave)
- [x] Windows/Anzeigen-Layout verändern
- [x] Auswahl einer benutzerdefinierten Auflösung (Achtung: mit Whiteboard kompatibel) -> Fullscreen
- [ ] Geste für das Radieren ändern
- [ ] Gesten auf Optimalität überprüfen
- [x] Toolbar in Window benutzen -> Nein
- [x] Benutzung durch beide Hände (aktuell: rechte Hand)
- [x] Buttons in Window einfügen (bisher Speichern/Laden)
	
## Bugs:
- [x] Programm kann nicht durch ESCAPE (X) im Fenster geschlossen werden
- [x] Untere Capture-Screen kann nicht für Gesten benutzt werden
- [x] Ladefunktion -> ValueError: could not broadcast input array from shape (50,125,3) into shape (0,125,3)
- [x] (bei Stefan) Fullscreen offset nicht korrekt dargestellt

# Auf NVIDIA Jetson Nano lauffähig bekommen
Probleme:
- [ ] Kamera initialisieren durch GStreamer_Pipeline
- [x] Packages können nicht über pip installiert werden (Mediapipe)
- [x] Versionen kompatibel?

# Präsentation

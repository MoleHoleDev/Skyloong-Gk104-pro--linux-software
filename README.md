# Skyloong GK104 Pro Studio (RGB • Remap • Makra)

Zaawansowana, natywna aplikacja graficzna w **Pythonie (PySide6)** stworzona dla systemu Linux / CachyOS do kompleksowej konfiguracji klawiatury **Skyloong GK104 Pro (104RGB)**.

---

## Główne Funkcje Aplikacji

### 1. ⌨️ Zaawansowane Remapowanie Klawiszy (Key Remapping)
- **Pełna obsługa warstw sprzętowych:**
  - `Base` (Warstwa podstawowa)
  - `Layer 1`, `Layer 2`, `Layer 3` (Warstwy pokładowe Onboard)
  - `FnLayer 1`, `FnLayer 2`, `FnLayer 3` (Kombinacje klawisza `Fn + Klawisz`)
- **Interaktywna Wirtualna Klawiatura 104:**
  - Wizualne oznaczenia zmodyfikowanych klawiszy i przypisanych akcji.
  - Wybór dowolnego klawisza jednym kliknięciem myszy.
- **Kategorie przypisań:**
  - **Pojedyncze klawisze:** Alfanumeryczne, F1–F24, Nawigacja (Arrows, Home, End, Del, PgUp/Dn), NumPad, Modyfikatory.
  - **Kombinacje skrótów:** Dowolne modyfikatory (`Ctrl`, `Shift`, `Alt`, `Win`) + klawisz bazowy (np. `Ctrl+C`, `Ctrl+V`, `Alt+Tab`, `Ctrl+Shift+Esc`, `Win+D`, `Alt+F4`).
  - **Multimedia & System:** Regulacja głośności, Wyciszanie, Play/Pause, Następny/Poprzedni utwór, Odtwarzacz muzyki, Kalkulator, Mój Komputer, Funkcje przeglądarki.
  - **Mysz:** Lewy klik, Prawy klik, Środkowy klik, Wstecz, Dalej.
  - **Przypisanie Makra:** Błyskawiczne powiązanie dowolnego stworzonego makra z wybranym klawiszem.
  - **Reset / Unmap:** Przywracanie domyślnego działania lub wyłączanie klawisza.
- **Tabela przypisań aktywnej warstwy** z możliwością usuwania pojedynczych wpisów lub czyszczenia całej warstwy.

---

### 2. ⚡ Kompleksowy Menedżer Makr (Macro Studio)
- **Tworzenie i edycja makr:**
  - Nazwa makra, domyślne opóźnienie między krokami (ms).
  - Tryby powtarzania:
    - `Wykonaj X razy` (`RepeatXTimes`)
    - `Powtarzaj przy trzymaniu klawisza` (`ReleaseKeyToStop`)
    - `Włącz / Wyłącz ponownym kliknięciem - Toggle` (`PressKeyAgainToStop`)
- **Kreator kroków sekwencji:**
  - Typy operacji: `Press` (Naciśnij i puść), `Down` (Wciśnij i przytrzymaj), `Up` (Puść klawisz).
  - Precyzyjne opóźnienia po każdym kroku (ms).
  - Narzędzia edycji: Przesuwanie kroków w górę / w dół, usuwanie i czyszczenie.
- **Szybki generator tekstu (Quick Text):**
  - Wpisz dowolny tekst lub komendę (np. `sudo pacman -Syu`), a aplikacja automatycznie przekonwertuje go na sekwencję naciśnięć klawiszy z uwzględnieniem wielkich liter, cyfr i znaków specjalnych.

---

### 3. 🌈 Oświetlenie LED, Jasność, Podgląd Animacji & Kontroler w Trayu
- **Naprawa gaśnięcia LED:** Wyeliminowano problem wyłączania podświetlenia – konfiguracja oświetlenia jest natychmiast propagowana na wszystkie aktywne warstwy sprzętowe (Base, Layer 1, Layer 2, Layer 3).
- **Podgląd animacji na żywo (Live Animation Engine):**
  - Płynny silnik animacji w czasie rzeczywistym (~30 FPS) symulujący wybrane efekty (Tęcza, Fala, Oddychanie, Wiatrak, Gwiazdy/Meteor, Matrix, Cyberpunk, Rytm dźwięku oraz własne palety) bezpośrednio na wirtualnej klawiaturze.
  - Sterowanie podglądem: przycisk Pauza/Start oraz suwak regulacji prędkości animacji.
- **Wizualna Klawiatura & Obudowa GK104 Pro:**
  - Realistyczna stylizacja obudowy CNC GK104 Pro z zagłębioną płytą montażową (Switch Plate), wskaźnikami LED (`[CAPS]`, `[NUM]`, `[WIN]`, `[MAC]`, `[2.4G]`, `[BT]`, `[USB]`) oraz symulacją ekranu 1.04″ Smart OLED Screen.
  - Kwadratowe proporcje nasadek klawiszy (1:1 aspect ratio) z czytelnymi legendami.
  - **Wyróżnienie gniazd pokręteł (Knobs 1..6):** Klawisze obsługujące modułowe pokrętła (`Esc`, `F11`, `F12`, `PrtSc`, `ScrLk`, `Pause`) są w trybie remapowania wyraźnie wyróżnione bursztynową ramką i plakietkami `🎛️ K1`..`🎛️ K6`.
- **Płynna regulacja jasności (0–100%):** Dedykowany suwak jasności oraz szybkie przyciski (25%, 50%, 75%, 100%, Wył.) z dynamicznym skalowaniem luminancji profili RGB.
- **Kontroler w zasobniku KDE Plasma (System Tray):**
  - Ikona w trayu ze wskaźnikiem na żywo: podgląd stanu baterii laptopa (`BAT0`), zasilacza i urządzeń bezprzewodowych.
  - Szybkie menu kontekstowe: zmiana jasności podświetlenia (100%, 75%, 50%, 25%, 0%), szybkie motywy RGB, przełączanie warstw sprzętowych (Base, Layer 1-3).
  - Działanie w tle i minimalizacja do traya przy zamykaniu okna.
- **Biblioteka animacji:** Ponad 330 animowanych efektów z wyszukiwarką i podziałem na kategorie.
- **Wirtualne malowanie klawiatury (Per-Key RGB):** Malowanie pojedynczych klawiszy własnym kolorem z próbnika `QColorDialog`.
- **Malowanie strefowe:** Szybkie nakładanie kolorów na strefy (WASD, Strzałki, NumPad, F1-F12, Litery, Całość).
- **Gotowe motywy stylizowane:** Cyberpunk 2077, Synthwave Neon, Matrix Green, Sunset Glow, Ice Blizzard, Blood Red.

---

### 4. 🎛️ Modularne Pokrętła (Rotary Knobs — GK104 Pro)
- Obsługa do 6 modularnych pokręteł (Knob 1..6) z niezależnym mapowaniem obrotu w prawo (CW), obrotu w lewo (CCW) oraz wciśnięcia (Click).
- Gotowe schematy: Głośność, Odtwarzacz muzyki, Nawigacja WWW, Przewijanie stron, Zoom, Karty okien.
- Przycisk szybkiej synchronizacji: *"Skopiuj te pokrętła na wszystkie warstwy"* – sprawia, że pokrętła działają identycznie niezależnie od aktywnego profilu sprzętowego.

---

### 5. 🚀 Zapis do Pamięci Klawiatury & Profile
- **Przycisk "Wgraj do klawiatury" (Apply):** Generuje spójną konfigurację łączącą makra, remapy, pokrętła i oświetlenie, a następnie zapisuje je w trwałej pamięci Flash kontrolera GK104 Pro.
- **Zabezpieczenie bufora sprzętowego:** Automatyczna walidacja długości makr zapobiegająca błędom kontrolera.
- **Reset do ustawień fabrycznych (Unmap):** Przywraca fabryczny stan układu klawiszy.
- **Eksport & Import profili JSON:** Zapisywanie kopii zapasowej całej konfiguracji do pliku i łatwe przenoszenie między profilami.
- **Automatyczna pamięć:** Wszystkie ustawienia zapisują się lokalnie w `~/.config/skyloong_studio/profile.json`.

---

## Uruchomienie & Wymagania

Aplikacja posiada wbudowanego **Asystenta Diagnostyki i Instalacji**, który automatycznie sprawdza obecność wymaganych komponentów (Mono Runtime, reguły Udev dla USB/hidraw) i pozwala zainstalować je jednym kliknięciem:

- **Z Pulpitu:** Kliknij dwukrotnie skrót `Skyloong GK104 Pro Studio`.
- **Z Terminala:**
  ```bash
  python3 main.py
  # lub
  ./run.sh
  ```

### Ręczna instalacja zależności (opcjonalnie):
W przypadku chęci ręcznej konfiguracji uprawnień Udev i środowiska Mono:
```bash
sudo ./install_rules.sh
```
lub dla dystrybucji Arch / CachyOS:
```bash
sudo pacman -S mono
sudo cp install_rules.sh /tmp/ && sudo ./install_rules.sh
```

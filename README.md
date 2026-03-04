```markdown
# Żarówka Clicker – Prerelease

## Cel gry
Twoim zadaniem jest generowanie jak największej liczby punktów (**Score**) poprzez klikanie w żarówkę oraz rozsądne zarządzanie jej temperaturą.  
Gra łączy mechanikę *clickera* z prostą symulacją fizyczną – im większa moc, tym więcej ciepła, a przegrzanie oznacza straty.

---

## Sterowanie
- **Lewy przycisk myszy** na żarówce – kliknięcie (zdobywasz punkty)
- **Spacja** – alternatywne kliknięcie
- **Mysz** – obsługa menu

---

## Mechanika żarówki
- Każde kliknięcie zwiększa **Score** o wartość *Income/click*
- Kliknięcie przełącza żarówkę między stanem `ON / OFF`
- W stanie `ON` temperatura rośnie
- W stanie `OFF` żarówka stygnie do temperatury otoczenia

### Przegrzanie
- Po przekroczeniu **100°C**:
  - żarówka wyłącza się automatycznie
  - tracisz procent punktów (kara)

Balans między zyskiem a temperaturą to klucz do sukcesu.

---

## Panel boczny (Side Menu)
Wyświetla:
- **Score** – aktualne punkty
- **Income/click** – punkty za klik
- **Passive/sec** – pasywny dochód
- **Temp** – aktualna temperatura
- **Difficulty** – poziom trudności

Przyciski:
- **Difficulty Menu** – wybór trudności (tylko na początku)
- **Upgrades** – sklep z ulepszeniami
- **Exit** – zapis, wczytanie lub wyjście z gry

---

## Poziomy trudności
Trudność ustala temperaturę otoczenia:

- **Easy** – 18°C
- **Medium** – 36°C
- **Hard** – 52°C
- **Hell** – 80°C

⚠️ Po wybraniu trudności nie można jej zmienić.

---

## Ulepszenia (Upgrades)
Ulepszenia kupuje się za punkty. Mogą:
- zwiększać dochód z kliknięć
- dodawać pasywny dochód
- poprawiać lub pogarszać chłodzenie

Przykłady:
- **Better filament** – więcej punktów za klik
- **Solar power** – pasywny dochód
- **Heatsink** – lepsze chłodzenie
- **Overclock** – duży zysk kosztem temperatury
- **Undervolt** – mniejszy zysk, lepsze chłodzenie

### Randomizer
Specjalne ulepszenie losowe:
- losowo zmienia income, pasywny dochód i chłodzenie
- może bardzo pomóc albo poważnie zaszkodzić
- każdy zakup jest inny

Czysty chaos.

---

## Stronicowanie ulepszeń
Gdy ulepszeń jest dużo:
- **Next >>** – następna strona
- **<< Back** – poprzednia strona
- numer strony widoczny na dole menu

---

## Zapis i wczytywanie gry
W menu **Exit**:
- **Save Game** – zapis stanu gry
- **Load Game** – wczytanie zapisu
- **Exit to Desktop** – wyjście z gry

Zapis posiada **checksumę**, co utrudnia ręczne modyfikacje.

---

## Wskazówki
- Spam-klikanie bez kontroli temperatury kończy się stratami
- Pasywny dochód działa cały czas
- Chłodzenie bywa ważniejsze niż sam income
- Wyższe trudności nagradzają cierpliwość

---

## Podsumowanie
To nie jest zwykły clicker.  
To gra o energii, cieple i konsekwencjach.

Więcej mocy → więcej temperatury → większe ryzyko.  
Kto kontroluje temperaturę, ten wygrywa.
```

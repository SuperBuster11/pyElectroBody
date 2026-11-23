# pyelectroman

Port gry **Electro Man** (DOS, 1993) do Pythona 3 + pygame. Działa na Windows 32- i 64-bit (oraz Linux/macOS).

## O grze

**Electro Man** (w Polsce wydany jako **Electro Body**) to platformówka akcji na DOS
stworzona przez polskie studio xLand: w Polsce w 1992 roku, na świecie w 1993 roku
nakładem Epic MegaGames. Bohater, Jacek, przypomina RoboCopa. W przyszłości obcy
napadają na kosmiczną bazę ludzi i zabijają jego rodzinę, a on rusza po zemstę.

Przechodzisz 8 poziomów bazy obcych. Zbierasz baterie, które wzmacniają broń (ale
broń się przegrzewa i zużywa amunicję), korzystasz z teleportów i punktów kontrolnych,
a do otwarcia wyjścia potrzebujesz 3 dyskietek. Każdy dotyk wroga, pocisku albo
pułapki kończy się wybuchem i powrotem do ostatniego punktu kontrolnego. Gra słynie
z wysokiego poziomu trudności.

xLand udostępnił grę za darmo w 2006 roku na licencji Creative Commons
Attribution-ShareAlike 2.5. Grafiki i dźwięki w folderze `data` pochodzą
z oryginału, a ten projekt przenosi grę do Pythona.

## Uruchomienie z kodu (Windows)

1. Zainstaluj Pythona 3.10–3.14 z https://www.python.org/downloads/windows/
   (do 32-bitowego Windows wybierz instalator „Windows installer (32-bit)”).
   Przy instalacji zaznacz **Add python.exe to PATH**.
2. Kliknij dwukrotnie `uruchom.bat` (za pierwszym razem doinstaluje pygame).

Ręcznie: `pip install -r requirements.txt`, potem `python em.py`.

Gra używa biblioteki **pygame-ce** (`import pygame` działa bez zmian). Klasyczne
`pygame` 2.6.1 nie ma gotowych paczek dla Pythona 3.14. Nie instaluj obu naraz:
jeśli masz stare `pygame`, usuń je poleceniem `pip uninstall pygame`.

## Samodzielny plik .exe

- Lokalnie: uruchom `zbuduj_exe.bat` → powstanie `dist\ElectroMan.exe`.
  Bitowość .exe = bitowość zainstalowanego Pythona.
- Automatycznie: po wypchnięciu zmian na GitHub zakładka **Actions** zbuduje
  `ElectroMan-windows-x86` (32-bit) i `ElectroMan-windows-x64` (64-bit) do pobrania.

## Sterowanie

| Klawisz | Akcja |
|---|---|
| ← → | chodzenie |
| ↑ | skok |
| ↓ | wejście do teleportu (stojąc na nim) |
| Spacja | strzał (w menu: start) |
| Esc | powrót do menu / wyjście |
| F1 | informacje deweloperskie |

Klawisze deweloperskie: `1`–`8` wczytanie poziomu, `Shift+0`–`Shift+5` wybór broni,
`Ctrl+strzałki` przełączanie ekranów, `Tab` podgląd kolizji.

## Zasady

Zbieraj baterie (silniejsza broń) i 3 dyskietki, potem stań na wyjściu (niebieski pas
w podłodze), żeby przejść do następnego poziomu. Przeciwnicy, ich pociski oraz
elementy elektryczne i kolce zabijają; po śmierci wracasz do ostatniego punktu
kontrolnego.

## Stan prac

Działa: intro z oryginalnym logo i muzyką, wszystkie 8 poziomów, animacje otoczenia,
chodzenie, skoki, kolizje, teleporty, baterie, dyskietki, punkty kontrolne, wyjście,
strzelanie, ruch i strzały przeciwników, działka, rakiety, śmierć i odradzanie, dźwięki.

Przeszkody: działka strzelające w stałym rytmie, rakiety spadające z sufitu lub
wylatujące z podłogi, gdy przechodzisz obok, łuki elektryczne i kolce, przepaść
na ekranach oznaczonych „podłoga zabija”.

Do zrobienia: ekran końca gry.

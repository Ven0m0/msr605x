# MSR605X Utility per Ubuntu

Un'applicazione nativa GTK4 per Ubuntu per leggere, scrivere e gestire carte a banda magnetica utilizzando il dispositivo MSR605X.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2022.04+-purple.svg)

## Panoramica

MSR605X Utility è un'alternativa open source all'utility Windows per il lettore/scrittore di carte magnetiche MSR605X. L'applicazione è stata progettata per funzionare nativamente su Ubuntu e altre distribuzioni Linux compatibili con GTK4.

**Testato con firmware**: REVH7.31

## Funzionalità

### Operazioni sulle Carte
- **Lettura**: Leggi tutte e 3 le tracce (ISO e dati grezzi)
- **Scrittura**: Scrivi dati su tutte e 3 le tracce
- **Cancellazione**: Cancellazione selettiva delle tracce
- **Copia**: Clona carte (lettura + scrittura)

### Connessione Automatica
- **Plug & Play**: Il dispositivo viene rilevato e connesso automaticamente
- **Hot-plug**: Rilevamento automatico quando il dispositivo viene collegato/scollegato
- **Nessun pulsante Connect**: L'interfaccia è semplificata, la connessione è gestita automaticamente

### Formati Supportati
- **ISO 7811** - Standard internazionale per carte magnetiche
- **Dati Grezzi** - Accesso diretto ai bit

### Configurazione
- **Coercività**: Hi-Co (2750-4000 Oe) / Lo-Co (300 Oe)
- **BPI**: 75 o 210 bit per pollice per traccia
- **BPC**: 5, 7 o 8 bit per carattere per traccia

### Gestione File
- Salvataggio dati in formato JSON
- Salvataggio dati in formato CSV
- Caricamento dati da file

### Interfaccia Utente
- Design moderno con GTK4 e libadwaita
- Supporto tema chiaro/scuro automatico
- Indicatori LED di stato
- Log delle operazioni in tempo reale
- Notifiche toast per feedback immediato

## Requisiti di Sistema

- **Sistema Operativo**: Ubuntu 22.04+ (o altre distribuzioni Linux con GTK4)
- **Python**: 3.10 o superiore
- **Hardware**: Dispositivo MSR605X collegato via USB

## Installazione

### Metodo 1: Pacchetto Debian (.deb) - Consigliato

Il modo più semplice per installare l'applicazione su Ubuntu/Debian:

```bash
# Scarica il pacchetto .deb dalla pagina Releases
wget https://github.com/Sam4000133/msr605x-ubuntu/releases/latest/download/msr605x-utility_1.0.0-1_all.deb

# Installa il pacchetto
sudo dpkg -i msr605x-utility_1.0.0-1_all.deb

# Installa eventuali dipendenze mancanti
sudo apt-get install -f
```

Dopo l'installazione, l'applicazione sarà disponibile nel menu applicazioni.

### Metodo 2: Ubuntu Software Center (Snap)

Installa direttamente da Ubuntu Software Center o via terminale:

```bash
# Installa da Snap Store (quando disponibile)
sudo snap install msr605x-utility

# Abilita l'accesso al dispositivo USB
sudo snap connect msr605x-utility:raw-usb
```

Oppure installa da file .snap locale:

```bash
# Scarica il pacchetto .snap dalla pagina Releases
wget https://github.com/Sam4000133/msr605x-ubuntu/releases/latest/download/msr605x-utility_1.0.0_amd64.snap

# Installa il pacchetto
sudo snap install msr605x-utility_1.0.0_amd64.snap --dangerous

# Abilita l'accesso al dispositivo USB
sudo snap connect msr605x-utility:raw-usb
```

### Metodo 3: Script di Installazione

```bash
# Clona il repository
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu

# Esegui lo script di installazione
chmod +x install.sh
sudo ./install.sh
```

### Metodo 4: Installazione Manuale

#### 1. Installa le dipendenze di sistema

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libhidapi-hidraw0 libhidapi-dev
```

#### 2. Clona il repository

```bash
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu
```

#### 3. Installa le dipendenze Python

```bash
pip install -r requirements.txt
```

#### 4. Installa l'applicazione

```bash
pip install -e .
```

#### 5. Configura i permessi udev (richiesto per accesso senza root)

```bash
# Copia le regole udev
sudo cp data/99-msr605x.rules /etc/udev/rules.d/

# Ricarica le regole
sudo udevadm control --reload-rules
sudo udevadm trigger

# Aggiungi il tuo utente al gruppo plugdev
sudo usermod -aG plugdev $USER
```

**Importante**: Effettua il logout e login per applicare le modifiche al gruppo.

### Metodo 3: Flatpak

```bash
# Installa flatpak-builder se non presente
sudo apt install flatpak-builder

# Compila e installa
flatpak-builder --user --install build-dir com.github.msr605x.yaml
```

## Utilizzo

### Avvio dell'Applicazione

```bash
# Da terminale
python -m src.main

# Oppure dopo l'installazione
msr605x-gui
```

L'applicazione sarà anche disponibile nel menu applicazioni come "MSR605X Utility".

### Guida Rapida

1. **Connessione**: Il dispositivo viene rilevato e connesso automaticamente quando collegato via USB
2. **Lettura**:
   - Vai al pannello "Read Card"
   - Seleziona il formato (ISO o Raw)
   - Clicca "Read Card" e striscia la carta
3. **Scrittura**:
   - Vai al pannello "Write Card"
   - Inserisci i dati per ogni traccia (senza sentinel %, ;, ? - vengono aggiunti automaticamente)
   - Clicca "Write Card" e striscia una carta vuota
4. **Cancellazione**:
   - Vai al pannello "Erase Card"
   - Seleziona le tracce da cancellare
   - Conferma e striscia la carta
5. **Impostazioni**:
   - Configura coercività (Hi-Co/Lo-Co)
   - Esegui test diagnostici sul dispositivo

## Struttura del Progetto

```
msr605x-ubuntu/
├── src/
│   ├── main.py              # Punto di ingresso
│   ├── app.py               # Classe GtkApplication
│   ├── window.py            # Finestra principale
│   ├── msr605x/             # Modulo comunicazione dispositivo
│   │   ├── device.py        # Comunicazione USB HID
│   │   ├── commands.py      # Comandi alto livello
│   │   ├── constants.py     # Costanti protocollo
│   │   └── parser.py        # Parser dati tracce
│   ├── ui/                  # Componenti interfaccia
│   │   ├── read_panel.py    # Pannello lettura
│   │   ├── write_panel.py   # Pannello scrittura
│   │   ├── erase_panel.py   # Pannello cancellazione
│   │   └── settings_panel.py # Pannello impostazioni
│   └── utils/
│       └── file_io.py       # Gestione file
├── data/
│   ├── com.github.msr605x.desktop  # Entry desktop
│   ├── com.github.msr605x.svg      # Icona
│   ├── style.css                   # Stili CSS
│   └── 99-msr605x.rules            # Regole udev
├── tests/
│   └── test_parser.py       # Test unitari
├── pyproject.toml           # Configurazione progetto
├── requirements.txt         # Dipendenze Python
├── install.sh               # Script installazione
├── com.github.msr605x.yaml  # Manifest Flatpak
├── LICENSE                  # Licenza MIT
└── README.md                # Questo file
```

## Specifiche Tecniche

### Tracce Magnetiche

| Traccia | BPI | BPC | Max Caratteri | Tipo Dati |
|---------|-----|-----|---------------|-----------|
| Track 1 | 210 | 7   | 79            | Alfanumerico |
| Track 2 | 75  | 5   | 40            | Numerico |
| Track 3 | 210 | 5   | 107           | Numerico |

### Comandi Dispositivo

| Comando | Descrizione |
|---------|-------------|
| ESC a   | Reset dispositivo |
| ESC e   | Test comunicazione |
| ESC v   | Versione firmware |
| ESC r   | Lettura ISO |
| ESC m   | Lettura Raw |
| ESC w   | Scrittura ISO |
| ESC n   | Scrittura Raw |
| ESC c   | Cancellazione (mask: 0x01=T1, 0x02=T2, 0x04=T3) |
| ESC x   | Imposta Hi-Co |
| ESC y   | Imposta Lo-Co |

### Note Tecniche Importanti

- **Sentinel**: NON includere i sentinel (%, ;, ?) nei dati di scrittura - il dispositivo li aggiunge automaticamente
- **Formato Scrittura ISO**: `ESC w ESC s ESC 01 [data] ESC 02 [data] ESC 03 [data] ? FS`
- **Protocollo HID**: Pacchetti da 64 byte con header (bit7=first, bit6=last, bits0-5=length)

### Coercività

- **Hi-Co (Alta Coercività)**: 2750-4000 Oe
  - Più resistente alla smagnetizzazione
  - Usata per carte che richiedono maggiore durabilità

- **Lo-Co (Bassa Coercività)**: 300 Oe
  - Standard per la maggior parte delle carte
  - Più facile da codificare

## Risoluzione Problemi

### Il dispositivo non viene rilevato

1. Verifica che il dispositivo sia collegato:
   ```bash
   lsusb | grep -i "0801:0003"
   ```

2. Controlla i permessi:
   ```bash
   ls -la /dev/hidraw*
   ```

3. Assicurati che le regole udev siano installate:
   ```bash
   cat /etc/udev/rules.d/99-msr605x.rules
   ```

4. Ricarica le regole udev:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

### Errore "Permission denied"

Assicurati di essere nel gruppo `plugdev`:
```bash
groups $USER
sudo usermod -aG plugdev $USER
# Effettua logout e login
```

### La GUI non si avvia

Verifica che GTK4 e libadwaita siano installati:
```bash
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1
```

### Errori di lettura/scrittura

- Pulisci la testina del lettore
- Striscia la carta a velocità costante
- Verifica che la carta non sia danneggiata
- Prova a cambiare la coercività nelle impostazioni

## Compilazione Pacchetti

Se vuoi compilare i pacchetti da solo invece di scaricarli:

### Compilare il pacchetto .deb

```bash
# Installa le dipendenze di build
sudo apt install build-essential debhelper dh-python python3-all python3-setuptools devscripts

# Clona il repository
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu

# Compila il pacchetto
dpkg-buildpackage -us -uc -b

# Il pacchetto sarà in ../msr605x-utility_*.deb
```

### Compilare il pacchetto Snap

```bash
# Installa snapcraft
sudo apt install snapcraft

# Clona il repository
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu

# Compila lo snap
snapcraft

# Il pacchetto sarà in ./msr605x-utility_*.snap
```

### Script di Build Automatico

Usa lo script incluso per compilare facilmente:

```bash
# Compila entrambi i formati
./build-packages.sh --all

# Compila solo .deb
./build-packages.sh --deb

# Compila solo Snap
./build-packages.sh --snap

# Pulisci i file di build
./build-packages.sh --clean
```

I pacchetti compilati saranno nella cartella `dist/`.

## Sviluppo

### Eseguire i Test

```bash
# Installa dipendenze di sviluppo
pip install pytest pytest-cov

# Esegui i test
pytest tests/
```

### Contribuire

1. Fai un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/NuovaFunzionalita`)
3. Committa le modifiche (`git commit -m 'Aggiunta nuova funzionalità'`)
4. Pusha il branch (`git push origin feature/NuovaFunzionalita`)
5. Apri una Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per i dettagli.

## Crediti

- Ispirato dai progetti [eucalyp/MSR605](https://github.com/eucalyp/MSR605) e [bentbot/MSR605-GUI](https://github.com/bentbot/MSR605-GUI)
- Icona e design UI originali

## Disclaimer

Questo software è fornito esclusivamente per scopi educativi e legittimi. Gli utenti sono responsabili di garantire la conformità con tutte le leggi e i regolamenti applicabili riguardanti l'uso della tecnologia delle carte a banda magnetica.

## Contatti

- **Repository**: [https://github.com/Sam4000133/msr605x-ubuntu](https://github.com/Sam4000133/msr605x-ubuntu)
- **Issues**: [https://github.com/Sam4000133/msr605x-ubuntu/issues](https://github.com/Sam4000133/msr605x-ubuntu/issues)

---

Sviluppato con ❤️ per la community Linux

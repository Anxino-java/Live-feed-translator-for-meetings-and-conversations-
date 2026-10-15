# meeting co-pilot

a lightweight desktop overlay that captures real-time incoming meeting audio from your computer speakers, transcribes the speech, translates it to English when needed, and recommends contextual responses in the exact language the speaker used.

---

## features

* **direct system loopback capture**: records the other party's voice directly from your sound output without requiring bots to join the call.
* **multimodal gemini audio analysis**: streams raw audio bytes straight to Gemini models without relying on a separate speech-to-text pipeline.
* **dynamic model failover**: automatically cycles through alternative model endpoints if high demand or server limits occur.
* **always on top overlay**: stays docked above Google Meet, Zoom, Microsoft Teams, or browser tabs.
* **in-language response generation**: crafts immediate replies directly in the language spoken on the call, letting you read them out loud seamlessly.

---

## prerequisites

Before running the application, make sure you have the following installed on your machine:

1. **Python 3.10 or newer**: verify with `python --version` or `python3 --version`.
2. **Google Gemini API key**: generate a free key from Google AI Studio at https://aistudio.google.com.
3. **system audio loopback access**:
   * **Windows**: works natively via Windows WASAPI loopback.
   * **macOS**: requires a virtual loopback device such as BlackHole 2ch, or set input to the built-in microphone.
   * **Linux**: requires PulseAudio or PipeWire development libraries.

---

## installation commands

### 1. system level dependencies

#### Windows
No extra OS packages required.

#### macOS
If you use Homebrew:
```zsh
xcode-select --install
brew install blackhole-2ch







python dependencies

Install all required Python libraries via pip:
pip install google-genai soundcard numpy scipy

On macOS or Linux where pip is managed by the system, use:
pip3 install google-genai soundcard numpy scipy --break-system-packages

setting up the api key

The application reads your API key from either GEMINI_API_KEY or GOOGLE_API_KEY

Windows PowerShell
PowerShell

$env:GEMINI_API_KEY="your_api_key_here"

To persist it across all future PowerShell sessions:
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key_here", "User")

Windows Command Prompt
set GEMINI_API_KEY=your_api_key_here
setx GEMINI_API_KEY "your_api_key_here"

macOS and Linux Zsh
export GEMINI_API_KEY="your_api_key_here"
echo 'export GEMINI_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc

macOS and Linux Bash
export GEMINI_API_KEY="your_api_key_here"
echo 'export GEMINI_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc






step-by-step procedure to run

Follow these exact steps to launch and use the app during a live meeting:
step 1: prepare the project directory

Place meeting_copilot.py in your working folder and open your terminal in that folder:
cd path/to/your/folder



step 2: set the api key in your terminal

Run the export command for your operating system as shown in the configuration section above. Confirm it is active:

On Windows:
$env:GEMINI_API_KEY

On macOS or Linux:
echo $GEMINI_API_KEY

step 3: start the application

Launch the script:

On Windows:
python meeting_copilot.py

On macOS or Linux:

export TK_SILENCE_DEPRECATION=1
python3 meeting_copilot.py









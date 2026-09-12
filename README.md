<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# BANSHEE 🎯


## Basic Details
### Team Name: BANSHEE


### Team Members
- Team Lead: Induchoodan VS


### Project Description
BANSHEE is a cartoon blob ghost who starts inside one pygame bedroom, talks through a local Ollama model, then climbs onto your real Windows desktop when you close the window. She wanders as a mascot, chats (text or creepy goblin audio), opens harmless apps, and only leaves if you type bazinga.

### The Problem (that doesn't exist)
Your laptop is too obedient. Nothing haunts the taskbar. Closing a window actually closes things. That is unacceptable.

### The Solution (that nobody asked for)
A local poltergeist with free will. You poke furniture, she lands, she talks. You close the room — that is consent. She possesses the desktop, comments on whatever you are doing, and pretends your cursor asked her for directions. The kill spell is the word bazinga.

## Technical Details
### Technologies/Components Used
For Software:
- Python 3.11
- pygame (the one cartoon bedroom)
- tkinter (desktop mascot + chat box)
- Ollama + llama3.2:3b (local brain, no cloud)
- pyttsx3 / edge-tts (goblin voice)
- SpeechRecognition + PyAudio (your mic)
- pynput, Pillow, ctypes / Win32 (cursor, wallpaper, apps)



### Implementation
For Software:
# Installation
```
ollama pull llama3.2:3b
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

# Run
```
python main.py
```
Room only (no desktop haunt):
```
python main.py --house-only
```
Fake haunt on someone else's laptop:
```
python main.py --safe
```
Or double-click `run.bat` / `run-safe.bat`.

Type `bazinga` in the bottom-right chat box to banish her.

### Project Documentation
For Software:

# Screenshots (Add at least 3)
![Screenshot1](Add screenshot 1 here with proper name)
*Add caption explaining what this shows*

![Screenshot2](Add screenshot 2 here with proper name)
*Add caption explaining what this shows*

![Screenshot3](Add screenshot 3 here with proper name)
*Add caption explaining what this shows*

# Diagrams
![Workflow](Add your workflow/architecture diagram here)
*Add caption explaining your workflow*

For Hardware:

# Build Photos
![Components](Add photo of your components here)
*List out all components shown*

![Build](Add photos of build process here)
*Explain the build steps*

![Final](Add photo of final product here)
*Explain the final build*

### Project Demo
# Video
[Add your demo video link here]
*Explain what the video demonstrates*

# Additional Demos
[Add any extra demo materials/links]

## Team Contributions
- Induchoodan VS: everything — room, local LLM, desktop possession, mascot, chat, audio

---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)

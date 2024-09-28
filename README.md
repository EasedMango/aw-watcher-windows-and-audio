# Watchers
Two separate watchers
  1. Visible Windows
     - What windows are currently visible on screen(s) with window title and app name
  2. Audio Sources
     - What processes are currently playing audio
    
# Installation
  1. I just used ```pyinstaller --noconsole --onefile aw-watcher-visible-windows.py```
  2. moved the exe into:```C:\Users\%User%\AppData\Local\Programs\ActivityWatch\aw-server\aw-watcher-visible-windows```
  3. restart ActivityWatcher and activate it through the modules section of the tray application
  4. configuration files are generated on first run and located in the same place as the exe
  5. same steps for each but change from ```aw-watcher-visible-windows``` to ```aw-watcher-audio-sources```

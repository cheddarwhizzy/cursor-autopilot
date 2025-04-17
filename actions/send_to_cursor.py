import subprocess

def send_prompt(prompt):
    script = f'''
    tell application "System Events"
        tell application "Cursor" to activate
        delay 0.8
        keystroke "k" using {{command down}}
        delay 0.5
        key code 125
        delay 0.3
        key code 36
        delay 0.5
        keystroke "{prompt}"
        delay 0.3
        key code 36
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

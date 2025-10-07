# Installation & Environment

## Python Version Management (Recommended)

To ensure consistent Python version across different machines, use Pyenv:

1. **Install Pyenv:**
   ```bash
   brew install pyenv
   ```
2. **Add Pyenv to your shell configuration:**
   ```bash
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
   echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
   echo 'eval "$(pyenv init -)"' >> ~/.zshrc
   ```
3. **Install Python 3.13.2:**
   ```bash
   pyenv install 3.13.2
   ```
4. **Set the local Python version:**
   ```bash
   pyenv local 3.13.2
   ```

## Virtual Environment

Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

## Install Dependencies

Install required packages:
```bash
pip install flask
```

---

Return to [SETUP.md](./SETUP.md) for the main workflow.

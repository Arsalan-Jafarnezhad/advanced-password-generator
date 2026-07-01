# 🔐 Advanced Password Generator

A modern desktop password generator built with **Python** and **Tkinter** that creates strong, secure, and customizable passwords with an intuitive dark-themed interface.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## ✨ Features

- 🔐 Secure password generation using Python's `secrets` module
- 📏 Adjustable password length (4–128 characters)
- 🔤 Include:
  - Uppercase letters
  - Lowercase letters
  - Numbers
  - Special characters
- 🚫 Option to exclude ambiguous characters (`O`, `0`, `I`, `l`, `1`)
- ✅ Require at least one character from every selected character group
- 📊 Real-time password strength indicator
- 📋 One-click clipboard copy
- 🧹 Clear generated password
- 🖱️ Fully scrollable options panel
- ⌨️ Keyboard shortcuts
- 🌙 Modern dark interface
- 🔗 GitHub, Telegram and LinkedIn quick links
- 🪶 Lightweight standalone executable support via PyInstaller

---

## 📸 Preview

> *(Add a screenshot here)*

```
/images/screenshot.png
```

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/arsalan-jafarnezhad/advanced-password-generator.git
cd advanced-password-generator
```

### Install requirements

No external packages are required.

Python already includes:

- tkinter
- secrets
- string
- webbrowser

Simply run:

```bash
python password_generator.py
```

---

## 📦 Build Executable

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller ^
--onefile ^
--windowed ^
--icon icon.ico ^
--add-data "github.png;." ^
--add-data "telegram.png;." ^
--add-data "linkedin.png;." ^
password_generator.py
```

The executable will be generated inside:

```
dist/
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Generate password |
| Ctrl + C | Copy password |

---

## 🛡️ Password Strength

The application evaluates passwords based on:

- Password length
- Uppercase letters
- Lowercase letters
- Numbers
- Special characters

Strength levels:

- 🔴 Weak
- 🟡 Medium
- 🟢 Strong

---

## 📁 Project Structure

```
Advanced Password Generator/
│
├── password_generator.py
├── icon.ico
├── github.png
├── telegram.png
├── linkedin.png
├── README.md
└── LICENSE
```

---

## 🧠 Technologies Used

- Python
- Tkinter
- Python Secrets Module
- PyInstaller

---

## 🎯 Future Improvements

- Password history
- Password export
- Password import
- QR code generation
- Multiple themes
- Password entropy calculation
- Passphrase generator
- Random username generator
- Automatic update checker

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

Feel free to fork the repository and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**Arsalan Jafarnezhad**

GitHub: https://github.com/arsalan-jafarnezhad/

LinkedIn: https://linkedin.com/in/arsalan-jafarnezhad/

Telegram: https://t.me/axiomlite/

---

⭐ If you like this project, consider giving it a star on GitHub.
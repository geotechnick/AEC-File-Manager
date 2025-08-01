# 🏗️ AEC File Manager - Easy Installation Guide

**For Non-Programmers: Get Started in 3 Simple Steps!**

This guide will help you install and use the AEC File Manager without any programming knowledge. Just follow the pictures and instructions below.

---

## 📋 What You Need

✅ **Windows 10 or 11** (the version you're probably already using)  
✅ **15 minutes** of your time  
✅ **Internet connection** to download files  

That's it! No special technical knowledge required.

---

## 🚀 Step 1: Install Python (One-Time Setup)

Python is a free program that our AEC File Manager needs to run. Think of it like installing Microsoft Office - you do it once and then use it forever.

### Download Python:
1. **Go to**: https://www.python.org/downloads/
2. **Click the big yellow button** that says "Download Python 3.x.x"
3. **Wait for download** (it's about 25MB - like downloading 5-6 photos)

### Install Python:
1. **Find the file** you just downloaded (usually in your Downloads folder)
2. **Double-click** the file to start installation
3. **IMPORTANT**: ✅ Check the box "Add Python to PATH" at the bottom
4. **Click "Install Now"**
5. **Wait 2-3 minutes** for installation to complete
6. **Click "Close"** when finished

> 💡 **Why Python?** Many professional tools use Python because it's reliable and safe. It won't harm your computer.

---

## 🚀 Step 2: Download AEC File Manager

### Get the Files:
1. **Go to**: [AEC File Manager on GitHub](https://github.com/geotechnick/AEC-File-Manager)
2. **Click the green "Code" button**
3. **Click "Download ZIP"**
4. **Wait for download** (it's small - about 2MB)

### Extract the Files:
1. **Find the ZIP file** in your Downloads folder
2. **Right-click** on it and select "Extract All..."
3. **Choose where to put it** (Desktop is fine)
4. **Click "Extract"**
5. **Open the extracted folder** (should be called "AEC-File-Manager-main")

---

## 🚀 Step 3: Install AEC File Manager

### Simple Installation:
1. **Open the AEC File Manager folder** you just extracted
2. **Hold Shift and right-click** in an empty space inside the folder
3. **Select "Open PowerShell window here"** or "Open command window here"
4. **Type this command** and press Enter:
   ```
   pip install -r requirements.txt
   ```
5. **Wait 1-2 minutes** while it installs (you'll see text scrolling)
6. **Type this command** and press Enter:
   ```
   pip install -e .
   ```
7. **Wait another minute** for final installation

### Test Installation:
**Type this command** and press Enter:
```
aec status
```

If you see some text about "AEC Scanner Status" - **Congratulations! You're ready to go!** 🎉

---

## 🎯 Using AEC File Manager (Super Easy!)

### For Your First Project:

1. **Open Command Prompt or PowerShell** (Windows key + R, type "cmd", press Enter)
2. **Navigate to your project folder**:
   ```
   cd "C:\Path\To\Your\Project\Folder"
   ```
   (Replace with your actual project path)

3. **Set up your project** (creates all the folders automatically):
   ```
   aec
   ```
   That's it! Just type "aec" and it does everything automatically!

4. **Scan your files**:
   ```
   aec scan
   ```

5. **Get a beautiful report**:
   ```
   aec report
   ```

### Even Easier: Use the Folder Path

Instead of navigating, you can tell the program exactly where your project is:

```
aec init "C:\Users\YourName\Documents\My Project 2024"
aec scan "C:\Users\YourName\Documents\My Project 2024"
```

---

## 📖 What Each Command Does

| Command | What It Does | When to Use It |
|---------|-------------|----------------|
| `aec` | Sets up project folders automatically | First time with a new project |
| `aec scan` | Looks through all your files and organizes them | When you add new files |
| `aec report` | Creates a nice HTML report you can view in your browser | When you want to see project summary |
| `aec status` | Shows what's happening with your projects | To check if everything is working |

---

## 🆘 Need Help?

### If Something Goes Wrong:

**"Command not found" or "aec is not recognized":**
- Make sure you checked "Add Python to PATH" during Python installation
- Restart your computer and try again
- Try using `python -m aec_streamlined_cli` instead of `aec`

**"Permission denied" or "Access denied":**
- Right-click on Command Prompt and select "Run as administrator"
- Try the commands again

**Files not organizing correctly:**
- Make sure your file names follow AEC naming conventions
- Check that you're in the right project folder
- Try running `aec scan` again

### Get More Help:
- Email the project team: [GitHub Issues](https://github.com/geotechnick/AEC-File-Manager/issues)
- Include a screenshot of any error messages
- Tell us what you were trying to do when the problem happened

---

## ✨ Pro Tips for Non-Programmers

### Making It Even Easier:

1. **Create a Desktop Shortcut:**
   - Right-click on Desktop → New → Shortcut
   - Location: `cmd /k "cd /d C:\Your\Project\Path && aec"`
   - Name it "AEC Project Setup"

2. **Batch File for Multiple Projects:**
   - Create a text file called `scan_all_projects.bat`
   - Add these lines:
     ```
     aec scan "C:\Projects\Office Building 2024"
     aec scan "C:\Projects\Warehouse Project"
     aec scan "C:\Projects\School Renovation"
     pause
     ```
   - Double-click to scan all projects at once!

3. **Regular Scanning:**
   - Set a calendar reminder to run `aec scan` weekly
   - This keeps your project database up to date

### Understanding the Magic:

The AEC File Manager automatically:
- ✅ Creates 506 organized folders following industry standards
- ✅ Reads your file names and sorts them correctly
- ✅ Tracks revisions and project phases
- ✅ Generates professional reports
- ✅ Finds files instantly when you need them

All without you having to learn complicated file organization rules!

---

## 🎉 You're Done!

You now have a professional-grade AEC file management system that would cost thousands of dollars if you bought it from a software company. 

**Remember**: 
- Run `aec` once per project to set up folders
- Run `aec scan` whenever you add new files
- Run `aec report` when you need to show project status

**Questions?** Don't hesitate to ask for help - this tool is designed to make your work easier, not harder!

---

*Made with ❤️ for AEC professionals who want organized projects without the technical headaches.*
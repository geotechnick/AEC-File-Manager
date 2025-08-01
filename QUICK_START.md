# 🚀 Quick Start Guide - AEC File Manager

**Get organized in under 5 minutes!**

---

## 🎯 Just Want to Get Started? Follow These 3 Steps:

### Step 1: Open Command Prompt
- Press `Windows Key + R`
- Type `cmd` and press Enter
- A black window will open (this is normal!)

### Step 2: Go to Your Project Folder
Type this (replace with your actual project path):
```
cd "C:\Users\YourName\Documents\Your Project Name"
```

**Real examples:**
```
cd "C:\Users\John\Documents\Office Building 2024"
cd "C:\Projects\Warehouse Expansion"
cd "D:\Work\School Renovation Project"
```

### Step 3: Set Up Your Project
Just type:
```
aec
```

That's it! The program will:
- ✅ Create all 506 professional AEC folders
- ✅ Set up your project database
- ✅ Scan your existing files
- ✅ Organize everything automatically

---

## 📁 What Gets Created

After running `aec`, you'll see these main folders in your project:

```
YOUR_PROJECT_2024/
├── 00_PROJECT_MANAGEMENT/     (Contracts, schedules, budgets)
├── 01_CORRESPONDENCE/         (RFIs, submittals, emails)
├── 02_DRAWINGS/              (All your CAD files and PDFs)
├── 03_SPECIFICATIONS/        (Specs organized by CSI divisions)
├── 04_CALCULATIONS/          (Engineering calculations)
├── 05_REPORTS/               (Geotech, environmental, surveys)
├── 06_PERMITS_APPROVALS/     (Building permits, zoning)
├── 07_SITE_DOCUMENTATION/    (Photos, site visits)
├── 08_MODELS_CAD/            (BIM models, 3D files)
├── 09_CONSTRUCTION_ADMIN/     (Construction phase docs)
├── 10_CLOSEOUT/              (As-builts, O&M manuals)
├── 11_SPECIALTY_CONSULTANTS/ (Acoustics, lighting, etc.)
├── 12_STANDARDS_TEMPLATES/   (CAD standards, templates)
└── 13_ARCHIVE/               (Old versions, superseded files)
```

Each main folder contains dozens of organized subfolders following industry standards.

---

## 🔄 Daily Workflow

### When You Add New Files:
```
aec scan
```
Scans for new files and organizes them automatically.

### When You Need a Project Report:
```
aec report
```
Creates a beautiful HTML report you can share with clients or management.

### To Check Everything Is Working:
```
aec status
```
Shows your project statistics and system health.

---

## 💡 Smart File Naming Examples

The system automatically recognizes and organizes files with these naming patterns:

### Drawings:
- `CD_A_DWG_001_R3_031524.pdf` → Architectural drawing, sheet 001, revision 3
- `DD_S_DWG_S201_R1_022824.dwg` → Structural framing plan, revision 1
- `CD_M_SCH_M401_R0_041024.pdf` → Mechanical schedule, initial issue

### Reports:
- `PD_G_RPT_GEOTECH_R0_011024.pdf` → Geotechnical report, pre-design phase
- `SD_EN_STUDY_ENVIR_R1_012524.pdf` → Environmental study, schematic design

### Correspondence:
- `CA_M_RFI_001_R0_052024.pdf` → Mechanical RFI during construction
- `CA_S_SUB_STEEL_R1_060124.pdf` → Structural steel submittal

**Don't worry if your files aren't named this way yet!** The system is smart enough to organize most files correctly, and you can always move things manually if needed.

---

## 🆘 Common Questions

**Q: "I don't see all those folders!"**  
A: Run `aec` in your project folder first. This creates the folder structure.

**Q: "My files aren't organizing correctly"**  
A: The system works best with standard AEC file naming. For oddly named files, just drag them to the right folder manually.

**Q: "Can I use this for multiple projects?"**  
A: Absolutely! Just run `aec` in each project folder. Each project gets its own organization.

**Q: "What if I already have an organized project?"**  
A: The system won't move your existing files unless they follow the naming patterns. It will just add the missing folders and track what you have.

**Q: "Is this safe? Will it delete my files?"**  
A: The system never deletes files. It only reads, organizes, and creates folders. Your original files are always safe.

---

## 🎊 You're All Set!

You now have a professional AEC file management system that:
- Automatically organizes your project files
- Follows industry standards (CSI MasterFormat)
- Creates professional reports
- Tracks file revisions and metadata
- Works for any size project

**Remember these three commands:**
1. `aec` - Set up new project
2. `aec scan` - Update when you add files  
3. `aec report` - Create project summary

Need more help? Check out `EASY_INSTALL_GUIDE.md` for detailed instructions or visit our [GitHub page](https://github.com/geotechnick/AEC-File-Manager) for support.

---

*Happy organizing! 🏗️*
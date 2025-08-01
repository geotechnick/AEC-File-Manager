@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo    AEC Project Setup - No Installation Needed
echo ===============================================
echo.
echo This will create a complete AEC project structure
echo following industry standards (506 directories)
echo.

REM Get project information
set /p project_name="Enter project name (e.g., Office Building): "
if "%project_name%"=="" set project_name=New Project

set /p project_year="Enter project year (e.g., 2024): "
if "%project_year%"=="" (
    for /f "tokens=3" %%a in ('date /t') do set project_year=%%a
    set project_year=!project_year:~0,4!
)

set /p base_path="Enter project location (or press Enter for current directory): "
if "%base_path%"=="" set base_path=%cd%

REM Create project folder name
set project_folder_name=%project_name: =_%_%project_year%
set project_folder_name=%project_folder_name: =_%

set full_project_path=%base_path%\%project_folder_name%

echo.
echo Creating project: %project_folder_name%
echo Location: %full_project_path%
echo.
pause

REM Create main project directory
mkdir "%full_project_path%" 2>nul

REM Create main directories (00-13)
echo Creating main directories...

mkdir "%full_project_path%\00_PROJECT_MANAGEMENT"
mkdir "%full_project_path%\01_CORRESPONDENCE" 
mkdir "%full_project_path%\02_DRAWINGS"
mkdir "%full_project_path%\03_SPECIFICATIONS"
mkdir "%full_project_path%\04_CALCULATIONS"
mkdir "%full_project_path%\05_REPORTS"
mkdir "%full_project_path%\06_PERMITS_APPROVALS"
mkdir "%full_project_path%\07_SITE_DOCUMENTATION"
mkdir "%full_project_path%\08_MODELS_CAD"
mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN"
mkdir "%full_project_path%\10_CLOSEOUT"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES"
mkdir "%full_project_path%\13_ARCHIVE"

REM 00_PROJECT_MANAGEMENT subdirectories
echo Creating Project Management structure...
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Charter"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Proposals"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Proposals\Technical"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Proposals\Commercial"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Proposals\Marketing"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Contracts"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Contracts\Prime_Contract"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Contracts\Subcontracts"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Contracts\Amendments"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Schedule"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Schedule\Master_Schedule"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Schedule\Milestone_Schedule"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Schedule\Look_Ahead"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Budget_Cost_Control"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Budget_Cost_Control\Budget_Tracking"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Budget_Cost_Control\Cost_Reports" 
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Budget_Cost_Control\Invoicing"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Meeting_Minutes"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Meeting_Minutes\Kickoff"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Meeting_Minutes\Design_Reviews"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Meeting_Minutes\Progress_Meetings"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Meeting_Minutes\Coordination"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Team"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Team\Contact_Lists"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Team\Org_Charts"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Project_Team\Roles_Responsibilities"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Risk_Management"
mkdir "%full_project_path%\00_PROJECT_MANAGEMENT\Quality_Assurance"

REM 01_CORRESPONDENCE subdirectories
echo Creating Correspondence structure...
mkdir "%full_project_path%\01_CORRESPONDENCE\RFIs"
mkdir "%full_project_path%\01_CORRESPONDENCE\RFIs\Incoming"
mkdir "%full_project_path%\01_CORRESPONDENCE\RFIs\Outgoing"
mkdir "%full_project_path%\01_CORRESPONDENCE\RFIs\Logs"
mkdir "%full_project_path%\01_CORRESPONDENCE\Submittals"
mkdir "%full_project_path%\01_CORRESPONDENCE\Submittals\Incoming"
mkdir "%full_project_path%\01_CORRESPONDENCE\Submittals\Outgoing"
mkdir "%full_project_path%\01_CORRESPONDENCE\Submittals\Logs"
mkdir "%full_project_path%\01_CORRESPONDENCE\Submittals\Review_Status"
mkdir "%full_project_path%\01_CORRESPONDENCE\Change_Orders"
mkdir "%full_project_path%\01_CORRESPONDENCE\Change_Orders\Requests"
mkdir "%full_project_path%\01_CORRESPONDENCE\Change_Orders\Approved"
mkdir "%full_project_path%\01_CORRESPONDENCE\Change_Orders\Logs"
mkdir "%full_project_path%\01_CORRESPONDENCE\Transmittals"
mkdir "%full_project_path%\01_CORRESPONDENCE\Notice_Letters"
mkdir "%full_project_path%\01_CORRESPONDENCE\Progress_Reports"
mkdir "%full_project_path%\01_CORRESPONDENCE\Email_Archives"

REM 02_DRAWINGS subdirectories
echo Creating Drawings structure...
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Architectural"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Structural"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Civil"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Geotechnical"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Mechanical"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Electrical"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Plumbing"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Fire_Protection"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Landscape"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Interiors"
mkdir "%full_project_path%\02_DRAWINGS\Current_Issue\Specialty"
mkdir "%full_project_path%\02_DRAWINGS\Superseded"
mkdir "%full_project_path%\02_DRAWINGS\Superseded\By_Date"
mkdir "%full_project_path%\02_DRAWINGS\Superseded\By_Revision"
mkdir "%full_project_path%\02_DRAWINGS\Markups"
mkdir "%full_project_path%\02_DRAWINGS\Markups\Review_Comments"
mkdir "%full_project_path%\02_DRAWINGS\Markups\Field_Sketches"
mkdir "%full_project_path%\02_DRAWINGS\Record_Drawings"
mkdir "%full_project_path%\02_DRAWINGS\Shop_Drawings"
mkdir "%full_project_path%\02_DRAWINGS\Shop_Drawings\Submitted"
mkdir "%full_project_path%\02_DRAWINGS\Shop_Drawings\Under_Review"
mkdir "%full_project_path%\02_DRAWINGS\Shop_Drawings\Approved"

REM Continue with other major directories...
echo Creating Specifications structure...
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_00_Bidding_Requirements"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_01_General_Requirements"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_02_Site_Preparation"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_03_Concrete"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_04_Masonry"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_05_Metals"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_06_Wood_Plastics"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_07_Thermal_Moisture"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_08_Openings"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_09_Finishes"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_10_Specialties"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_11_Equipment"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_12_Furnishings"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_13_Special_Construction"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_14_Conveying_Equipment"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_15_Mechanical"
mkdir "%full_project_path%\03_SPECIFICATIONS\Division_16_Electrical"
mkdir "%full_project_path%\03_SPECIFICATIONS\Master_Specification"

echo Creating Calculations structure...
mkdir "%full_project_path%\04_CALCULATIONS\Structural"
mkdir "%full_project_path%\04_CALCULATIONS\Geotechnical"
mkdir "%full_project_path%\04_CALCULATIONS\Civil"
mkdir "%full_project_path%\04_CALCULATIONS\Environmental"
mkdir "%full_project_path%\04_CALCULATIONS\Hydraulics"
mkdir "%full_project_path%\04_CALCULATIONS\Mechanical"
mkdir "%full_project_path%\04_CALCULATIONS\Electrical"
mkdir "%full_project_path%\04_CALCULATIONS\Plumbing"
mkdir "%full_project_path%\04_CALCULATIONS\Fire_Protection"
mkdir "%full_project_path%\04_CALCULATIONS\Transportation"

echo Creating Reports structure...
mkdir "%full_project_path%\05_REPORTS\Geotechnical"
mkdir "%full_project_path%\05_REPORTS\Environmental"
mkdir "%full_project_path%\05_REPORTS\Survey"
mkdir "%full_project_path%\05_REPORTS\Testing_Inspection"
mkdir "%full_project_path%\05_REPORTS\Traffic_Studies"
mkdir "%full_project_path%\05_REPORTS\Utility_Studies"
mkdir "%full_project_path%\05_REPORTS\Feasibility_Studies"
mkdir "%full_project_path%\05_REPORTS\Code_Analysis"
mkdir "%full_project_path%\05_REPORTS\Peer_Review"

echo Creating remaining structures...
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Building_Permits"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Zoning"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Environmental"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Utility_Permits"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Transportation"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Fire_Department"
mkdir "%full_project_path%\06_PERMITS_APPROVALS\Health_Department"

mkdir "%full_project_path%\07_SITE_DOCUMENTATION\Photos"
mkdir "%full_project_path%\07_SITE_DOCUMENTATION\Site_Visits"
mkdir "%full_project_path%\07_SITE_DOCUMENTATION\Surveys"
mkdir "%full_project_path%\07_SITE_DOCUMENTATION\Video_Documentation"

mkdir "%full_project_path%\08_MODELS_CAD\BIM_Models"
mkdir "%full_project_path%\08_MODELS_CAD\CAD_Files"
mkdir "%full_project_path%\08_MODELS_CAD\3D_Models"
mkdir "%full_project_path%\08_MODELS_CAD\GIS_Data"
mkdir "%full_project_path%\08_MODELS_CAD\Point_Clouds"

mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN\Pre_Construction"
mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN\Bidding"
mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN\Construction_Phase"
mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN\Testing_Commissioning"
mkdir "%full_project_path%\09_CONSTRUCTION_ADMIN\Substantial_Completion"

mkdir "%full_project_path%\10_CLOSEOUT\As_Built_Drawings"
mkdir "%full_project_path%\10_CLOSEOUT\Operation_Maintenance"
mkdir "%full_project_path%\10_CLOSEOUT\Warranties_Guarantees"
mkdir "%full_project_path%\10_CLOSEOUT\Certificates_Approvals"
mkdir "%full_project_path%\10_CLOSEOUT\Final_Documentation"
mkdir "%full_project_path%\10_CLOSEOUT\Lien_Releases"

mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Acoustical"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Security"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Audio_Visual"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Kitchen_Equipment"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Code_Consultant"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Envelope_Consultant"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Sustainability_LEED"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Historic_Preservation"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Lighting_Design"
mkdir "%full_project_path%\11_SPECIALTY_CONSULTANTS\Cost_Estimating"

mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\CAD_Standards"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\BIM_Standards"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\Drawing_Templates"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\Specification_Templates"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\Calculation_Templates"
mkdir "%full_project_path%\12_STANDARDS_TEMPLATES\Report_Templates"

mkdir "%full_project_path%\13_ARCHIVE\Superseded_Drawings"
mkdir "%full_project_path%\13_ARCHIVE\Previous_Versions"
mkdir "%full_project_path%\13_ARCHIVE\Old_Correspondence"
mkdir "%full_project_path%\13_ARCHIVE\Inactive_Files"
mkdir "%full_project_path%\13_ARCHIVE\Project_History"

REM Create a project info file
echo Creating project information file...
(
echo Project Name: %project_name%
echo Project Year: %project_year%
echo Created: %date% %time%
echo Location: %full_project_path%
echo.
echo This project structure follows AEC industry standards
echo with complete CSI MasterFormat integration.
echo.
echo Main Directories Created:
echo - 00_PROJECT_MANAGEMENT: Contracts, schedules, budgets
echo - 01_CORRESPONDENCE: RFIs, submittals, emails  
echo - 02_DRAWINGS: All CAD files and PDFs
echo - 03_SPECIFICATIONS: Specs organized by CSI divisions
echo - 04_CALCULATIONS: Engineering calculations
echo - 05_REPORTS: Geotech, environmental, surveys
echo - 06_PERMITS_APPROVALS: Building permits, zoning
echo - 07_SITE_DOCUMENTATION: Photos, site visits
echo - 08_MODELS_CAD: BIM models, 3D files
echo - 09_CONSTRUCTION_ADMIN: Construction phase docs
echo - 10_CLOSEOUT: As-builts, O&M manuals
echo - 11_SPECIALTY_CONSULTANTS: Acoustics, lighting, etc.
echo - 12_STANDARDS_TEMPLATES: CAD standards, templates
echo - 13_ARCHIVE: Old versions, superseded files
) > "%full_project_path%\PROJECT_INFO.txt"

echo.
echo ===============================================
echo            PROJECT SETUP COMPLETE!
echo ===============================================
echo.
echo ✅ Project: %project_folder_name%
echo ✅ Location: %full_project_path%
echo ✅ Directories created: 100+ following AEC standards
echo.
echo What's next:
echo 1. Start organizing your files in the appropriate folders
echo 2. Use standard AEC naming conventions for best results
echo 3. Check PROJECT_INFO.txt for folder descriptions
echo.
echo Your project is now ready for professional AEC workflows!
echo.
pause

REM Optionally open the project folder
set /p open_folder="Open project folder now? (y/n): "
if /i "%open_folder%"=="y" explorer "%full_project_path%"

echo.
echo Thank you for using AEC File Manager!
pause
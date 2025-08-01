@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo   AEC File Organizer - No Installation Needed
echo ===============================================
echo.
echo This will help organize your AEC project files
echo into the appropriate directories based on file types.
echo.

set /p project_path="Enter your project folder path: "
if "%project_path%"=="" (
    echo Using current directory...
    set project_path=%cd%
)

REM Check if project path exists
if not exist "%project_path%" (
    echo Error: Project path does not exist!
    pause
    exit /b 1
)

cd /d "%project_path%"

echo.
echo Scanning for files to organize in: %project_path%
echo.

REM Initialize counters
set /a pdf_count=0
set /a dwg_count=0
set /a doc_count=0
set /a img_count=0
set /a other_count=0

REM Process PDF files
echo Organizing PDF files...
for /r %%f in (*.pdf) do (
    set filename=%%~nf
    set filepath=%%f
    
    REM Check if it's already in the right place
    echo !filepath! | findstr /i "02_DRAWINGS\|03_SPECIFICATIONS\|04_CALCULATIONS\|05_REPORTS" >nul
    if errorlevel 1 (
        REM Try to categorize based on filename patterns
        echo !filename! | findstr /i /c:"DWG" /c:"PLN" /c:"SEC" /c:"DTL" >nul
        if not errorlevel 1 (
            REM Drawing file
            if exist "02_DRAWINGS\Current_Issue" (
                copy "!filepath!" "02_DRAWINGS\Current_Issue\" >nul 2>&1
                if not errorlevel 1 (
                    echo   Moved drawing: %%~nxf
                    set /a pdf_count+=1
                )
            )
        ) else (
            echo !filename! | findstr /i /c:"SPEC" /c:"DIV" >nul
            if not errorlevel 1 (
                REM Specification file
                if exist "03_SPECIFICATIONS" (
                    copy "!filepath!" "03_SPECIFICATIONS\" >nul 2>&1
                    if not errorlevel 1 (
                        echo   Moved spec: %%~nxf
                        set /a pdf_count+=1
                    )
                )
            ) else (
                echo !filename! | findstr /i /c:"CALC" /c:"LOAD" /c:"SIZE" >nul
                if not errorlevel 1 (
                    REM Calculation file
                    if exist "04_CALCULATIONS" (
                        copy "!filepath!" "04_CALCULATIONS\" >nul 2>&1
                        if not errorlevel 1 (
                            echo   Moved calculation: %%~nxf
                            set /a pdf_count+=1
                        )
                    )
                ) else (
                    echo !filename! | findstr /i /c:"RPT" /c:"REPORT" /c:"STUDY" >nul
                    if not errorlevel 1 (
                        REM Report file
                        if exist "05_REPORTS" (
                            copy "!filepath!" "05_REPORTS\" >nul 2>&1
                            if not errorlevel 1 (
                                echo   Moved report: %%~nxf
                                set /a pdf_count+=1
                            )
                        )
                    )
                )
            )
        )
    )
)

REM Process DWG files
echo Organizing CAD files...
for /r %%f in (*.dwg *.dxf) do (
    set filepath=%%f
    
    REM Check if it's already in the right place
    echo !filepath! | findstr /i "02_DRAWINGS\|08_MODELS_CAD" >nul
    if errorlevel 1 (
        if exist "02_DRAWINGS\Current_Issue" (
            copy "!filepath!" "02_DRAWINGS\Current_Issue\" >nul 2>&1
            if not errorlevel 1 (
                echo   Moved CAD file: %%~nxf
                set /a dwg_count+=1
            )
        )
    )
)

REM Process Office documents
echo Organizing Office documents...
for /r %%f in (*.docx *.doc *.xlsx *.xls *.pptx *.ppt) do (
    set filename=%%~nf
    set filepath=%%f
    
    REM Check if it's already in the right place
    echo !filepath! | findstr /i "00_PROJECT_MANAGEMENT\|01_CORRESPONDENCE\|03_SPECIFICATIONS" >nul
    if errorlevel 1 (
        echo !filename! | findstr /i /c:"SPEC" /c:"SPECIFICATION" >nul
        if not errorlevel 1 (
            REM Specification document
            if exist "03_SPECIFICATIONS" (
                copy "!filepath!" "03_SPECIFICATIONS\" >nul 2>&1
                if not errorlevel 1 (
                    echo   Moved specification: %%~nxf
                    set /a doc_count+=1
                )
            )
        ) else (
            echo !filename! | findstr /i /c:"RFI" /c:"SUBMITTAL" /c:"TRANSMITTAL" >nul
            if not errorlevel 1 (
                REM Correspondence
                if exist "01_CORRESPONDENCE" (
                    copy "!filepath!" "01_CORRESPONDENCE\" >nul 2>&1
                    if not errorlevel 1 (
                        echo   Moved correspondence: %%~nxf
                        set /a doc_count+=1
                    )
                )
            ) else (
                REM General project management
                if exist "00_PROJECT_MANAGEMENT" (
                    copy "!filepath!" "00_PROJECT_MANAGEMENT\" >nul 2>&1
                    if not errorlevel 1 (
                        echo   Moved document: %%~nxf
                        set /a doc_count+=1
                    )
                )
            )
        )
    )
)

REM Process image files
echo Organizing images and photos...
for /r %%f in (*.jpg *.jpeg *.png *.tiff *.bmp *.gif) do (
    set filepath=%%f
    
    REM Check if it's already in the right place
    echo !filepath! | findstr /i "07_SITE_DOCUMENTATION\Photos" >nul
    if errorlevel 1 (
        if exist "07_SITE_DOCUMENTATION\Photos" (
            copy "!filepath!" "07_SITE_DOCUMENTATION\Photos\" >nul 2>&1
            if not errorlevel 1 (
                echo   Moved photo: %%~nxf
                set /a img_count+=1
            )
        )
    )
)

REM Process BIM/3D files
echo Organizing BIM and 3D files...
for /r %%f in (*.rvt *.rfa *.ifc *.3dm *.skp) do (
    set filepath=%%f
    
    REM Check if it's already in the right place
    echo !filepath! | findstr /i "08_MODELS_CAD" >nul
    if errorlevel 1 (
        if exist "08_MODELS_CAD\BIM_Models" (
            copy "!filepath!" "08_MODELS_CAD\BIM_Models\" >nul 2>&1
            if not errorlevel 1 (
                echo   Moved BIM file: %%~nxf
                set /a other_count+=1
            )
        )
    )
)

echo.
echo ===============================================
echo             FILE ORGANIZATION COMPLETE!
echo ===============================================
echo.
echo Files organized:
echo   📄 PDF files: %pdf_count%
echo   📐 CAD files: %dwg_count%
echo   📝 Documents: %doc_count%
echo   📷 Images: %img_count%
echo   🏗️ BIM/Other: %other_count%
echo.
echo Note: Files are COPIED, not moved. Original files remain in place.
echo You can now delete the originals if the copies are in the right locations.
echo.
echo For better organization:
echo 1. Use standard AEC naming conventions
echo 2. Manually review and adjust file locations as needed
echo 3. Consider using the full AEC File Manager for advanced features
echo.
pause

REM Optionally open the project folder
set /p open_folder="Open project folder to review organization? (y/n): "
if /i "%open_folder%"=="y" explorer "%project_path%"

echo.
echo Thank you for using AEC File Organizer!
pause
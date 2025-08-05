using AECFileProcessor.Core.Interfaces;
using Microsoft.Extensions.Logging;

namespace AECFileProcessor.Core.Services;

public class ProjectStructureService : IProjectStructureService
{
    private readonly ILogger<ProjectStructureService> _logger;

    private static readonly string[] StandardDirectories = new[]
    {
        "00_PROJECT_MANAGEMENT",
        "00_PROJECT_MANAGEMENT/Proposals",
        "00_PROJECT_MANAGEMENT/Contracts",
        "00_PROJECT_MANAGEMENT/Schedule",
        "00_PROJECT_MANAGEMENT/Budget",
        "00_PROJECT_MANAGEMENT/Meeting_Minutes",
        "00_PROJECT_MANAGEMENT/Team_Info",
        "00_PROJECT_MANAGEMENT/Risk_QA",
        
        "01_CORRESPONDENCE",
        "01_CORRESPONDENCE/RFIs",
        "01_CORRESPONDENCE/Submittals",
        "01_CORRESPONDENCE/Change_Orders",
        "01_CORRESPONDENCE/Transmittals",
        "01_CORRESPONDENCE/Progress_Reports",
        
        "02_DRAWINGS",
        "02_DRAWINGS/Current",
        "02_DRAWINGS/Current/Architectural",
        "02_DRAWINGS/Current/Structural",
        "02_DRAWINGS/Current/Civil",
        "02_DRAWINGS/Current/Mechanical",
        "02_DRAWINGS/Current/Electrical",
        "02_DRAWINGS/Current/Plumbing",
        "02_DRAWINGS/Current/Specialty",
        "02_DRAWINGS/Superseded",
        "02_DRAWINGS/Markups",
        "02_DRAWINGS/Shop_Drawings",
        
        "03_SPECIFICATIONS",
        "03_SPECIFICATIONS/Division_00_Bidding",
        "03_SPECIFICATIONS/Division_01_General",
        "03_SPECIFICATIONS/Division_02_Site",
        "03_SPECIFICATIONS/Division_03_Concrete",
        "03_SPECIFICATIONS/Division_04_Masonry",
        "03_SPECIFICATIONS/Division_05_Metals",
        "03_SPECIFICATIONS/Division_06_Wood",
        "03_SPECIFICATIONS/Division_07_Thermal",
        "03_SPECIFICATIONS/Division_08_Openings",
        "03_SPECIFICATIONS/Division_09_Finishes",
        "03_SPECIFICATIONS/Division_10_Specialties",
        "03_SPECIFICATIONS/Division_11_Equipment",
        "03_SPECIFICATIONS/Division_12_Furnishings",
        "03_SPECIFICATIONS/Division_13_Special",
        "03_SPECIFICATIONS/Division_14_Conveying",
        "03_SPECIFICATIONS/Division_15_Mechanical",
        "03_SPECIFICATIONS/Division_16_Electrical",
        "03_SPECIFICATIONS/Division_31_Earthwork",
        "03_SPECIFICATIONS/Division_32_Exterior",
        "03_SPECIFICATIONS/Division_33_Utilities",
        "03_SPECIFICATIONS/Master_Specification",
        
        "04_CALCULATIONS",
        "04_CALCULATIONS/Civil",
        "04_CALCULATIONS/Electrical",
        "04_CALCULATIONS/Mechanical", 
        "04_CALCULATIONS/Structural",
        "04_CALCULATIONS/Hydraulic",
        "04_CALCULATIONS/Geotechnical",
        "04_CALCULATIONS/Environmental",
        
        "05_REPORTS",
        "05_REPORTS/Geotechnical",
        "05_REPORTS/Environmental",
        "05_REPORTS/Survey",
        "05_REPORTS/Testing",
        "05_REPORTS/Studies",
        
        "06_PERMITS_APPROVALS",
        "06_PERMITS_APPROVALS/Building_Permits",
        "06_PERMITS_APPROVALS/Zoning",
        "06_PERMITS_APPROVALS/Environmental",
        "06_PERMITS_APPROVALS/Utilities",
        "06_PERMITS_APPROVALS/Other_Agencies",
        
        "07_SITE_DOCUMENTATION",
        "07_SITE_DOCUMENTATION/Photos",
        "07_SITE_DOCUMENTATION/Site_Visits",
        "07_SITE_DOCUMENTATION/Surveys",
        
        "08_MODELS_CAD",
        "08_MODELS_CAD/BIM_Models",
        "08_MODELS_CAD/CAD_Files",
        "08_MODELS_CAD/3D_Models",
        "08_MODELS_CAD/Point_Clouds",
        
        "09_CONSTRUCTION_ADMIN",
        "09_CONSTRUCTION_ADMIN/Pre_Construction",
        "09_CONSTRUCTION_ADMIN/Bidding",
        "09_CONSTRUCTION_ADMIN/Construction_Phase",
        "09_CONSTRUCTION_ADMIN/Completion",
        
        "10_CLOSEOUT",
        "10_CLOSEOUT/As_Built_Drawings",
        "10_CLOSEOUT/Operations_Manuals",
        "10_CLOSEOUT/Warranties",
        "10_CLOSEOUT/Final_Documentation",
        
        "11_CONSULTANTS",
        "12_ARCHIVE"
    };

    public ProjectStructureService(ILogger<ProjectStructureService> logger)
    {
        _logger = logger;
    }

    public async Task<bool> CreateProjectStructureAsync(string projectPath, string projectName, string projectNumber)
    {
        try
        {
            var fullProjectPath = Path.Combine(projectPath, $"{projectName}_{projectNumber}");
            
            _logger.LogInformation($"Creating project structure at: {fullProjectPath}");

            // Create root project directory
            if (!Directory.Exists(fullProjectPath))
            {
                Directory.CreateDirectory(fullProjectPath);
                _logger.LogInformation($"Created root project directory: {fullProjectPath}");
            }

            // Create all standard directories
            var createdCount = 0;
            var skippedCount = 0;

            foreach (var directory in StandardDirectories)
            {
                var fullPath = Path.Combine(fullProjectPath, directory);
                
                if (!Directory.Exists(fullPath))
                {
                    Directory.CreateDirectory(fullPath);
                    createdCount++;
                    _logger.LogDebug($"Created directory: {directory}");
                }
                else
                {
                    skippedCount++;
                    _logger.LogDebug($"Directory already exists: {directory}");
                }
            }

            // Create a project info file
            await CreateProjectInfoFileAsync(fullProjectPath, projectName, projectNumber);

            // Create README files in key directories
            await CreateReadmeFilesAsync(fullProjectPath);

            _logger.LogInformation($"Project structure creation completed. Created: {createdCount}, Skipped: {skippedCount}");
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Failed to create project structure at: {projectPath}");
            return false;
        }
    }

    public async Task<bool> ValidateProjectStructureAsync(string projectPath)
    {
        try
        {
            var status = await GetProjectStructureStatusAsync(projectPath);
            return status.IsValidStructure;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Failed to validate project structure at: {projectPath}");
            return false;
        }
    }

    public async Task<ProjectStructureStatus> GetProjectStructureStatusAsync(string projectPath)
    {
        var status = new ProjectStructureStatus();
        
        try
        {
            if (!Directory.Exists(projectPath))
            {
                status.MissingDirectories.AddRange(StandardDirectories);
                return status;
            }

            // Check if this looks like a project directory
            var dirName = Path.GetFileName(projectPath);
            var parts = dirName.Split('_');
            if (parts.Length >= 2)
            {
                status.ProjectName = string.Join("_", parts.Take(parts.Length - 1));
                status.ProjectNumber = parts.Last();
            }

            foreach (var directory in StandardDirectories)
            {
                var fullPath = Path.Combine(projectPath, directory);
                
                if (Directory.Exists(fullPath))
                {
                    status.ExistingDirectories.Add(directory);
                }
                else
                {
                    status.MissingDirectories.Add(directory);
                }
            }

            // Consider structure valid if at least 80% of directories exist
            var validThreshold = StandardDirectories.Length * 0.8;
            status.IsValidStructure = status.ExistingDirectories.Count >= validThreshold;

            _logger.LogDebug($"Project structure validation: {status.ExistingDirectories.Count}/{StandardDirectories.Length} directories exist");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Failed to get project structure status for: {projectPath}");
        }

        return status;
    }

    private async Task CreateProjectInfoFileAsync(string projectPath, string projectName, string projectNumber)
    {
        var infoFilePath = Path.Combine(projectPath, "PROJECT_INFO.md");
        
        if (File.Exists(infoFilePath))
        {
            _logger.LogDebug("PROJECT_INFO.md already exists, skipping creation");
            return;
        }

        var content = $"""
# {projectName}

**Project Number:** {projectNumber}  
**Created:** {DateTime.Now:yyyy-MM-dd HH:mm:ss}

## Directory Structure

This project follows the standard AEC directory structure:

- **00_PROJECT_MANAGEMENT** - Project management documents, contracts, schedules
- **01_CORRESPONDENCE** - RFIs, submittals, change orders, transmittals
- **02_DRAWINGS** - Current drawings, superseded versions, markups
- **03_SPECIFICATIONS** - Technical specifications by CSI division
- **04_CALCULATIONS** - Engineering calculations by discipline
- **05_REPORTS** - Geotechnical, environmental, survey reports
- **06_PERMITS_APPROVALS** - Building permits, zoning, regulatory approvals
- **07_SITE_DOCUMENTATION** - Photos, site visits, survey data
- **08_MODELS_CAD** - BIM models, CAD files, 3D models
- **09_CONSTRUCTION_ADMIN** - Construction phase documentation
- **10_CLOSEOUT** - As-built drawings, O&M manuals, warranties
- **11_CONSULTANTS** - Consultant-specific deliverables
- **12_ARCHIVE** - Archived project materials

## File Naming Convention

Files should follow the format: `Phase_DocumentType_Description_Revision_Date.ext`

**Example:** `CD_DWG_FloorPlan_Level1_R2_031524.pdf`

### Phase Codes
- **PD** - Pre-Design/Programming
- **SD** - Schematic Design
- **DD** - Design Development
- **CD** - Construction Documents
- **CA** - Construction Administration
- **CO** - Closeout

### Document Types
- **DWG** - Drawings/Plans
- **CALC** - Calculations
- **RPT** - Reports
- **SPEC** - Specifications
- **RFI** - Request for Information
- **SUB** - Submittal
- **CHG** - Change Order
""";

        await File.WriteAllTextAsync(infoFilePath, content);
        _logger.LogInformation("Created PROJECT_INFO.md file");
    }

    private Task CreateReadmeFilesAsync(string projectPath)
    {
        var readmeContent = new Dictionary<string, string>
        {
            ["02_DRAWINGS/Current"] = "Place current revision drawings here, organized by discipline.",
            ["02_DRAWINGS/Superseded"] = "Archive superseded drawing revisions here.",
            ["03_SPECIFICATIONS"] = "Technical specifications organized by CSI MasterFormat divisions.",
            ["04_CALCULATIONS"] = "Engineering calculations organized by discipline.",
            ["08_MODELS_CAD"] = "BIM models, CAD files, and 3D models.",
            ["10_CLOSEOUT"] = "Final project deliverables including as-built drawings and O&M manuals."
        };

        foreach (var (directory, content) in readmeContent)
        {
            var readmePath = Path.Combine(projectPath, directory, "README.md");
            var readmeDir = Path.GetDirectoryName(readmePath)!;
            
            if (Directory.Exists(readmeDir) && !File.Exists(readmePath))
            {
                File.WriteAllText(readmePath, $"# {Path.GetFileName(directory)}\n\n{content}");
                _logger.LogDebug($"Created README.md in {directory}");
            }
        }
        
        return Task.CompletedTask;
    }
}
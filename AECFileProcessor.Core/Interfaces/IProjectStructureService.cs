namespace AECFileProcessor.Core.Interfaces;

public interface IProjectStructureService
{
    Task<bool> CreateProjectStructureAsync(string projectPath, string projectName, string projectNumber);
    Task<bool> ValidateProjectStructureAsync(string projectPath);
    Task<ProjectStructureStatus> GetProjectStructureStatusAsync(string projectPath);
}

public class ProjectStructureStatus
{
    public bool IsValidStructure { get; set; }
    public List<string> MissingDirectories { get; set; } = new();
    public List<string> ExistingDirectories { get; set; } = new();
    public string ProjectName { get; set; } = string.Empty;
    public string ProjectNumber { get; set; } = string.Empty;
}
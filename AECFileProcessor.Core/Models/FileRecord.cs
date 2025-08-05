namespace AECFileProcessor.Core.Models;

public class FileRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string ProjectNumber { get; set; } = string.Empty;
    public string FilePath { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public string FileHash { get; set; } = string.Empty;
    public DateTime CreatedDate { get; set; }
    public DateTime ModifiedDate { get; set; }
    public DateTime ProcessedDate { get; set; }
    
    // AEC Classification
    public string Phase { get; set; } = string.Empty;
    public string Discipline { get; set; } = string.Empty;
    public string DocumentType { get; set; } = string.Empty;
    public string SheetNumber { get; set; } = string.Empty;
    public string RevisionNumber { get; set; } = string.Empty;
    public bool IsCurrentRevision { get; set; } = true;
    
    // Processing Status
    public ProcessingStatus Status { get; set; } = ProcessingStatus.Discovered;
    public string? ErrorMessage { get; set; }
    
    // Extracted Content (JSON for now)
    public string? ExtractedMetadata { get; set; }
}

public enum ProcessingStatus
{
    Discovered,
    Classified,
    Processing,
    Completed,
    Failed
}
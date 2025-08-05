namespace AECFileProcessor.Core.Models;

public class ExtractedMetadata
{
    public TitleBlockData? TitleBlock { get; set; }
    public List<string> TextContent { get; set; } = new();
    public List<string> TechnicalKeywords { get; set; } = new();
    public Dictionary<string, string> Properties { get; set; } = new();
    public DateTime ExtractedAt { get; set; } = DateTime.UtcNow;
    public double ConfidenceScore { get; set; }
}

public class TitleBlockData
{
    public string? ProjectName { get; set; }
    public string? SheetTitle { get; set; }
    public string? SheetNumber { get; set; }
    public string? RevisionNumber { get; set; }
    public string? DrawnBy { get; set; }
    public string? CheckedBy { get; set; }
    public string? Date { get; set; }
    public string? Scale { get; set; }
}
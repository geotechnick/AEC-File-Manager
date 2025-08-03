using AECFileProcessor.Core.Interfaces;
using AECFileProcessor.Core.Models;
using Microsoft.Extensions.Logging;
using System.Security.Cryptography;
using System.Text.Json;

namespace AECFileProcessor.Core.Services;

public class BasicFileProcessor : IFileProcessor
{
    private readonly IFileRepository _repository;
    private readonly ILogger<BasicFileProcessor> _logger;

    public BasicFileProcessor(IFileRepository repository, ILogger<BasicFileProcessor> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    public async Task<FileRecord> ProcessFileAsync(string filePath)
    {
        try
        {
            _logger.LogInformation($"Processing file: {filePath}");

            // Check if file already processed and unchanged
            var existingRecord = await _repository.GetByPathAsync(filePath);
            var fileInfo = new FileInfo(filePath);
            var currentHash = await CalculateFileHashAsync(filePath);

            if (existingRecord != null && existingRecord.FileHash == currentHash)
            {
                _logger.LogDebug($"File unchanged, skipping: {filePath}");
                return existingRecord;
            }

            var fileRecord = new FileRecord
            {
                FilePath = filePath,
                FileName = fileInfo.Name,
                FileSize = fileInfo.Length,
                FileHash = currentHash,
                CreatedDate = fileInfo.CreationTime,
                ModifiedDate = fileInfo.LastWriteTime,
                ProcessedDate = DateTime.UtcNow,
                Status = ProcessingStatus.Processing
            };

            // Extract project number from path
            fileRecord.ProjectNumber = ExtractProjectNumber(filePath);

            // Parse file name for AEC conventions
            ParseFileName(fileRecord);

            // Extract basic metadata
            var metadata = await ExtractBasicMetadataAsync(filePath);
            fileRecord.ExtractedMetadata = JsonSerializer.Serialize(metadata);

            fileRecord.Status = ProcessingStatus.Completed;

            var savedRecord = await _repository.SaveAsync(fileRecord);
            _logger.LogInformation($"Successfully processed file: {filePath}");

            return savedRecord;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Failed to process file: {filePath}");
            
            var errorRecord = new FileRecord
            {
                FilePath = filePath,
                FileName = Path.GetFileName(filePath),
                Status = ProcessingStatus.Failed,
                ErrorMessage = ex.Message,
                ProcessedDate = DateTime.UtcNow
            };

            return await _repository.SaveAsync(errorRecord);
        }
    }

    public async Task<bool> IsFileProcessedAsync(string filePath)
    {
        var record = await _repository.GetByPathAsync(filePath);
        return record != null && record.Status == ProcessingStatus.Completed;
    }

    public async Task<FileRecord?> GetFileRecordAsync(string filePath)
    {
        return await _repository.GetByPathAsync(filePath);
    }

    private async Task<string> CalculateFileHashAsync(string filePath)
    {
        using var stream = File.OpenRead(filePath);
        using var sha256 = SHA256.Create();
        var hash = await sha256.ComputeHashAsync(stream);
        return Convert.ToBase64String(hash);
    }

    private string ExtractProjectNumber(string filePath)
    {
        // Extract project number from standard directory structure: PROJECT_NAME_PROJECT_NUMBER
        var parts = filePath.Split(Path.DirectorySeparatorChar, StringSplitOptions.RemoveEmptyEntries);
        
        foreach (var part in parts)
        {
            // Look for standard naming: PROJECT_NAME_PROJECT_NUMBER
            var underscoreParts = part.Split('_');
            if (underscoreParts.Length >= 2)
            {
                var lastPart = underscoreParts[^1]; // Last part should be project number
                if (System.Text.RegularExpressions.Regex.IsMatch(lastPart, @"^\d{4,6}$"))
                {
                    return lastPart;
                }
            }
            
            // Fallback: Look for numeric project numbers
            if (System.Text.RegularExpressions.Regex.IsMatch(part, @"^\d{4,6}$"))
            {
                return part;
            }
            
            // Look for patterns like "Project12345"
            var match = System.Text.RegularExpressions.Regex.Match(part, @"[Pp]roject(\d+)");
            if (match.Success)
            {
                return match.Groups[1].Value;
            }
        }

        return "UNKNOWN";
    }

    private void ParseFileName(FileRecord fileRecord)
    {
        var fileName = Path.GetFileNameWithoutExtension(fileRecord.FileName);
        
        // Standard AEC naming convention: Phase_DocumentType_Description_Revision_Date
        // Example: CD_DWG_FloorPlan_Level1_R2_031524
        var parts = fileName.Split('_');
        
        if (parts.Length >= 4)
        {
            fileRecord.Phase = parts[0].ToUpper();
            fileRecord.DocumentType = parts[1].ToUpper();
            
            // Extract discipline from directory path or document type
            fileRecord.Discipline = InferDisciplineFromPath(fileRecord.FilePath) ?? 
                                  InferDisciplineFromDocumentType(parts[1]);
            
            // Description is parts[2] (could be multiple parts)
            var descriptionParts = new List<string> { parts[2] };
            
            // Find revision and date
            for (int i = 3; i < parts.Length; i++)
            {
                if (IsRevisionCode(parts[i]))
                {
                    fileRecord.RevisionNumber = parts[i];
                    // Date should be next part if it exists
                    if (i + 1 < parts.Length && IsDateCode(parts[i + 1]))
                    {
                        // Date is already in filename, we have file system dates
                        break;
                    }
                }
                else if (!IsDateCode(parts[i]))
                {
                    // Part of description
                    descriptionParts.Add(parts[i]);
                }
            }
            
            fileRecord.SheetNumber = string.Join("_", descriptionParts);
        }
        else
        {
            // Fallback parsing for non-standard names
            fileRecord.Discipline = InferDisciplineFromFileName(fileName);
            fileRecord.DocumentType = InferDocumentTypeFromExtension(fileRecord.FileName);
            fileRecord.Phase = InferPhaseFromPath(fileRecord.FilePath) ?? "UNKNOWN";
        }

        fileRecord.Status = ProcessingStatus.Classified;
    }

    private string DetermineDocumentType(string sheetNumber)
    {
        if (string.IsNullOrEmpty(sheetNumber))
            return "UNKNOWN";

        var firstChar = sheetNumber.ToUpper()[0];
        return firstChar switch
        {
            '1' => "PLAN",
            '2' => "ELEVATION", 
            '3' => "SECTION",
            '4' => "DETAIL",
            '5' => "SCHEDULE",
            '9' => "3D_VIEW",
            _ => "DRAWING"
        };
    }

    private string InferDisciplineFromFileName(string fileName)
    {
        var upperName = fileName.ToUpper();
        
        if (upperName.Contains("ARCH") || upperName.Contains("FLOOR") || upperName.Contains("PLAN"))
            return "A";
        if (upperName.Contains("STRUCT") || upperName.Contains("BEAM") || upperName.Contains("COLUMN"))
            return "S";
        if (upperName.Contains("MECH") || upperName.Contains("HVAC") || upperName.Contains("AIR"))
            return "M";
        if (upperName.Contains("ELEC") || upperName.Contains("POWER") || upperName.Contains("LIGHT"))
            return "E";
        if (upperName.Contains("PLUMB") || upperName.Contains("WATER") || upperName.Contains("SEWER"))
            return "P";
            
        return "UNKNOWN";
    }

    private string InferDocumentTypeFromExtension(string fileName)
    {
        var extension = Path.GetExtension(fileName).ToLower();
        
        return extension switch
        {
            ".dwg" => "DWG",
            ".pdf" => "DWG", // PDFs are often exported drawings
            ".docx" => "SPEC",
            ".xlsx" => "CALC",
            ".rvt" => "BIM",
            ".ifc" => "BIM",
            _ => "UNKNOWN"
        };
    }

    private string? InferDisciplineFromPath(string filePath)
    {
        var pathUpper = filePath.ToUpper();
        
        if (pathUpper.Contains("ARCHITECTURAL"))
            return "A";
        if (pathUpper.Contains("STRUCTURAL"))
            return "S";
        if (pathUpper.Contains("CIVIL"))
            return "C";
        if (pathUpper.Contains("MECHANICAL"))
            return "M";
        if (pathUpper.Contains("ELECTRICAL"))
            return "E";
        if (pathUpper.Contains("PLUMBING"))
            return "P";
            
        return null;
    }

    private string InferDisciplineFromDocumentType(string documentType)
    {
        var docTypeUpper = documentType.ToUpper();
        
        return docTypeUpper switch
        {
            "DWG" => "A", // Default to architectural for drawings
            "BIM" => "A",
            "CALC" => "S", // Calculations often structural
            "SPEC" => "A", // Default to architectural
            _ => "UNKNOWN"
        };
    }

    private string? InferPhaseFromPath(string filePath)
    {
        var pathUpper = filePath.ToUpper();
        
        if (pathUpper.Contains("PRE-DESIGN") || pathUpper.Contains("PROGRAMMING"))
            return "PD";
        if (pathUpper.Contains("SCHEMATIC"))
            return "SD";
        if (pathUpper.Contains("DESIGN_DEVELOPMENT") || pathUpper.Contains("DD"))
            return "DD";
        if (pathUpper.Contains("CONSTRUCTION_DOCUMENTS") || pathUpper.Contains("CD"))
            return "CD";
        if (pathUpper.Contains("CONSTRUCTION_ADMIN") || pathUpper.Contains("CA"))
            return "CA";
        if (pathUpper.Contains("CLOSEOUT") || pathUpper.Contains("CO"))
            return "CO";
            
        return null;
    }

    private bool IsRevisionCode(string part)
    {
        if (string.IsNullOrEmpty(part))
            return false;
            
        var upperPart = part.ToUpper();
        
        // Check for standard revision patterns
        return upperPart.StartsWith("R") ||  // R0, R1, R2, etc.
               upperPart.StartsWith("C") ||  // C01, C02, etc. (check prints)
               upperPart == "IFC" ||         // Issued for Construction
               upperPart == "IFB" ||         // Issued for Bidding
               upperPart == "IFP";           // Issued for Permit
    }

    private bool IsDateCode(string part)
    {
        if (string.IsNullOrEmpty(part) || part.Length != 6)
            return false;
            
        // Check if it's in MMDDYY format
        return part.All(char.IsDigit);
    }

    private Task<ExtractedMetadata> ExtractBasicMetadataAsync(string filePath)
    {
        var metadata = new ExtractedMetadata();
        var extension = Path.GetExtension(filePath).ToLower();

        // Basic file properties
        var fileInfo = new FileInfo(filePath);
        metadata.Properties["FileSize"] = fileInfo.Length.ToString();
        metadata.Properties["CreatedDate"] = fileInfo.CreationTime.ToString();
        metadata.Properties["ModifiedDate"] = fileInfo.LastWriteTime.ToString();
        metadata.Properties["Extension"] = extension;

        // TODO: Add specific extractors for different file types
        // For now, just basic file system metadata
        metadata.ConfidenceScore = 0.5; // Basic extraction only

        return Task.FromResult(metadata);
    }
}
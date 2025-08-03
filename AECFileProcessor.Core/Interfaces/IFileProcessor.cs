using AECFileProcessor.Core.Models;

namespace AECFileProcessor.Core.Interfaces;

public interface IFileProcessor
{
    Task<FileRecord> ProcessFileAsync(string filePath);
    Task<bool> IsFileProcessedAsync(string filePath);
    Task<FileRecord?> GetFileRecordAsync(string filePath);
}
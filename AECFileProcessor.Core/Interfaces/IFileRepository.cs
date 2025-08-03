using AECFileProcessor.Core.Models;

namespace AECFileProcessor.Core.Interfaces;

public interface IFileRepository
{
    Task<FileRecord> SaveAsync(FileRecord fileRecord);
    Task<FileRecord?> GetByPathAsync(string filePath);
    Task<FileRecord?> GetByIdAsync(Guid id);
    Task<IEnumerable<FileRecord>> GetByProjectAsync(string projectNumber);
    Task<IEnumerable<FileRecord>> GetAllAsync();
    Task<bool> ExistsAsync(string filePath);
    Task DeleteAsync(Guid id);
}
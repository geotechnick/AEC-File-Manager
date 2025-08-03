using AECFileProcessor.Core.Interfaces;
using AECFileProcessor.Core.Models;
using System.Collections.Concurrent;

namespace AECFileProcessor.Core.Services;

public class InMemoryFileRepository : IFileRepository
{
    private readonly ConcurrentDictionary<Guid, FileRecord> _records = new();
    private readonly ConcurrentDictionary<string, Guid> _pathIndex = new();

    public Task<FileRecord> SaveAsync(FileRecord fileRecord)
    {
        // Update existing or create new
        var existingId = _pathIndex.GetValueOrDefault(fileRecord.FilePath);
        if (existingId != Guid.Empty)
        {
            fileRecord.Id = existingId;
        }

        _records.AddOrUpdate(fileRecord.Id, fileRecord, (key, oldValue) => fileRecord);
        _pathIndex.AddOrUpdate(fileRecord.FilePath, fileRecord.Id, (key, oldValue) => fileRecord.Id);

        return Task.FromResult(fileRecord);
    }

    public Task<FileRecord?> GetByPathAsync(string filePath)
    {
        var id = _pathIndex.GetValueOrDefault(filePath);
        if (id != Guid.Empty && _records.TryGetValue(id, out var record))
        {
            return Task.FromResult<FileRecord?>(record);
        }
        return Task.FromResult<FileRecord?>(null);
    }

    public Task<FileRecord?> GetByIdAsync(Guid id)
    {
        _records.TryGetValue(id, out var record);
        return Task.FromResult<FileRecord?>(record);
    }

    public Task<IEnumerable<FileRecord>> GetByProjectAsync(string projectNumber)
    {
        var records = _records.Values
            .Where(r => r.ProjectNumber.Equals(projectNumber, StringComparison.OrdinalIgnoreCase))
            .ToList();
        return Task.FromResult<IEnumerable<FileRecord>>(records);
    }

    public Task<IEnumerable<FileRecord>> GetAllAsync()
    {
        return Task.FromResult<IEnumerable<FileRecord>>(_records.Values.ToList());
    }

    public Task<bool> ExistsAsync(string filePath)
    {
        return Task.FromResult(_pathIndex.ContainsKey(filePath));
    }

    public Task DeleteAsync(Guid id)
    {
        if (_records.TryRemove(id, out var record))
        {
            _pathIndex.TryRemove(record.FilePath, out _);
        }
        return Task.CompletedTask;
    }
}
using AECFileProcessor.Core.Interfaces;
using Microsoft.Extensions.Logging;
using System.Collections.Concurrent;

namespace AECFileProcessor.Core.Services;

public class LocalFileWatcher : IDisposable
{
    private readonly FileSystemWatcher _watcher;
    private readonly IFileProcessor _processor;
    private readonly ILogger<LocalFileWatcher> _logger;
    private readonly Timer _batchTimer;
    private readonly ConcurrentQueue<string> _fileQueue = new();
    private bool _disposed = false;

    public LocalFileWatcher(string watchPath, IFileProcessor processor, ILogger<LocalFileWatcher> logger)
    {
        _processor = processor;
        _logger = logger;
        
        _watcher = new FileSystemWatcher(watchPath)
        {
            IncludeSubdirectories = true,
            NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite | NotifyFilters.CreationTime
        };
        
        _watcher.Created += OnFileChanged;
        _watcher.Changed += OnFileChanged;
        _watcher.Renamed += OnFileRenamed;
        
        // Process files in batches every 5 seconds
        _batchTimer = new Timer(ProcessQueuedFiles, null, TimeSpan.FromSeconds(5), TimeSpan.FromSeconds(5));
    }

    public void StartWatching()
    {
        _watcher.EnableRaisingEvents = true;
        _logger.LogInformation($"Started watching {_watcher.Path}");
        
        // Process existing files
        _ = Task.Run(ProcessExistingFilesAsync);
    }

    public void StopWatching()
    {
        _watcher.EnableRaisingEvents = false;
        _logger.LogInformation("Stopped file watching");
    }

    private void OnFileChanged(object sender, FileSystemEventArgs e)
    {
        if (ShouldProcessFile(e.FullPath))
        {
            _fileQueue.Enqueue(e.FullPath);
            _logger.LogDebug($"Queued file: {e.FullPath}");
        }
    }

    private void OnFileRenamed(object sender, RenamedEventArgs e)
    {
        if (ShouldProcessFile(e.FullPath))
        {
            _fileQueue.Enqueue(e.FullPath);
        }
    }

    private bool ShouldProcessFile(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLower();
        var fileName = Path.GetFileName(filePath);
        
        // Skip temporary files
        if (fileName.StartsWith("~") || fileName.StartsWith(".tmp") || fileName.Contains("$"))
            return false;
            
        // Only process known AEC file types
        return extension is ".dwg" or ".pdf" or ".docx" or ".xlsx" or ".rvt" or ".ifc";
    }

    private async void ProcessQueuedFiles(object? state)
    {
        var filesToProcess = new List<string>();
        
        // Dequeue all pending files
        while (_fileQueue.TryDequeue(out var filePath))
        {
            if (File.Exists(filePath))
            {
                filesToProcess.Add(filePath);
            }
        }

        if (filesToProcess.Any())
        {
            _logger.LogInformation($"Processing batch of {filesToProcess.Count} files");
            
            // Process files in parallel with limited concurrency
            var semaphore = new SemaphoreSlim(Environment.ProcessorCount);
            var tasks = filesToProcess.Select(async filePath =>
            {
                await semaphore.WaitAsync();
                try
                {
                    await _processor.ProcessFileAsync(filePath);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"Failed to process file: {filePath}");
                }
                finally
                {
                    semaphore.Release();
                }
            });
            
            await Task.WhenAll(tasks);
        }
    }

    private Task ProcessExistingFilesAsync()
    {
        try
        {
            _logger.LogInformation("Scanning for existing files...");
            
            var files = Directory.GetFiles(_watcher.Path, "*", SearchOption.AllDirectories)
                .Where(ShouldProcessFile)
                .ToList();
                
            _logger.LogInformation($"Found {files.Count} existing files to process");
            
            foreach (var file in files)
            {
                _fileQueue.Enqueue(file);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to scan existing files");
        }
        
        return Task.CompletedTask;
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _watcher?.Dispose();
            _batchTimer?.Dispose();
            _disposed = true;
        }
    }
}
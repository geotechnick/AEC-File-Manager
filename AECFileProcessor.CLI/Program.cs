using AECFileProcessor.Core.Interfaces;
using AECFileProcessor.Core.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

class Program
{
    static async Task<int> Main(string[] args)
    {
        if (args.Length == 0)
        {
            ShowHelp();
            return 1;
        }

        var command = args[0].ToLower();
        
        try
        {
            return command switch
            {
                "watch" => await HandleWatchCommand(args),
                "process" => await HandleProcessCommand(args),
                "query" => await HandleQueryCommand(args),
                "create-project" => await HandleCreateProjectCommand(args),
                "validate-project" => await HandleValidateProjectCommand(args),
                "help" or "--help" or "-h" => ShowHelp(),
                _ => ShowUnknownCommand(command)
            };
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return 1;
        }
    }

    static async Task<int> HandleWatchCommand(string[] args)
    {
        var (path, database) = ParsePathAndDatabase(args);
        if (string.IsNullOrEmpty(path))
        {
            Console.WriteLine("Error: --path is required for watch command");
            Console.WriteLine("Usage: aec-processor watch --path <directory> [--database <path>]");
            return 1;
        }

        await RunWatchModeAsync(path, database);
        return 0;
    }

    static async Task<int> HandleProcessCommand(string[] args)
    {
        var (path, database) = ParsePathAndDatabase(args);
        if (string.IsNullOrEmpty(path))
        {
            Console.WriteLine("Error: --path is required for process command");
            Console.WriteLine("Usage: aec-processor process --path <directory> [--database <path>]");
            return 1;
        }

        await RunProcessModeAsync(path, database);
        return 0;
    }

    static async Task<int> HandleQueryCommand(string[] args)
    {
        var (_, database) = ParsePathAndDatabase(args);
        var project = ParseProject(args);

        await RunQueryModeAsync(project, database);
        return 0;
    }

    static async Task<int> HandleCreateProjectCommand(string[] args)
    {
        var (path, _) = ParsePathAndDatabase(args);
        var (projectName, projectNumber) = ParseProjectNameAndNumber(args);

        if (string.IsNullOrEmpty(path))
        {
            Console.WriteLine("Error: --path is required for create-project command");
            Console.WriteLine("Usage: aec-processor create-project --path <directory> --name <project-name> --number <project-number>");
            return 1;
        }

        if (string.IsNullOrEmpty(projectName) || string.IsNullOrEmpty(projectNumber))
        {
            Console.WriteLine("Error: --name and --number are required for create-project command");
            Console.WriteLine("Usage: aec-processor create-project --path <directory> --name <project-name> --number <project-number>");
            return 1;
        }

        await RunCreateProjectAsync(path, projectName, projectNumber);
        return 0;
    }

    static async Task<int> HandleValidateProjectCommand(string[] args)
    {
        var (path, _) = ParsePathAndDatabase(args);

        if (string.IsNullOrEmpty(path))
        {
            Console.WriteLine("Error: --path is required for validate-project command");
            Console.WriteLine("Usage: aec-processor validate-project --path <project-directory>");
            return 1;
        }

        await RunValidateProjectAsync(path);
        return 0;
    }

    static (string path, string database) ParsePathAndDatabase(string[] args)
    {
        string path = "";
        string database = "aec_files.db";

        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "--path" || args[i] == "-p")
                path = args[i + 1];
            else if (args[i] == "--database" || args[i] == "-d")
                database = args[i + 1];
        }

        return (path, database);
    }

    static string? ParseProject(string[] args)
    {
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "--project")
                return args[i + 1];
        }
        return null;
    }

    static (string name, string number) ParseProjectNameAndNumber(string[] args)
    {
        string name = "";
        string number = "";

        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "--name")
                name = args[i + 1];
            else if (args[i] == "--number")
                number = args[i + 1];
        }

        return (name, number);
    }

    static int ShowHelp()
    {
        Console.WriteLine("AEC File Processor - Local Version");
        Console.WriteLine();
        Console.WriteLine("Commands:");
        Console.WriteLine("  watch             Watch a directory for file changes");
        Console.WriteLine("  process           Process files in a directory once");
        Console.WriteLine("  query             Query processed files");
        Console.WriteLine("  create-project    Create standard AEC project directory structure");
        Console.WriteLine("  validate-project  Validate existing project structure");
        Console.WriteLine("  help              Show this help message");
        Console.WriteLine();
        Console.WriteLine("Options:");
        Console.WriteLine("  --path, -p        Directory path to watch/process/create");
        Console.WriteLine("  --database, -d    SQLite database path (default: aec_files.db)");
        Console.WriteLine("  --project         Project number to query");
        Console.WriteLine("  --name            Project name (for create-project)");
        Console.WriteLine("  --number          Project number (for create-project)");
        Console.WriteLine();
        Console.WriteLine("Examples:");
        Console.WriteLine("  aec-processor watch --path \"C:\\Projects\\Project123\"");
        Console.WriteLine("  aec-processor process --path \"C:\\Projects\" --database mydb.db");
        Console.WriteLine("  aec-processor query --project 12345");
        Console.WriteLine("  aec-processor create-project --path \"C:\\Projects\" --name \"OfficeBuilding\" --number \"12345\"");
        Console.WriteLine("  aec-processor validate-project --path \"C:\\Projects\\OfficeBuilding_12345\"");
        return 0;
    }

    static int ShowUnknownCommand(string command)
    {
        Console.WriteLine($"Unknown command: {command}");
        Console.WriteLine("Run 'aec-processor help' for usage information.");
        return 1;
    }

    static async Task RunWatchModeAsync(string watchPath, string databasePath)
    {
        var host = CreateHost(databasePath);
        var services = host.Services;
        
        var logger = services.GetRequiredService<ILogger<Program>>();
        var processor = services.GetRequiredService<IFileProcessor>();
        
        logger.LogInformation($"Starting file watcher for: {watchPath}");
        logger.LogInformation($"Database: {databasePath}");
        
        using var watcher = new LocalFileWatcher(watchPath, processor, 
            services.GetRequiredService<ILogger<LocalFileWatcher>>());
        
        watcher.StartWatching();
        
        logger.LogInformation("File watcher started. Press Ctrl+C to stop...");
        
        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (s, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };
        
        try
        {
            await Task.Delay(-1, cts.Token);
        }
        catch (OperationCanceledException)
        {
            logger.LogInformation("Shutting down...");
        }
    }

    static async Task RunProcessModeAsync(string processPath, string databasePath)
    {
        var host = CreateHost(databasePath);
        var services = host.Services;
        
        var logger = services.GetRequiredService<ILogger<Program>>();
        var processor = services.GetRequiredService<IFileProcessor>();
        
        logger.LogInformation($"Processing files in: {processPath}");
        
        var files = Directory.GetFiles(processPath, "*.*", SearchOption.AllDirectories)
            .Where(f => ShouldProcessFile(f))
            .ToList();
            
        logger.LogInformation($"Found {files.Count} files to process");
        
        var processed = 0;
        var errors = 0;
        
        foreach (var file in files)
        {
            try
            {
                await processor.ProcessFileAsync(file);
                processed++;
                
                if (processed % 10 == 0)
                {
                    logger.LogInformation($"Processed {processed}/{files.Count} files");
                }
            }
            catch (Exception ex)
            {
                logger.LogError(ex, $"Failed to process: {file}");
                errors++;
            }
        }
        
        logger.LogInformation($"Processing complete. Processed: {processed}, Errors: {errors}");
    }

    static async Task RunQueryModeAsync(string? projectNumber, string databasePath)
    {
        var host = CreateHost(databasePath);
        var repository = host.Services.GetRequiredService<IFileRepository>();
        
        if (string.IsNullOrEmpty(projectNumber))
        {
            // Show all files
            var allFiles = await repository.GetAllAsync();
            var projects = allFiles.GroupBy(f => f.ProjectNumber).ToList();
            
            Console.WriteLine($"Found {projects.Count} projects:");
            foreach (var project in projects)
            {
                Console.WriteLine($"  {project.Key}: {project.Count()} files");
            }
        }
        else
        {
            // Show files for specific project
            var files = await repository.GetByProjectAsync(projectNumber);
            var fileList = files.ToList();
            
            Console.WriteLine($"Project {projectNumber}: {fileList.Count} files");
            Console.WriteLine();
            
            foreach (var file in fileList.Take(20)) // Limit output
            {
                Console.WriteLine($"  {file.FileName}");
                Console.WriteLine($"    Discipline: {file.Discipline}, Phase: {file.Phase}");
                Console.WriteLine($"    Status: {file.Status}, Modified: {file.ModifiedDate:yyyy-MM-dd HH:mm}");
                Console.WriteLine();
            }
            
            if (fileList.Count > 20)
            {
                Console.WriteLine($"  ... and {fileList.Count - 20} more files");
            }
        }
    }

    static async Task RunCreateProjectAsync(string basePath, string projectName, string projectNumber)
    {
        var host = CreateHostForStructure();
        var structureService = host.Services.GetRequiredService<IProjectStructureService>();
        var logger = host.Services.GetRequiredService<ILogger<Program>>();

        logger.LogInformation($"Creating project structure for {projectName}_{projectNumber} at {basePath}");

        var success = await structureService.CreateProjectStructureAsync(basePath, projectName, projectNumber);

        if (success)
        {
            var projectPath = Path.Combine(basePath, $"{projectName}_{projectNumber}");
            Console.WriteLine($"Successfully created project structure at: {projectPath}");
            Console.WriteLine();
            Console.WriteLine("Project structure includes:");
            Console.WriteLine("- Standard AEC directory structure");
            Console.WriteLine("- PROJECT_INFO.md with naming conventions");
            Console.WriteLine("- README files in key directories");
            Console.WriteLine();
            Console.WriteLine("You can now:");
            Console.WriteLine($"  - Watch for changes: dotnet run watch --path \"{projectPath}\"");
            Console.WriteLine($"  - Process existing files: dotnet run process --path \"{projectPath}\"");
        }
        else
        {
            Console.WriteLine("Failed to create project structure. Check logs for details.");
        }
    }

    static async Task RunValidateProjectAsync(string projectPath)
    {
        var host = CreateHostForStructure();
        var structureService = host.Services.GetRequiredService<IProjectStructureService>();
        var logger = host.Services.GetRequiredService<ILogger<Program>>();

        logger.LogInformation($"Validating project structure at: {projectPath}");

        var status = await structureService.GetProjectStructureStatusAsync(projectPath);

        Console.WriteLine($"Project Structure Validation for: {Path.GetFileName(projectPath)}");
        Console.WriteLine();

        if (!string.IsNullOrEmpty(status.ProjectName))
        {
            Console.WriteLine($"Project Name: {status.ProjectName}");
            Console.WriteLine($"Project Number: {status.ProjectNumber}");
            Console.WriteLine();
        }

        Console.WriteLine($"Structure Status: {(status.IsValidStructure ? "VALID" : "INCOMPLETE")}");
        Console.WriteLine($"Existing Directories: {status.ExistingDirectories.Count}");
        Console.WriteLine($"Missing Directories: {status.MissingDirectories.Count}");
        Console.WriteLine();

        if (status.MissingDirectories.Any())
        {
            Console.WriteLine("Missing directories:");
            foreach (var missing in status.MissingDirectories.Take(10))
            {
                Console.WriteLine($"  - {missing}");
            }
            if (status.MissingDirectories.Count > 10)
            {
                Console.WriteLine($"  ... and {status.MissingDirectories.Count - 10} more");
            }
            Console.WriteLine();
        }

        if (status.IsValidStructure)
        {
            Console.WriteLine("Project structure is valid and ready for use.");
        }
        else
        {
            Console.WriteLine("Consider running create-project to complete the structure.");
        }
    }

    static IHost CreateHost(string databasePath)
    {
        return Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddLogging(builder =>
                {
                    builder.AddConsole();
                    builder.SetMinimumLevel(LogLevel.Information);
                });
                
                // Use in-memory repository for now (will add SQLite later)
                services.AddSingleton<IFileRepository, InMemoryFileRepository>();
                services.AddSingleton<IFileProcessor, BasicFileProcessor>();
                services.AddSingleton<IProjectStructureService, ProjectStructureService>();
            })
            .Build();
    }

    static IHost CreateHostForStructure()
    {
        return Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddLogging(builder =>
                {
                    builder.AddConsole();
                    builder.SetMinimumLevel(LogLevel.Information);
                });
                
                services.AddSingleton<IProjectStructureService, ProjectStructureService>();
            })
            .Build();
    }

    static bool ShouldProcessFile(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLower();
        var fileName = Path.GetFileName(filePath);
        
        if (fileName.StartsWith("~") || fileName.StartsWith(".tmp") || fileName.Contains("$"))
            return false;
            
        return extension is ".dwg" or ".pdf" or ".docx" or ".xlsx" or ".rvt" or ".ifc";
    }
}

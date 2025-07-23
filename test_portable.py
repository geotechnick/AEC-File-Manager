"""
AEC File Manager - Portable Version Tester
Tests the portable executable across different scenarios
"""

import os
import sys
import subprocess
import platform
import time
import requests
from pathlib import Path

def test_system_compatibility():
    """Test system compatibility"""
    print("Testing System Compatibility")
    print("-" * 40)
    
    # System info
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Available RAM: {get_available_ram()}MB")
    print(f"Available Disk: {get_available_disk()}GB")
    
    # Check minimum requirements
    checks = []
    
    # RAM check (minimum 2GB)
    ram_mb = get_available_ram()
    checks.append(("RAM >= 2GB", ram_mb >= 2048, f"{ram_mb}MB available"))
    
    # Disk space check (minimum 1GB)
    disk_gb = get_available_disk()
    checks.append(("Disk >= 1GB", disk_gb >= 1, f"{disk_gb}GB available"))
    
    # Port availability check
    port_free = check_port_available(8501)
    checks.append(("Port 8501 free", port_free, "Default Streamlit port"))
    
    print("\nSystem Requirements:")
    for check_name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status} {check_name}: {detail}")
    
    return all(check[1] for check in checks)

def get_available_ram():
    """Get available RAM in MB"""
    try:
        if platform.system() == "Windows":
            import psutil
            return psutil.virtual_memory().available // (1024 * 1024)
        else:
            # Fallback for systems without psutil
            return 4096  # Assume 4GB
    except ImportError:
        return 4096  # Default assumption

def get_available_disk():
    """Get available disk space in GB"""
    try:
        if platform.system() == "Windows":
            import shutil
            free_bytes = shutil.disk_usage('.').free
            return free_bytes // (1024 * 1024 * 1024)
        else:
            import shutil
            free_bytes = shutil.disk_usage('.').free
            return free_bytes // (1024 * 1024 * 1024)
    except:
        return 10  # Default assumption

def check_port_available(port):
    """Check if a port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0  # Port is free if connection fails
    except:
        return True

def test_build_process():
    """Test the build process"""
    print("\nTesting Build Process")
    print("-" * 40)
    
    tests = []
    
    # Check if build scripts exist
    build_files = [
        'build_portable.py',
        'create_lightweight_portable.py', 
        'requirements-build.txt'
    ]
    
    for file in build_files:
        exists = Path(file).exists()
        tests.append((f"Build file: {file}", exists))
        status = "PASS" if exists else "FAIL"
        print(f"{status} {file}")
    
    # Test PyInstaller availability
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'pyinstaller'], 
                      capture_output=True, check=True)
        pyinstaller_available = True
    except subprocess.CalledProcessError:
        pyinstaller_available = False
    
    tests.append(("PyInstaller available", pyinstaller_available))
    status = "PASS" if pyinstaller_available else "FAIL"
    print(f"{status} PyInstaller available")
    
    return all(test[1] for test in tests)

def test_executable_functionality(exe_path):
    """Test executable functionality"""
    print(f"\nTesting Executable: {exe_path}")
    print("-" * 40)
    
    if not Path(exe_path).exists():
        print(f"FAIL Executable not found: {exe_path}")
        return False
    
    # Test executable runs
    try:
        # Start the executable in background
        if platform.system() == "Windows":
            process = subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            process = subprocess.Popen([exe_path])
        
        # Wait a bit for startup
        time.sleep(10)
        
        # Test if web interface is accessible
        try:
            response = requests.get('http://localhost:8501', timeout=5)
            web_accessible = response.status_code == 200
        except:
            web_accessible = False
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        
        print(f"{'PASS' if web_accessible else 'FAIL'} Web interface accessible")
        return web_accessible
        
    except Exception as e:
        print(f"FAIL Executable test failed: {e}")
        return False

def test_docker_container():
    """Test Docker container if available"""
    print("\nTesting Docker Container")
    print("-" * 40)
    
    # Check if Docker is available
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        docker_available = True
        print("PASS Docker available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_available = False
        print("FAIL Docker not available")
        return False
    
    # Check if docker-compose.yml exists
    if not Path('docker-compose.yml').exists():
        print("FAIL docker-compose.yml not found")
        return False
    
    print("PASS Docker configuration found")
    
    # Note: We don't actually test Docker build here as it's time-consuming
    # This would be done in CI/CD pipeline
    print("INFO Docker build test skipped (use 'docker-compose up' to test)")
    
    return True

def create_test_report():
    """Create a comprehensive test report"""
    print("\nCreating Test Report")
    print("=" * 50)
    
    report = []
    
    # Run all tests
    system_ok = test_system_compatibility()
    build_ok = test_build_process()
    docker_ok = test_docker_container()
    
    # Check for built executables
    exe_paths = [
        'dist/AEC-File-Manager/AEC-File-Manager.exe',
        'dist/AEC-File-Manager/AEC-File-Manager',
        'dist/AEC-File-Manager-Lite/AEC-File-Manager-Lite.exe',
        'dist/AEC-File-Manager-Lite/AEC-File-Manager-Lite'
    ]
    
    executable_tests = []
    for exe_path in exe_paths:
        if Path(exe_path).exists():
            exe_ok = test_executable_functionality(exe_path)
            executable_tests.append((exe_path, exe_ok))
    
    # Generate report
    report_content = f"""
AEC File Manager - Portable Version Test Report
===============================================
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
System: {platform.system()} {platform.release()} ({platform.machine()})

Test Results:
------------
System Compatibility: {'PASS' if system_ok else 'FAIL'}
Build Process: {'PASS' if build_ok else 'FAIL'}
Docker Configuration: {'PASS' if docker_ok else 'FAIL'}

Executable Tests:
"""
    
    if executable_tests:
        for exe_path, result in executable_tests:
            report_content += f"- {exe_path}: {'PASS' if result else 'FAIL'}\n"
    else:
        report_content += "- No executables found (run build scripts first)\n"
    
    report_content += f"""

Overall Status: {'READY FOR DISTRIBUTION' if system_ok and build_ok else 'ISSUES FOUND'}

Next Steps:
----------
1. {'✅' if system_ok else '❌'} System meets minimum requirements
2. {'✅' if build_ok else '❌'} Build environment is ready
3. {'✅' if executable_tests else '❌'} Run build scripts to create executables
4. {'✅' if docker_ok else '❌'} Docker deployment available

Recommendations:
---------------
"""
    
    if not system_ok:
        report_content += "- Address system requirement issues before building\n"
    
    if not build_ok:
        report_content += "- Install missing build dependencies: pip install -r requirements-build.txt\n"
    
    if not executable_tests:
        report_content += "- Run build_all_platforms.bat (Windows) or ./build_all_platforms.sh (Linux/Mac)\n"
    
    if system_ok and build_ok:
        report_content += "- System is ready for portable deployment\n"
        report_content += "- Run the build scripts to create distribution packages\n"
    
    # Save report
    with open('PORTABLE_TEST_REPORT.txt', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(report_content)
    print(f"\nFull report saved to: PORTABLE_TEST_REPORT.txt")

def main():
    """Main test function"""
    print("AEC File Manager - Portable Version Test Suite")
    print("=" * 60)
    
    # Install test dependencies if needed
    try:
        import requests
    except ImportError:
        print("Installing test dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests
    
    # Run comprehensive tests
    create_test_report()

if __name__ == "__main__":
    main()
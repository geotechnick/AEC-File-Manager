"""
Database Manager

Handles all database operations including schema management, data insertion,
querying, and backup operations for the AEC Directory Scanner system.
"""

import os
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import contextmanager
from dataclasses import asdict
from queue import Queue, Empty
from functools import lru_cache
import weakref


class ConnectionPool:
    """
    Database connection pool for improved performance and resource management.
    """
    
    def __init__(self, connection_string: str, max_connections: int = 10, timeout: int = 30):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = Queue(maxsize=max_connections)
        self._all_connections = weakref.WeakSet()
        self._lock = threading.Lock()
        self.db_type = 'postgresql' if connection_string.startswith(('postgresql://', 'postgres://')) else 'sqlite'
        
        # Initialize pool with connections
        self._populate_pool()
    
    def _populate_pool(self):
        """Initialize the connection pool."""
        for _ in range(self.max_connections):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self):
        """Create a new database connection."""
        try:
            if self.db_type == 'sqlite':
                db_path = Path(self.connection_string)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                
                conn = sqlite3.connect(
                    self.connection_string,
                    timeout=self.timeout,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                
            else:  # PostgreSQL
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(
                    self.connection_string,
                    connect_timeout=self.timeout,
                    cursor_factory=RealDictCursor
                )
                conn.autocommit = False
            
            self._all_connections.add(conn)
            return conn
            
        except Exception as e:
            logging.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            # Try to get connection from pool with timeout
            try:
                conn = self._pool.get(timeout=5)
            except Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if len(self._all_connections) < self.max_connections:
                        conn = self._create_connection()
                    else:
                        # Wait longer for connection
                        conn = self._pool.get(timeout=self.timeout)
            
            if conn is None:
                raise RuntimeError("Unable to obtain database connection")
            
            # Test connection health
            try:
                if self.db_type == 'sqlite':
                    conn.execute("SELECT 1")
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
            except Exception:
                # Connection is stale, create new one
                conn.close()
                conn = self._create_connection()
                if conn is None:
                    raise RuntimeError("Unable to create new database connection")
            
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        else:
            if conn:
                try:
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self._pool.put_nowait(conn)
                except:
                    # Pool is full, close connection
                    conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        # Close pooled connections
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        # Close any remaining connections
        for conn in list(self._all_connections):
            try:
                conn.close()
            except Exception:
                pass


class DatabaseManager:
    """
    Manages database operations with support for both SQLite and PostgreSQL,
    optimized for read-heavy workloads with proper indexing and JSON metadata storage.
    """
    
    # Database schema version
    SCHEMA_VERSION = "1.0.0"
    
    # SQL schema definitions
    SCHEMA_SQL = {
        "projects": """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_number VARCHAR(50) UNIQUE NOT NULL,
                project_name VARCHAR(255) NOT NULL,
                base_path VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active'
            )
        """,
        
        "directories": """
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id),
                folder_path VARCHAR(500) NOT NULL,
                folder_name VARCHAR(255) NOT NULL,
                parent_id INTEGER REFERENCES directories(id),
                folder_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scanned TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (parent_id) REFERENCES directories(id)
            )
        """,
        
        "files": """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id),
                directory_id INTEGER REFERENCES directories(id),
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) UNIQUE NOT NULL,
                file_extension VARCHAR(10),
                file_size BIGINT,
                file_hash VARCHAR(64),
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                last_accessed TIMESTAMP,
                first_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_count INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT true,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (directory_id) REFERENCES directories(id)
            )
        """,
        
        "file_metadata": """
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER REFERENCES files(id),
                metadata_type VARCHAR(50),
                metadata_json TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extractor_version VARCHAR(20),
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """,
        
        "aec_file_metadata": """
            CREATE TABLE IF NOT EXISTS aec_file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER REFERENCES files(id),
                project_number VARCHAR(50),
                discipline_code VARCHAR(10),
                document_type VARCHAR(50),
                phase_code VARCHAR(10),
                drawing_number VARCHAR(50),
                revision VARCHAR(20),
                sheet_number VARCHAR(20),
                csi_division VARCHAR(10),
                csi_section VARCHAR(20),
                author VARCHAR(100),
                checker VARCHAR(100),
                approver VARCHAR(100),
                issue_date DATE,
                keywords TEXT,
                related_files TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """,
        
        "scan_history": """
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id),
                scan_type VARCHAR(50),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                files_scanned INTEGER,
                files_added INTEGER,
                files_updated INTEGER,
                files_removed INTEGER,
                errors_encountered INTEGER,
                scan_status VARCHAR(20),
                error_details TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """,
        
        "schema_version": """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(20) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """
    }
    
    # Index definitions for performance optimization
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)",
        "CREATE INDEX IF NOT EXISTS idx_files_extension ON files(file_extension)",
        "CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_at)",
        "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_metadata_file_id ON file_metadata(file_id)",
        "CREATE INDEX IF NOT EXISTS idx_metadata_type ON file_metadata(metadata_type)",
        "CREATE INDEX IF NOT EXISTS idx_aec_metadata_file_id ON aec_file_metadata(file_id)",
        "CREATE INDEX IF NOT EXISTS idx_aec_metadata_project ON aec_file_metadata(project_number)",
        "CREATE INDEX IF NOT EXISTS idx_aec_metadata_discipline ON aec_file_metadata(discipline_code)",
        "CREATE INDEX IF NOT EXISTS idx_aec_metadata_drawing ON aec_file_metadata(drawing_number)",
        "CREATE INDEX IF NOT EXISTS idx_directories_project_id ON directories(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_directories_parent_id ON directories(parent_id)",
        "CREATE INDEX IF NOT EXISTS idx_scan_history_project_id ON scan_history(project_id)"
    ]
    
    def __init__(
        self, 
        connection_string: str,
        logger: Optional[logging.Logger] = None,
        connection_timeout: int = 30,
        max_connections: int = 10
    ):
        """
        Initialize the Database Manager.
        
        Args:
            connection_string: Database connection string (SQLite file path or PostgreSQL URL)
            logger: Optional logger instance
            connection_timeout: Connection timeout in seconds
            max_connections: Maximum number of connections in pool
        """
        self.connection_string = connection_string
        self.logger = logger or logging.getLogger(__name__)
        self.connection_timeout = connection_timeout
        
        # Initialize connection pool
        self.connection_pool = ConnectionPool(
            connection_string, 
            max_connections=max_connections, 
            timeout=connection_timeout
        )
        
        # Determine database type
        if connection_string.startswith(('postgresql://', 'postgres://')):
            self.db_type = 'postgresql'
            try:
                import psycopg2
                self.db_module = psycopg2
            except ImportError:
                raise ImportError("psycopg2 is required for PostgreSQL support")
        else:
            self.db_type = 'sqlite'
            self.db_module = sqlite3
        
        # Query cache for frequently used queries
        self._query_cache = {}
        self._cache_lock = threading.Lock()
            
        self.logger.info(f"Initialized DatabaseManager with {self.db_type} backend and connection pool")
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection from the connection pool.
        """
        with self.connection_pool.get_connection() as conn:
            yield conn
    
    def close_connection(self):
        """Close all connections in the pool."""
        self.connection_pool.close_all()
    
    @lru_cache(maxsize=128)
    def _get_cached_query_result(self, query: str, params_hash: str, cache_timeout: int = 300):
        """
        Get cached query result. Only for read-only queries.
        
        Args:
            query: SQL query
            params_hash: Hash of query parameters
            cache_timeout: Cache timeout in seconds
            
        Returns:
            Cached result or None if not cached/expired
        """
        cache_key = f"{query}:{params_hash}"
        
        with self._cache_lock:
            if cache_key in self._query_cache:
                result, timestamp = self._query_cache[cache_key]
                if time.time() - timestamp < cache_timeout:
                    return result
                else:
                    # Remove expired entry
                    del self._query_cache[cache_key]
        
        return None
    
    def _cache_query_result(self, query: str, params_hash: str, result: Any):
        """Cache query result."""
        cache_key = f"{query}:{params_hash}"
        
        with self._cache_lock:
            # Limit cache size
            if len(self._query_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self._query_cache.keys(), 
                                   key=lambda k: self._query_cache[k][1])[:100]
                for key in oldest_keys:
                    del self._query_cache[key]
            
            self._query_cache[cache_key] = (result, time.time())
    
    def _execute_cached_query(self, query: str, params: tuple = (), cache: bool = False, cache_timeout: int = 300):
        """
        Execute query with optional caching for read operations.
        
        Args:
            query: SQL query
            params: Query parameters
            cache: Whether to use caching
            cache_timeout: Cache timeout in seconds
            
        Returns:
            Query results
        """
        if cache and query.strip().upper().startswith('SELECT'):
            # Generate hash of parameters for cache key
            import hashlib
            params_hash = hashlib.md5(str(params).encode()).hexdigest()
            
            # Try to get from cache first
            cached_result = self._get_cached_query_result(query, params_hash, cache_timeout)
            if cached_result is not None:
                return cached_result
        
        # Execute query
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                if self.db_type == 'sqlite':
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    result = [dict(row) for row in cursor.fetchall()]
                
                # Cache result if caching is enabled
                if cache:
                    self._cache_query_result(query, params_hash, result)
                
                return result
            else:
                return cursor.rowcount
    
    def initialize_database(self) -> bool:
        """
        Initialize the database schema and create all necessary tables and indexes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create all tables
                for table_name, schema_sql in self.SCHEMA_SQL.items():
                    try:
                        cursor.execute(schema_sql)
                        self.logger.debug(f"Created table: {table_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to create table {table_name}: {e}")
                        return False
                
                # Create indexes
                for index_sql in self.INDEXES:
                    try:
                        cursor.execute(index_sql)
                    except Exception as e:
                        self.logger.warning(f"Failed to create index: {e}")
                
                # Insert schema version
                try:
                    cursor.execute(
                        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                        (self.SCHEMA_VERSION, "Initial schema creation")
                    )
                except Exception:
                    # Schema version might already exist
                    pass
                
                self.logger.info("Database initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
    
    def insert_project(self, project_data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a new project record.
        
        Args:
            project_data: Dictionary containing project information
            
        Returns:
            Project ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO projects (project_number, project_name, base_path, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        project_data["project_number"],
                        project_data["project_name"],
                        project_data["base_path"],
                        project_data.get("status", "active")
                    )
                )
                
                project_id = cursor.lastrowid
                self.logger.info(f"Inserted project: {project_data['project_number']} (ID: {project_id})")
                return project_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert project: {e}")
            return None
    
    def insert_file_record(self, file_data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a new file record.
        
        Args:
            file_data: Dictionary containing file information
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if file already exists
                cursor.execute("SELECT id FROM files WHERE file_path = ?", (file_data["file_path"],))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    file_id = existing[0]
                    cursor.execute(
                        """
                        UPDATE files SET
                            file_name = ?, file_extension = ?, file_size = ?, file_hash = ?,
                            modified_at = ?, last_accessed = ?, last_scanned = CURRENT_TIMESTAMP,
                            scan_count = scan_count + 1, is_active = true
                        WHERE id = ?
                        """,
                        (
                            file_data["file_name"],
                            file_data.get("file_extension"),
                            file_data.get("file_size"),
                            file_data.get("file_hash"),
                            file_data.get("modified_at"),
                            file_data.get("last_accessed"),
                            file_id
                        )
                    )
                    self.logger.debug(f"Updated existing file record: {file_data['file_path']}")
                    
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO files (
                            project_id, directory_id, file_name, file_path, file_extension,
                            file_size, file_hash, created_at, modified_at, last_accessed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            file_data["project_id"],
                            file_data.get("directory_id"),
                            file_data["file_name"],
                            file_data["file_path"],
                            file_data.get("file_extension"),
                            file_data.get("file_size"),
                            file_data.get("file_hash"),
                            file_data.get("created_at"),
                            file_data.get("modified_at"),
                            file_data.get("last_accessed")
                        )
                    )
                    file_id = cursor.lastrowid
                    self.logger.debug(f"Inserted new file record: {file_data['file_path']} (ID: {file_id})")
                
                return file_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert file record: {e}")
            return None
    
    def update_file_metadata(self, file_id: int, metadata: Dict[str, Any]) -> bool:
        """
        Update or insert metadata for a file.
        
        Args:
            file_id: File ID
            metadata: Dictionary containing metadata information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert general metadata
                for metadata_type, metadata_content in metadata.items():
                    if metadata_type == "aec_metadata":
                        # Handle AEC-specific metadata separately
                        self._insert_aec_metadata(cursor, file_id, metadata_content)
                    else:
                        # Insert as JSON metadata
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO file_metadata 
                            (file_id, metadata_type, metadata_json, extractor_version)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                file_id,
                                metadata_type,
                                json.dumps(metadata_content, default=str),
                                metadata_content.get("extractor_version", "1.0")
                            )
                        )
                
                self.logger.debug(f"Updated metadata for file ID: {file_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update file metadata: {e}")
            return False
    
    def _insert_aec_metadata(self, cursor, file_id: int, aec_data: Dict[str, Any]) -> None:
        """Insert AEC-specific metadata into structured table."""
        # First, delete existing AEC metadata for this file
        cursor.execute("DELETE FROM aec_file_metadata WHERE file_id = ?", (file_id,))
        
        # Convert lists to JSON strings for storage
        keywords_json = json.dumps(aec_data.get("keywords", []))
        related_files_json = json.dumps(aec_data.get("related_files", []))
        
        cursor.execute(
            """
            INSERT INTO aec_file_metadata (
                file_id, project_number, discipline_code, document_type, phase_code,
                drawing_number, revision, sheet_number, csi_division, csi_section,
                author, checker, approver, issue_date, keywords, related_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                aec_data.get("project_number"),
                aec_data.get("discipline_code"),
                aec_data.get("document_type"),
                aec_data.get("phase_code"),
                aec_data.get("drawing_number"),
                aec_data.get("revision"),
                aec_data.get("sheet_number"),
                aec_data.get("csi_division"),
                aec_data.get("csi_section"),
                aec_data.get("author"),
                aec_data.get("checker"),
                aec_data.get("approver"),
                aec_data.get("issue_date"),
                keywords_json,
                related_files_json
            )
        )
    
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve file information by file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information or None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT f.*, p.project_name, p.project_number
                    FROM files f
                    LEFT JOIN projects p ON f.project_id = p.id
                    WHERE f.file_path = ?
                    """,
                    (file_path,)
                )
                
                result = cursor.fetchone()
                if result:
                    return dict(result) if self.db_type == 'sqlite' else dict(zip([d[0] for d in cursor.description], result))
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get file by path: {e}")
            return None
    
    def get_files_by_project(self, project_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all files for a specific project.
        
        Args:
            project_id: Project ID
            limit: Optional limit on number of results
            
        Returns:
            List of dictionaries containing file information
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT f.*, d.folder_name, d.folder_path
                    FROM files f
                    LEFT JOIN directories d ON f.directory_id = d.id
                    WHERE f.project_id = ? AND f.is_active = true
                    ORDER BY f.file_path
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (project_id,))
                results = cursor.fetchall()
                
                if self.db_type == 'sqlite':
                    return [dict(row) for row in results]
                else:
                    columns = [d[0] for d in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            self.logger.error(f"Failed to get files by project: {e}")
            return []
    
    def get_files_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve files based on search criteria.
        
        Args:
            criteria: Dictionary containing search criteria
            
        Returns:
            List of dictionaries containing file information
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic query based on criteria
                where_clauses = ["f.is_active = true"]
                params = []
                
                if "project_id" in criteria:
                    where_clauses.append("f.project_id = ?")
                    params.append(criteria["project_id"])
                
                if "file_extension" in criteria:
                    where_clauses.append("f.file_extension = ?")
                    params.append(criteria["file_extension"])
                
                if "discipline_code" in criteria:
                    where_clauses.append("aec.discipline_code = ?")
                    params.append(criteria["discipline_code"])
                
                if "document_type" in criteria:
                    where_clauses.append("aec.document_type = ?")
                    params.append(criteria["document_type"])
                
                if "modified_after" in criteria:
                    where_clauses.append("f.modified_at > ?")
                    params.append(criteria["modified_after"])
                
                if "file_size_min" in criteria:
                    where_clauses.append("f.file_size >= ?")
                    params.append(criteria["file_size_min"])
                
                if "file_size_max" in criteria:
                    where_clauses.append("f.file_size <= ?")
                    params.append(criteria["file_size_max"])
                
                query = f"""
                    SELECT f.*, aec.discipline_code, aec.document_type, aec.drawing_number
                    FROM files f
                    LEFT JOIN aec_file_metadata aec ON f.id = aec.file_id
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY f.modified_at DESC
                """
                
                if "limit" in criteria:
                    query += f" LIMIT {criteria['limit']}"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                if self.db_type == 'sqlite':
                    return [dict(row) for row in results]
                else:
                    columns = [d[0] for d in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            self.logger.error(f"Failed to get files by criteria: {e}")
            return []
    
    def record_scan_session(self, scan_data: Dict[str, Any]) -> Optional[int]:
        """
        Record a scan session in the scan history.
        
        Args:
            scan_data: Dictionary containing scan session information
            
        Returns:
            Scan session ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO scan_history (
                        project_id, scan_type, start_time, end_time, files_scanned,
                        files_added, files_updated, files_removed, errors_encountered,
                        scan_status, error_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scan_data["project_id"],
                        scan_data["scan_type"],
                        scan_data["start_time"],
                        scan_data["end_time"],
                        scan_data.get("files_scanned", 0),
                        scan_data.get("files_added", 0),
                        scan_data.get("files_updated", 0),
                        scan_data.get("files_removed", 0),
                        scan_data.get("errors_encountered", 0),
                        scan_data.get("scan_status", "completed"),
                        json.dumps(scan_data.get("errors", []))
                    )
                )
                
                session_id = cursor.lastrowid
                self.logger.info(f"Recorded scan session: {session_id}")
                return session_id
                
        except Exception as e:
            self.logger.error(f"Failed to record scan session: {e}")
            return None
    
    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary containing project statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Basic file counts
                cursor.execute(
                    "SELECT COUNT(*), SUM(file_size) FROM files WHERE project_id = ? AND is_active = true",
                    (project_id,)
                )
                result = cursor.fetchone()
                stats["total_files"] = result[0] or 0
                stats["total_size_bytes"] = result[1] or 0
                
                # File types distribution
                cursor.execute(
                    """
                    SELECT file_extension, COUNT(*), SUM(file_size)
                    FROM files 
                    WHERE project_id = ? AND is_active = true 
                    GROUP BY file_extension 
                    ORDER BY COUNT(*) DESC
                    """,
                    (project_id,)
                )
                file_types = cursor.fetchall()
                stats["file_types"] = [
                    {"extension": row[0] or "no_extension", "count": row[1], "total_size": row[2] or 0}
                    for row in file_types
                ]
                
                # AEC metadata statistics
                cursor.execute(
                    """
                    SELECT discipline_code, COUNT(*)
                    FROM aec_file_metadata aec
                    JOIN files f ON aec.file_id = f.id
                    WHERE f.project_id = ? AND f.is_active = true
                    GROUP BY discipline_code
                    """,
                    (project_id,)
                )
                discipline_stats = cursor.fetchall()
                stats["disciplines"] = [
                    {"discipline": row[0] or "unknown", "count": row[1]}
                    for row in discipline_stats
                ]
                
                # Recent scan information
                cursor.execute(
                    """
                    SELECT scan_type, end_time, files_scanned, scan_status
                    FROM scan_history
                    WHERE project_id = ?
                    ORDER BY end_time DESC
                    LIMIT 5
                    """,
                    (project_id,)
                )
                recent_scans = cursor.fetchall()
                stats["recent_scans"] = [
                    {
                        "scan_type": row[0],
                        "end_time": row[1],
                        "files_scanned": row[2],
                        "status": row[3]
                    }
                    for row in recent_scans
                ]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get project statistics: {e}")
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where backup will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db_type == 'sqlite':
                # SQLite backup using built-in backup API
                with self.get_connection() as source_conn:
                    backup_conn = sqlite3.connect(backup_path)
                    source_conn.backup(backup_conn)
                    backup_conn.close()
                    
            else:
                # PostgreSQL backup using pg_dump (requires pg_dump in PATH)
                import subprocess
                result = subprocess.run(
                    ["pg_dump", self.connection_string, "-f", backup_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.logger.error(f"pg_dump failed: {result.stderr}")
                    return False
            
            self.logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False
    
    def migrate_schema(self, target_version: str) -> bool:
        """
        Migrate database schema to target version.
        
        Args:
            target_version: Target schema version
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current version
                cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
                result = cursor.fetchone()
                current_version = result[0] if result else "0.0.0"
                
                if current_version == target_version:
                    self.logger.info("Database is already at target version")
                    return True
                
                # Apply migrations (placeholder for future migration logic)
                self.logger.info(f"Migration from {current_version} to {target_version} not implemented yet")
                return True
                
        except Exception as e:
            self.logger.error(f"Schema migration failed: {e}")
            return False
    
    def cleanup_orphaned_records(self, project_id: int) -> int:
        """
        Clean up orphaned records for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Number of records cleaned up
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cleaned_count = 0
                
                # Remove metadata for non-existent files
                cursor.execute(
                    """
                    DELETE FROM file_metadata 
                    WHERE file_id NOT IN (SELECT id FROM files WHERE project_id = ?)
                    """,
                    (project_id,)
                )
                cleaned_count += cursor.rowcount
                
                # Remove AEC metadata for non-existent files
                cursor.execute(
                    """
                    DELETE FROM aec_file_metadata 
                    WHERE file_id NOT IN (SELECT id FROM files WHERE project_id = ?)
                    """,
                    (project_id,)
                )
                cleaned_count += cursor.rowcount
                
                self.logger.info(f"Cleaned up {cleaned_count} orphaned records")
                return cleaned_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup orphaned records: {e}")
            return 0
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.
        
        Returns:
            Dictionary containing database information
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                info = {
                    "database_type": self.db_type,
                    "connection_string": self.connection_string if self.db_type == 'sqlite' else "***",
                    "schema_version": None,
                    "table_counts": {}
                }
                
                # Get schema version
                try:
                    cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
                    result = cursor.fetchone()
                    if result:
                        info["schema_version"] = result[0]
                except Exception:
                    pass
                
                # Get table counts
                for table_name in self.SCHEMA_SQL.keys():
                    if table_name != "schema_version":
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            result = cursor.fetchone()
                            info["table_counts"][table_name] = result[0] if result else 0
                        except Exception:
                            info["table_counts"][table_name] = 0
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
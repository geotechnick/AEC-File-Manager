"""
AEC File Manager - Streamlit UI Application
"""

import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from agentic_ai import AgenticAI, AECDirectoryStructure, FileIntelligence, RevisionsTracker, QCLogger


def main():
    st.set_page_config(
        page_title="AEC File Manager",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏗️ AEC Project Directory Manager")
    st.markdown("---")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select Page",
            ["Home", "Create Project", "File Explorer", "AI Assistant", "Revisions", "QC Dashboard", "Settings"]
        )
        
        st.markdown("---")
        st.header("Current Project")
        
        # Project selector
        if "current_project" not in st.session_state:
            st.session_state.current_project = None
            
        project_dirs = [d for d in os.listdir(".") if os.path.isdir(d) and "_" in d and d.count("_") >= 1]
        
        if project_dirs:
            selected_project = st.selectbox("Select Project", ["None"] + project_dirs)
            if selected_project != "None" and selected_project != st.session_state.current_project:
                st.session_state.current_project = selected_project
                st.session_state.ai = AgenticAI(selected_project)
                st.rerun()
        else:
            st.info("No projects found. Create a new project first.")
    
    # Main content based on selected page
    if page == "Home":
        show_home_page()
    elif page == "Create Project":
        show_create_project_page()
    elif page == "File Explorer":
        show_file_explorer_page()
    elif page == "AI Assistant":
        show_ai_assistant_page()
    elif page == "Revisions":
        show_revisions_page()
    elif page == "QC Dashboard":
        show_qc_dashboard_page()
    elif page == "Settings":
        show_settings_page()


def show_home_page():
    """Home page with project overview"""
    st.header("Welcome to AEC File Manager")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Projects", len([d for d in os.listdir(".") if os.path.isdir(d) and "_" in d]))
    
    with col2:
        if st.session_state.current_project:
            file_count = sum([len(files) for r, d, files in os.walk(st.session_state.current_project)])
            st.metric("Files in Current Project", file_count)
        else:
            st.metric("Files in Current Project", "No project selected")
    
    with col3:
        if st.session_state.current_project and hasattr(st.session_state, 'ai'):
            try:
                qc_summary = st.session_state.ai.qc_logger.get_qc_summary()
                pending_qc = qc_summary.get('Pending', 0)
                st.metric("Pending QC Items", pending_qc)
            except:
                st.metric("Pending QC Items", "N/A")
        else:
            st.metric("Pending QC Items", "No project selected")
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("Recent Activity")
    if st.session_state.current_project:
        show_recent_activity()
    else:
        st.info("Select a project to view recent activity")
    
    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🆕 Create New Project", use_container_width=True):
            st.switch_page("Create Project")
    
    with col2:
        if st.button("📁 Browse Files", use_container_width=True):
            st.switch_page("File Explorer")
    
    with col3:
        if st.button("🤖 AI Assistant", use_container_width=True):
            st.switch_page("AI Assistant")
    
    with col4:
        if st.button("✅ QC Dashboard", use_container_width=True):
            st.switch_page("QC Dashboard")


def show_create_project_page():
    """Project creation page"""
    st.header("Create New AEC Project")
    
    with st.form("create_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input(
                "Project Name",
                placeholder="Enter project name (e.g., OFFICE_BUILDING)",
                help="Use uppercase and underscores for consistency"
            )
        
        with col2:
            current_year = datetime.now().year
            project_year = st.selectbox(
                "Project Year",
                options=list(range(current_year - 2, current_year + 5)),
                index=2
            )
        
        st.markdown("### Directory Structure Preview")
        with st.expander("View Standard AEC Directory Structure", expanded=False):
            structure = AECDirectoryStructure.DEFAULT_STRUCTURE
            for main_folder, subfolders in structure.items():
                st.markdown(f"**{main_folder}**")
                if isinstance(subfolders, dict):
                    for subfolder, sub_sub in subfolders.items():
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;📁 {subfolder}")
                        for ssf in sub_sub:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📁 {ssf}")
                elif isinstance(subfolders, list):
                    for subfolder in subfolders:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;📁 {subfolder}")
        
        custom_folders = st.text_area(
            "Additional Custom Folders (optional)",
            placeholder="Enter custom folder names, one per line",
            help="These will be added to the 00_PROJECT_MANAGEMENT folder"
        )
        
        submitted = st.form_submit_button("Create Project", type="primary")
        
        if submitted:
            if not project_name:
                st.error("Please enter a project name")
                return
                
            try:
                ai = AgenticAI()
                project_path = ai.initialize_project(project_name, project_year, ".")
                
                # Add custom folders if specified
                if custom_folders:
                    custom_list = [f.strip() for f in custom_folders.split('\n') if f.strip()]
                    pm_path = os.path.join(project_path, "00_PROJECT_MANAGEMENT")
                    for folder in custom_list:
                        os.makedirs(os.path.join(pm_path, folder), exist_ok=True)
                
                st.success(f"✅ Project created successfully at: {project_path}")
                st.session_state.current_project = f"{project_name}_{project_year}"
                st.session_state.ai = ai
                
                # Auto-refresh to show new project
                st.rerun()
                
            except Exception as e:
                st.error(f"Error creating project: {str(e)}")


def show_file_explorer_page():
    """File explorer with AI-enhanced features"""
    st.header("📁 File Explorer")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not hasattr(st.session_state, 'ai'):
        st.session_state.ai = AgenticAI(st.session_state.current_project)
    
    # File upload section
    st.subheader("Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        help="Files will be automatically classified and placed in appropriate folders"
    )
    
    if uploaded_files:
        with st.spinner("Processing uploaded files..."):
            for uploaded_file in uploaded_files:
                # Save uploaded file temporarily
                temp_path = os.path.join(st.session_state.current_project, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Classify and move to appropriate folder
                classification = st.session_state.ai.file_intelligence.classify_file(temp_path)
                suggested_folder = classification['suggested_folder']
                target_path = os.path.join(st.session_state.current_project, suggested_folder)
                
                if os.path.exists(target_path):
                    final_path = os.path.join(target_path, uploaded_file.name)
                    os.rename(temp_path, final_path)
                    
                    # Track revision
                    st.session_state.ai.revisions_tracker.track_file(
                        final_path, 
                        "user", 
                        "File uploaded via UI"
                    )
                    
                    st.success(f"✅ {uploaded_file.name} → {suggested_folder}")
                else:
                    st.warning(f"⚠️ Target folder {suggested_folder} not found. File saved to root.")
    
    # File browser
    st.markdown("---")
    st.subheader("Project Files")
    
    # Scan and display files
    classified_files = st.session_state.ai.scan_and_classify_files()
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        folder_filter = st.selectbox(
            "Filter by Folder",
            ["All"] + list(classified_files.keys())
        )
    
    with col2:
        file_type_filter = st.selectbox(
            "Filter by File Type",
            ["All", "PDF Document", "Word Document", "Excel Spreadsheet", "AutoCAD Drawing", "BIM Model"]
        )
    
    with col3:
        show_details = st.checkbox("Show Details", value=False)
    
    # Display files
    for folder, files in classified_files.items():
        if folder_filter != "All" and folder != folder_filter:
            continue
            
        if not files:
            continue
            
        st.markdown(f"### 📁 {folder}")
        
        for file_info in files:
            if file_type_filter != "All" and file_info['file_type'] != file_type_filter:
                continue
                
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{file_info['filename']}**")
                if show_details:
                    st.caption(f"Type: {file_info['file_type']} | Size: {file_info['size']:,} bytes")
                    if file_info['last_modified']:
                        st.caption(f"Modified: {file_info['last_modified'][:19]}")
            
            with col2:
                if st.button("📋", key=f"details_{file_info['filename']}", help="File Details"):
                    show_file_details_modal(file_info)
            
            with col3:
                if st.button("📝", key=f"qc_{file_info['filename']}", help="QC Review"):
                    show_qc_modal(file_info['full_path'])
            
            with col4:
                if st.button("🔄", key=f"history_{file_info['filename']}", help="Revision History"):
                    show_revision_history_modal(file_info['full_path'])


def show_ai_assistant_page():
    """AI assistant for natural language queries"""
    st.header("🤖 AI Assistant")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not hasattr(st.session_state, 'ai'):
        st.session_state.ai = AgenticAI(st.session_state.current_project)
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hello! I'm your AEC project assistant for {st.session_state.current_project}. I can help you find files, track revisions, and manage QC. What would you like to know?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.ai.process_query(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quick query buttons
    st.markdown("---")
    st.subheader("Quick Queries")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Latest Change Orders", use_container_width=True):
            response = st.session_state.ai.process_query("show me the latest change orders")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("📐 Structural Calculations", use_container_width=True):
            response = st.session_state.ai.process_query("find structural calculations")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("❓ Latest RFIs", use_container_width=True):
            response = st.session_state.ai.process_query("when was the last RFI received")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col4:
        if st.button("⚠️ Overdue QC", use_container_width=True):
            response = st.session_state.ai.process_query("show overdue QC items")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


def show_revisions_page():
    """Revisions tracking and history"""
    st.header("🔄 Revisions Tracking")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not hasattr(st.session_state, 'ai'):
        st.session_state.ai = AgenticAI(st.session_state.current_project)
    
    # Recent revisions
    st.subheader("Recent File Changes")
    
    try:
        # Get recent revisions from database
        import sqlite3
        db_path = os.path.join(st.session_state.current_project, "revisions.db")
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query('''
                SELECT filename, version, timestamp, user, change_summary, file_size
                FROM revisions 
                WHERE is_current = 1
                ORDER BY timestamp DESC
                LIMIT 20
            ''', conn)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['file_size'] = df['file_size'].apply(lambda x: f"{x:,} bytes" if pd.notna(x) else "")
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Last Modified"),
                        "file_size": "Size"
                    }
                )
            else:
                st.info("No revision history found")
        else:
            st.info("No revision tracking database found")
            
    except Exception as e:
        st.error(f"Error loading revision data: {str(e)}")


def show_qc_dashboard_page():
    """QC tracking dashboard"""
    st.header("✅ Quality Control Dashboard")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not hasattr(st.session_state, 'ai'):
        st.session_state.ai = AgenticAI(st.session_state.current_project)
    
    try:
        # QC Summary metrics
        qc_summary = st.session_state.ai.qc_logger.get_qc_summary()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Pending", qc_summary.get('Pending', 0))
        with col2:
            st.metric("In Review", qc_summary.get('In Review', 0))
        with col3:
            st.metric("Approved", qc_summary.get('Approved', 0))
        with col4:
            st.metric("Rejected", qc_summary.get('Rejected', 0))
        with col5:
            st.metric("Revision Required", qc_summary.get('Revision Required', 0))
        
        # QC Status Chart
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("QC Status Distribution")
            if any(qc_summary.values()):
                fig = px.pie(
                    values=list(qc_summary.values()),
                    names=list(qc_summary.keys()),
                    title="QC Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No QC data available")
        
        with col2:
            st.subheader("Overdue Items")
            overdue_items = st.session_state.ai.qc_logger.get_overdue_qc()
            
            if overdue_items:
                overdue_df = pd.DataFrame(overdue_items)
                overdue_df['due_date'] = pd.to_datetime(overdue_df['due_date'])
                overdue_df['days_overdue'] = (datetime.now() - overdue_df['due_date']).dt.days
                
                st.dataframe(
                    overdue_df[['filename', 'discipline', 'days_overdue']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No overdue QC items!")
        
        # Create new QC entry
        st.markdown("---")
        st.subheader("Create QC Entry")
        
        with st.form("create_qc_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                qc_file = st.text_input("File Path", placeholder="Path to file for QC review")
            
            with col2:
                qc_discipline = st.selectbox("Discipline", QCLogger.DISCIPLINES)
            
            with col3:
                qc_reviewer = st.text_input("Reviewer", placeholder="Reviewer name")
            
            due_days = st.slider("Due in Days", min_value=1, max_value=30, value=7)
            
            if st.form_submit_button("Create QC Entry"):
                if qc_file and qc_discipline:
                    try:
                        qc_id = st.session_state.ai.qc_logger.create_qc_entry(
                            qc_file, qc_discipline, qc_reviewer, due_days
                        )
                        st.success(f"QC entry created with ID: {qc_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating QC entry: {str(e)}")
                else:
                    st.error("Please fill in required fields")
                    
    except Exception as e:
        st.error(f"Error loading QC data: {str(e)}")


def show_settings_page():
    """Application settings and configuration"""
    st.header("⚙️ Settings")
    
    st.subheader("Directory Structure Templates")
    
    with st.expander("Edit Default Directory Structure", expanded=False):
        current_structure = AECDirectoryStructure.DEFAULT_STRUCTURE
        
        st.json(current_structure)
        st.info("Directory structure customization will be available in a future update")
    
    st.markdown("---")
    st.subheader("File Classification Rules")
    
    classification_rules = {
        "Drawings": ["drawing", "plan", "elevation", "dwg", "dxf"],
        "Specifications": ["spec", "specification", "division"],
        "Calculations": ["calc", "calculation", "analysis"],
        "Correspondence": ["rfi", "submittal", "email", "letter"]
    }
    
    for category, keywords in classification_rules.items():
        st.text_input(f"{category} Keywords", value=", ".join(keywords), disabled=True)
    
    st.info("Classification rule editing will be available in a future update")
    
    st.markdown("---")
    st.subheader("Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Revision History", type="secondary"):
            if st.session_state.current_project:
                db_path = os.path.join(st.session_state.current_project, "revisions.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                    st.success("Revision history cleared")
                    st.rerun()
    
    with col2:
        if st.button("🗑️ Clear QC Database", type="secondary"):
            if st.session_state.current_project:
                db_path = os.path.join(st.session_state.current_project, "qc_log.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                    st.success("QC database cleared")
                    st.rerun()


def show_recent_activity():
    """Show recent project activity"""
    if not hasattr(st.session_state, 'ai'):
        return
        
    try:
        # Get recent files (last 7 days)
        recent_files = []
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for root, dirs, files in os.walk(st.session_state.current_project):
            for file in files:
                if file.startswith('.') or file.endswith('.db'):
                    continue
                    
                filepath = os.path.join(root, file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if mod_time > cutoff_date:
                    recent_files.append({
                        "filename": file,
                        "modified": mod_time,
                        "folder": os.path.relpath(root, st.session_state.current_project)
                    })
        
        recent_files.sort(key=lambda x: x['modified'], reverse=True)
        
        if recent_files:
            st.write("Recent file activity (last 7 days):")
            for file_info in recent_files[:5]:
                st.markdown(f"• **{file_info['filename']}** in {file_info['folder']} - {file_info['modified'].strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("No recent file activity")
            
    except Exception as e:
        st.error(f"Error loading recent activity: {str(e)}")


def show_file_details_modal(file_info):
    """Show file details in a modal"""
    st.modal(f"File Details: {file_info['filename']}")
    st.json(file_info)


def show_qc_modal(filepath):
    """Show QC creation modal"""
    st.modal("Create QC Entry")
    # QC modal implementation would go here


def show_revision_history_modal(filepath):
    """Show revision history modal"""
    st.modal("Revision History")
    # Revision history modal implementation would go here


if __name__ == "__main__":
    main()
"""
Document Requests Database Functions
Handles all database operations for document request/sharing functionality
"""
from datetime import datetime
from pathlib import Path
import streamlit as st
from core.cache import get_database

def create_request_table():
    """Create document_requests table if it doesn't exist
    
    This function creates the table at runtime if needed.
    For proper setup, add this table definition to your setup_db.py file.
    """
    db = get_database()
    query = """
    CREATE TABLE IF NOT EXISTS document_requests (
        request_id INT AUTO_INCREMENT PRIMARY KEY,
        from_company_id INT NOT NULL,
        to_company_id INT NOT NULL,
        document_type VARCHAR(50) NOT NULL,
        request_note TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        pdf_filename VARCHAR(255),
        rejection_reason TEXT,
        request_date DATETIME NOT NULL,
        completed_date DATETIME,
        FOREIGN KEY (from_company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (to_company_id) REFERENCES companies(id) ON DELETE CASCADE,
        INDEX idx_from_company (from_company_id),
        INDEX idx_to_company (to_company_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    db.execute_query(query)

def create_document_request(from_company_id, to_company_id, document_type, request_note):
    """Create a new document request
    
    Args:
        from_company_id: Requesting company ID
        to_company_id: Target company ID
        document_type: Type of document (SEDG Report or i-ESG Questionnaire)
        request_note: Optional note explaining the request
    
    Returns:
        bool: True if successful, False otherwise
    """
    db = get_database()
    query = """
    INSERT INTO document_requests 
    (from_company_id, to_company_id, document_type, request_note, request_date, status)
    VALUES (%s, %s, %s, %s, %s, 'pending')
    """
    params = (
        from_company_id, 
        to_company_id, 
        document_type, 
        request_note, 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    result = db.execute_query(query, params)
    
    if result:
        # Clear caches
        get_incoming_requests.clear()
        get_outgoing_requests.clear()
    
    return result

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_incoming_requests(company_id):
    """Get requests TO this company (pending only)
    
    Args:
        company_id: Company ID
    
    Returns:
        list: List of pending request tuples
    """
    db = get_database()
    query = """
    SELECT request_id, from_company_id, document_type, request_note, 
           request_date, status, rejection_reason
    FROM document_requests
    WHERE to_company_id = %s AND status = 'pending'
    ORDER BY request_date DESC
    """
    
    return db.fetch_query(query, (company_id,))

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_outgoing_requests(company_id):
    """Get requests FROM this company (all statuses)
    
    Args:
        company_id: Company ID
    
    Returns:
        list: List of request tuples with all details
    """
    db = get_database()
    query = """
    SELECT request_id, to_company_id, document_type, request_note, 
           request_date, status, pdf_filename, rejection_reason, completed_date
    FROM document_requests
    WHERE from_company_id = %s
    ORDER BY request_date DESC
    """
    
    return db.fetch_query(query, (company_id,))

def approve_and_upload_document(request_id, pdf_file, upload_folder):
    """Approve request and upload document
    
    Args:
        request_id: Request ID
        pdf_file: Uploaded file object from Streamlit
        upload_folder: Path object for upload directory
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Save file
        filename = f"request_{request_id}_{pdf_file.name}"
        filepath = upload_folder / filename
        with open(filepath, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        # Update database
        db = get_database()
        query = """
        UPDATE document_requests
        SET status = 'completed', pdf_filename = %s, completed_date = %s
        WHERE request_id = %s
        """
        params = (filename, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request_id)
        
        result = db.execute_query(query, params)
        
        if result:
            # Clear caches
            get_incoming_requests.clear()
            get_outgoing_requests.clear()
        
        return result
    except Exception as e:
        print(f"Error uploading document: {e}")
        return False

def reject_request(request_id, rejection_reason):
    """Reject a document request
    
    Args:
        request_id: Request ID
        rejection_reason: Reason for rejection
    
    Returns:
        bool: True if successful, False otherwise
    """
    db = get_database()
    query = """
    UPDATE document_requests
    SET status = 'rejected', rejection_reason = %s, completed_date = %s
    WHERE request_id = %s
    """
    params = (rejection_reason, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request_id)
    
    result = db.execute_query(query, params)
    
    if result:
        # Clear caches
        get_incoming_requests.clear()
        get_outgoing_requests.clear()
    
    return result

def cancel_request(request_id):
    """Cancel a pending request
    
    Args:
        request_id: Request ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    db = get_database()
    query = """
    UPDATE document_requests
    SET status = 'cancelled', completed_date = %s
    WHERE request_id = %s
    """
    params = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request_id)
    
    result = db.execute_query(query, params)
    
    if result:
        # Clear caches
        get_incoming_requests.clear()
        get_outgoing_requests.clear()
    
    return result

def get_request_statistics(company_id):
    """Get statistics for a company's document requests
    
    Args:
        company_id: Company ID
    
    Returns:
        dict: Statistics including counts by status
    """
    db = get_database()
    query = """
    SELECT 
        COUNT(CASE WHEN status = 'pending' AND from_company_id = %s THEN 1 END) as outgoing_pending,
        COUNT(CASE WHEN status = 'pending' AND to_company_id = %s THEN 1 END) as incoming_pending,
        COUNT(CASE WHEN status = 'completed' AND from_company_id = %s THEN 1 END) as outgoing_completed,
        COUNT(CASE WHEN status = 'completed' AND to_company_id = %s THEN 1 END) as incoming_completed
    FROM document_requests
    WHERE from_company_id = %s OR to_company_id = %s
    """
    params = (company_id, company_id, company_id, company_id, company_id, company_id)
    
    row = db.fetch_one(query, params)
    
    if row:
        return {
            'outgoing_pending': row[0],
            'incoming_pending': row[1],
            'outgoing_completed': row[2],
            'incoming_completed': row[3]
        }
    return {
        'outgoing_pending': 0,
        'incoming_pending': 0,
        'outgoing_completed': 0,
        'incoming_completed': 0
    }
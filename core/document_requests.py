"""
Document Requests Database Functions
Handles all database operations for document request/sharing functionality
Now using BLOB storage for PDFs instead of filesystem
WITH OPTIMIZED CACHING
"""
from datetime import datetime
import streamlit as st
from core.cache import get_database

def create_request_table():
    """Create document_requests table if it doesn't exist"""
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
        pdf_data MEDIUMBLOB,
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
    """Create a new document request"""
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
        # Clear caches for both companies
        get_incoming_requests.clear()
        get_outgoing_requests.clear()
        get_all_requests_for_company.clear()
    
    return result

@st.cache_data(ttl=300)  # Cache for 5 minutes (increased from 1 min)
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

@st.cache_data(ttl=300)  # Cache for 5 minutes (increased from 1 min)
def get_outgoing_requests(company_id):
    """Get requests FROM this company (all statuses)
    
    Args:
        company_id: Company ID
    
    Returns:
        list: List of request tuples with all details (excluding BLOB data)
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

@st.cache_data(ttl=300)  # NEW: Cache combined requests
def get_all_requests_for_company(company_id):
    """Get ALL requests (incoming and outgoing) for a company
    
    This is more efficient than calling get_incoming_requests and 
    get_outgoing_requests separately
    
    Returns:
        dict: {
            'incoming': [...],
            'outgoing': [...]
        }
    """
    db = get_database()
    
    # Get incoming
    incoming_query = """
    SELECT request_id, from_company_id, document_type, request_note, 
           request_date, status, rejection_reason
    FROM document_requests
    WHERE to_company_id = %s AND status = 'pending'
    ORDER BY request_date DESC
    """
    
    # Get outgoing
    outgoing_query = """
    SELECT request_id, to_company_id, document_type, request_note, 
           request_date, status, pdf_filename, rejection_reason, completed_date
    FROM document_requests
    WHERE from_company_id = %s
    ORDER BY request_date DESC
    """
    
    incoming = db.fetch_query(incoming_query, (company_id,))
    outgoing = db.fetch_query(outgoing_query, (company_id,))
    
    return {
        'incoming': incoming or [],
        'outgoing': outgoing or []
    }

def approve_and_upload_document(request_id, pdf_file):
    """Approve request and upload document to BLOB storage"""
    try:
        # Read file data as bytes
        pdf_bytes = pdf_file.getvalue()
        filename = pdf_file.name
        
        # Update database with BLOB data
        db = get_database()
        query = """
        UPDATE document_requests
        SET status = 'completed', 
            pdf_filename = %s, 
            pdf_data = %s,
            completed_date = %s
        WHERE request_id = %s
        """
        params = (
            filename, 
            pdf_bytes, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            request_id
        )
        
        result = db.execute_query(query, params)
        
        if result:
            # Clear ALL caches
            get_incoming_requests.clear()
            get_outgoing_requests.clear()
            get_all_requests_for_company.clear()
            get_document_file.clear()
        
        return result
    except Exception as e:
        print(f"Error uploading document: {e}")
        return False

@st.cache_data(ttl=3600)  # NEW: Cache for 1 hour - documents rarely change once uploaded
def get_document_file(request_id):
    """Retrieve document file data from BLOB storage
    
    Args:
        request_id: Request ID
    
    Returns:
        tuple: (pdf_bytes, filename) or (None, None) if not found
    """
    db = get_database()
    query = """
    SELECT pdf_data, pdf_filename
    FROM document_requests
    WHERE request_id = %s AND status = 'completed' AND pdf_data IS NOT NULL
    """
    
    result = db.fetch_one(query, (request_id,))
    
    if result and result[0]:
        return result[0], result[1]  # pdf_data, pdf_filename
    return None, None

def reject_request(request_id, rejection_reason):
    """Reject a document request"""
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
        get_all_requests_for_company.clear()
    
    return result

def cancel_request(request_id):
    """Cancel a pending request"""
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
        get_all_requests_for_company.clear()
    
    return result

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_request_statistics(company_id):
    """Get statistics for a company's document requests"""
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
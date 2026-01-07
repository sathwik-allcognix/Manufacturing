"""
Sales Data Import Endpoints
Add these to your FastAPI router
"""

from typing import List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status,Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import pandas as pd
import io
from pydantic import BaseModel

# Assuming these imports from your existing codebase
from ..db import get_db
from .. import models, schemas
from .auth import get_current_org

router = APIRouter(prefix="/api/sales", tags=["importData"])


# Pydantic models for request/response
class SalesforceImportRequest(BaseModel):
    product_id: int
    username: str
    password: str
    security_token: str
    domain: str = "login"  # or "test" for sandbox
    product_name_field: str = ""  # Filter by product name in Salesforce
    start_date: str = ""  # YYYY-MM-DD format
    end_date: str = ""  # YYYY-MM-DD format


class ImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    message: str


@router.post("/import/excel", response_model=ImportResponse)
async def import_sales_from_excel(
    file: UploadFile = File(...),
    product_id: int = Form(...),   # <-- REQUIRED FIX
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):

    """
    Import sales data from Excel/CSV file
    Expected columns: sales_date, sales_quantity
    """
    if not product_id:
        raise HTTPException(
            status_code=400,
            detail="product_id is required"
        )
    
    # Verify product belongs to organization
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.org_id == current_org.org_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found or does not belong to your organization"
        )
    
    # Read file
    try:
        contents = await file.read()
        
        # Determine file type and read accordingly
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV or Excel file"
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )
    
    # Validate required columns
    required_columns = ['sales_date', 'sales_quantity']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}"
        )
    
    # Process and import data
    imported_count = 0
    skipped_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            if pd.isna(row['sales_date']) or pd.isna(row['sales_quantity']):
                skipped_count += 1
                continue
                
            sales_date = pd.to_datetime(row['sales_date']).date()
            sales_quantity = float(row['sales_quantity'])
            
            if sales_quantity < 0:
                errors.append(f"Row {idx + 2}: Negative quantity")
                skipped_count += 1
                continue
            
            # Check for existing record
            existing = db.query(models.SalesData).filter(
                models.SalesData.product_id == product_id,
                models.SalesData.sales_date == sales_date
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create new sales record
            sales_record = models.SalesData(
                product_id=product_id,
                sales_date=sales_date,
                sales_quantity=sales_quantity,
                created_at=datetime.utcnow()
            )
            db.add(sales_record)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
            skipped_count += 1
            continue
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
    message = f"Successfully imported {imported_count} records"
    if skipped_count > 0:
        message += f", skipped {skipped_count} records"
    if errors:
        message += f". Errors: {'; '.join(errors[:5])}"  # Show first 5 errors
    
    return ImportResponse(
        imported_count=imported_count,
        skipped_count=skipped_count,
        message=message
    )


@router.post("/import/salesforce", response_model=ImportResponse)
async def import_sales_from_salesforce(
    request: SalesforceImportRequest,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    """
    Import sales data from Salesforce CRM
    Fetches OpportunityLineItem records
    """
    # Verify product belongs to organization
    product = db.query(models.Product).filter(
        models.Product.product_id == request.product_id,
        models.Product.org_id == current_org.org_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found or does not belong to your organization"
        )
    
    try:
        from simple_salesforce import Salesforce
        
        # Connect to Salesforce
        sf_domain = 'test' if request.domain == 'test' else None
        sf = Salesforce(
            username=request.username,
            password=request.password,
            security_token=request.security_token,
            domain=sf_domain
        )
        
        # Build dynamic SOQL query with filters
        query = """
            SELECT 
                ServiceDate,
                Quantity,
                CloseDate,
                Product2.Name,
                Product2.ProductCode
            FROM OpportunityLineItem 
            WHERE Opportunity.IsClosed = true 
            AND Opportunity.IsWon = true
        """
        
        # Add product name filter if provided
        if request.product_name_field:
            # Escape single quotes in the product name
            escaped_product = request.product_name_field.replace("'", "\\'")
            query += f" AND (Product2.Name LIKE '%{escaped_product}%' OR Product2.ProductCode LIKE '%{escaped_product}%')"
        
        # Add date range filters if provided
        if request.start_date:
            query += f" AND (ServiceDate >= {request.start_date} OR CloseDate >= {request.start_date})"
        
        if request.end_date:
            query += f" AND (ServiceDate <= {request.end_date} OR CloseDate <= {request.end_date})"
        
        query += " ORDER BY ServiceDate DESC"
        
        result = sf.query(query)
        records = result.get('records', [])
        
        if not records:
            return ImportResponse(
                imported_count=0,
                skipped_count=0,
                message="No sales records found in Salesforce matching your criteria"
            )
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Salesforce integration not available. Install simple-salesforce package"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Salesforce connection error: {str(e)}"
        )
    
    # Process and import data
    imported_count = 0
    skipped_count = 0
    
    for record in records:
        try:
            # Use ServiceDate if available, otherwise CloseDate
            date_str = record.get('ServiceDate') or record.get('CloseDate')
            if not date_str:
                skipped_count += 1
                continue
                
            sales_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            sales_quantity = float(record.get('Quantity', 0))
            
            if sales_quantity <= 0:
                skipped_count += 1
                continue
            
            # Check for existing record
            existing = db.query(models.SalesData).filter(
                models.SalesData.product_id == request.product_id,
                models.SalesData.sales_date == sales_date
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create new sales record
            sales_record = models.SalesData(
                product_id=request.product_id,
                sales_date=sales_date,
                sales_quantity=sales_quantity,
                created_at=datetime.utcnow()
            )
            db.add(sales_record)
            imported_count += 1
            
        except Exception as e:
            skipped_count += 1
            continue
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
    return ImportResponse(
        imported_count=imported_count,
        skipped_count=skipped_count,
        message=f"Successfully imported {imported_count} records from Salesforce"
    )


# Optional: Get sales data for a product
@router.get("/product/{product_id}", response_model=List[schemas.SalesDataRead])
def get_product_sales(
    product_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    """Get all sales data for a specific product"""
    # Verify product belongs to organization
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.org_id == current_org.org_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found or does not belong to your organization"
        )
    
    sales_data = db.query(models.SalesData).filter(
        models.SalesData.product_id == product_id
    ).order_by(models.SalesData.sales_date.desc()).all()
    
    return sales_data
"""
SEDG PDF Generator with color-coded sections
Requires: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from datetime import datetime


# Color schemes for each section
COLORS = {
    'environmental': {
        'basic': colors.HexColor('#1a5f3f'),      # Dark green
        'intermediate': colors.HexColor('#2d8659'),  # Medium green
        'advanced': colors.HexColor('#a8d5ba')     # Light green
    },
    'social': {
        'basic': colors.HexColor('#8b1a1a'),      # Dark red
        'intermediate': colors.HexColor('#c44545'),  # Medium red
        'advanced': colors.HexColor('#f4a5a5')     # Light pink
    },
    'governance': {
        'basic': colors.HexColor('#1a3a5f'),      # Dark blue
        'intermediate': colors.HexColor('#2d5f8b'),  # Medium blue
        'advanced': colors.HexColor('#a5c4e6')     # Light blue
    }
}


def generate_sedg_pdf(company_info, sedg_data, ghg_data, disclosure_date):
    """Generate SEDG report PDF with color coding.
    
    Args:
        company_info: Company information dict
        sedg_data: SEDG form data from session state
        ghg_data: GHG emissions data
        disclosure_date: Date of disclosure
    
    Returns:
        BytesIO: PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        spaceAfter=6
    )
    
    # Title
    title = Paragraph("SIMPLIFIED ESG DISCLOSURE GUIDE (SEDG)", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # General Information Section
    elements.append(Paragraph("GENERAL INFORMATION", heading_style))
    
    general_info_data = [
        ['Name of Organisation', company_info['company_name']],
        ['Date of Disclosure', disclosure_date.strftime('%Y-%m-%d')],
        ['Disclosure Period', sedg_data['reporting_period']],
        ['Location of Headquarters', company_info.get('address', 'Not specified')],
        ['Industry Sector', company_info['industry_sector']],
        ['Entities Included', company_info['company_name']],
        ['Locations Included', company_info.get('address', 'Not specified')]
    ]
    
    general_table = Table(general_info_data, colWidths=[2.5*inch, 4*inch])
    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e0e0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elements.append(general_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Environmental Disclosures
    env_heading = Paragraph("ENVIRONMENTAL DISCLOSURES", heading_style)
    elements.append(env_heading)
    
    env_data = [
        ['Indicator', 'Description', 'Value', 'Unit', 'Level'],
        # GHG Emissions (Basic - Dark Green)
        ['SEDG-E1.1', 'Total Scope 1 GHG emissions', f"{ghg_data['scope_1']:.2f}", 'metric tonnes', 'Basic'],
        ['SEDG-E1.1', 'Total Scope 2 GHG emissions', f"{ghg_data['scope_2']:.2f}", 'metric tonnes', 'Basic'],
        ['SEDG-E1.1', 'Total Scope 3 GHG emissions', f"{ghg_data['scope_3']:.2f}", 'metric tonnes', 'Basic'],
        # Energy (Intermediate - Medium Green)
        ['SEDG-E1.2', 'Renewable fuel sources', f"{sedg_data['environmental'].get('renewable_fuel', 0):.2f}", 'joules/Wh', 'Intermediate'],
        ['SEDG-E1.2', 'Non-renewable fuel sources', f"{sedg_data['environmental'].get('non_renewable_fuel', 0):.2f}", 'joules/Wh', 'Intermediate'],
        ['SEDG-E1.2', 'Electricity', f"{sedg_data['environmental'].get('electricity', 0):.2f}", 'joules/Wh', 'Intermediate'],
        ['SEDG-E1.2', 'Heating', f"{sedg_data['environmental'].get('heating', 0):.2f}", 'joules/Wh', 'Intermediate'],
        ['SEDG-E1.2', 'Cooling', f"{sedg_data['environmental'].get('cooling', 0):.2f}", 'joules/Wh', 'Intermediate'],
        ['SEDG-E1.2', 'Steam', f"{sedg_data['environmental'].get('steam', 0):.2f}", 'joules/Wh', 'Intermediate'],
        # Water (Advanced - Light Green)
        ['SEDG-E2.1', 'Purchased water', f"{sedg_data['environmental'].get('purchased_water', 0):.2f}", 'litres', 'Advanced'],
        ['SEDG-E2.1', 'Surface water', f"{sedg_data['environmental'].get('surface_water', 0):.2f}", 'litres', 'Advanced'],
        ['SEDG-E2.1', 'Groundwater', f"{sedg_data['environmental'].get('groundwater', 0):.2f}", 'litres', 'Advanced'],
        # Waste (Basic - Dark Green)
        ['SEDG-E4.1', 'Waste generated', f"{sedg_data['environmental'].get('waste_generated', 0):.2f}", 'metric tonnes', 'Basic'],
        ['SEDG-E4.1', 'Waste diverted from disposal', f"{sedg_data['environmental'].get('waste_diverted', 0):.2f}", 'metric tonnes', 'Basic'],
        ['SEDG-E4.1', 'Waste directed to disposal', f"{sedg_data['environmental'].get('waste_disposed', 0):.2f}", 'metric tonnes', 'Basic'],
    ]
    
    env_table = Table(env_data, colWidths=[0.8*inch, 2.5*inch, 1.2*inch, 1.2*inch, 0.8*inch])
    
    # Apply color coding based on level
    env_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    
    # Color code rows based on level
    for i, row in enumerate(env_data[1:], start=1):
        level = row[4]
        if level == 'Basic':
            color = COLORS['environmental']['basic']
        elif level == 'Intermediate':
            color = COLORS['environmental']['intermediate']
        else:
            color = COLORS['environmental']['advanced']
        
        env_style.append(('BACKGROUND', (4, i), (4, i), color))
        env_style.append(('TEXTCOLOR', (4, i), (4, i), colors.white))
    
    env_table.setStyle(TableStyle(env_style))
    elements.append(env_table)
    elements.append(PageBreak())
    
    # Social Disclosures
    soc_heading = Paragraph("SOCIAL DISCLOSURES", heading_style)
    elements.append(soc_heading)
    
    social_data = [
        ['Indicator', 'Description', 'Value', 'Unit', 'Level'],
        # Labour (Basic - Dark Red)
        ['SEDG-S1.1', 'Child labour incidents', str(sedg_data['social'].get('child_labour_incidents', 0)), 'number', 'Basic'],
        ['SEDG-S1.2', 'Forced labour incidents', str(sedg_data['social'].get('forced_labour_incidents', 0)), 'number', 'Basic'],
        # Employees (Intermediate - Medium Red)
        ['SEDG-S2.1', 'Number of employees', str(sedg_data['social'].get('num_employees', 0)), 'number', 'Intermediate'],
        ['SEDG-S2.2', 'Turnover rate', f"{sedg_data['social'].get('turnover_rate', 0):.1f}", 'percent', 'Intermediate'],
        ['SEDG-S2.3', 'Training hours per employee', f"{sedg_data['social'].get('training_hours', 0):.1f}", 'hours', 'Intermediate'],
        ['SEDG-S2.3', 'Employees - Female', f"{sedg_data['social'].get('employees_female', 0):.1f}", 'percent', 'Intermediate'],
        ['SEDG-S2.3', 'Directors - Female', f"{sedg_data['social'].get('directors_female', 0):.1f}", 'percent', 'Intermediate'],
        # Health & Safety (Advanced - Light Red)
        ['SEDG-S3.1', 'Fatalities', str(sedg_data['social'].get('fatalities', 0)), 'number', 'Advanced'],
        ['SEDG-S3.1', 'Injuries', str(sedg_data['social'].get('injuries', 0)), 'number', 'Advanced'],
        ['SEDG-S3.2', 'H&S trained employees', f"{sedg_data['social'].get('hs_trained_pct', 0):.1f}", 'percent', 'Advanced'],
        # Community (Basic - Dark Red)
        ['SEDG-S5.1', 'Community investment', f"{sedg_data['social'].get('community_investment', 0):.2f}", 'MYR', 'Basic'],
    ]
    
    soc_table = Table(social_data, colWidths=[0.8*inch, 2.5*inch, 1.2*inch, 1.2*inch, 0.8*inch])
    
    soc_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    
    for i, row in enumerate(social_data[1:], start=1):
        level = row[4]
        if level == 'Basic':
            color = COLORS['social']['basic']
        elif level == 'Intermediate':
            color = COLORS['social']['intermediate']
        else:
            color = COLORS['social']['advanced']
        
        soc_style.append(('BACKGROUND', (4, i), (4, i), color))
        soc_style.append(('TEXTCOLOR', (4, i), (4, i), colors.white))
    
    soc_table.setStyle(TableStyle(soc_style))
    elements.append(soc_table)
    elements.append(PageBreak())
    
    # Governance Disclosures
    gov_heading = Paragraph("GOVERNANCE DISCLOSURES", heading_style)
    elements.append(gov_heading)
    
    governance_data = [
        ['Indicator', 'Description', 'Value', 'Level'],
        # Board (Basic - Dark Blue)
        ['SEDG-G1.1', 'Number of directors', str(sedg_data['governance'].get('num_directors', 0)), 'Basic'],
        # Policies (Intermediate - Medium Blue)
        ['SEDG-G2.1', 'Company policies', sedg_data['governance'].get('company_policies', 'Not specified')[:50] + '...', 'Intermediate'],
        # Risk (Advanced - Light Blue)
        ['SEDG-G3.1', 'Last audit year', str(sedg_data['governance'].get('last_audit_year', datetime.now().year)), 'Advanced'],
        # Anti-corruption (Basic - Dark Blue)
        ['SEDG-G4.1', 'Corruption incidents', str(sedg_data['governance'].get('corruption_incidents', 0)), 'Basic'],
        ['SEDG-G4.3', 'Anti-corruption trained', f"{sedg_data['governance'].get('anticorruption_trained_pct', 0):.1f}%", 'Basic'],
        # Privacy (Intermediate - Medium Blue)
        ['SEDG-G5.1', 'Privacy complaints', str(sedg_data['governance'].get('privacy_complaints', 0)), 'Intermediate'],
    ]
    
    gov_table = Table(governance_data, colWidths=[0.8*inch, 2.5*inch, 2.5*inch, 0.8*inch])
    
    gov_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    
    for i, row in enumerate(governance_data[1:], start=1):
        level = row[3]
        if level == 'Basic':
            color = COLORS['governance']['basic']
        elif level == 'Intermediate':
            color = COLORS['governance']['intermediate']
        else:
            color = COLORS['governance']['advanced']
        
        gov_style.append(('BACKGROUND', (3, i), (3, i), color))
        gov_style.append(('TEXTCOLOR', (3, i), (3, i), colors.white))
    
    gov_table.setStyle(TableStyle(gov_style))
    elements.append(gov_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
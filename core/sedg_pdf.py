"""
SEDG PDF Generator with TRULY DYNAMIC tables and automatic row height calculation
Complete implementation with automatic cell sizing to prevent data loss
Requires: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

# Color schemes
COLORS = {
    'environmental': {
        'basic': colors.HexColor('#1a5f3f'),
        'intermediate': colors.HexColor('#2d8659'),
        'advanced': colors.HexColor('#a8d5ba')
    },
    'social': {
        'basic': colors.HexColor('#8b1a1a'),
        'intermediate': colors.HexColor('#c44545'),
        'advanced': colors.HexColor('#f4a5a5')
    },
    'governance': {
        'basic': colors.HexColor('#1a3a5f'),
        'intermediate': colors.HexColor('#2d5f8b'),
        'advanced': colors.HexColor('#a5c4e6')
    }
}

def safe_get(data, key, default=0):
    """Safely get value from dict with default."""
    val = data.get(key, default)
    return val if val is not None and val != '' else default

def safe_str(data, key, default=''):
    """Safely get string value from dict."""
    val = data.get(key, default)
    return str(val) if val is not None and val != '' else default

def wrap_text(text, style):
    """Wrap text in a Paragraph for automatic text wrapping."""
    return Paragraph(str(text), style)

def generate_sedg_pdf(company_info, sedg_data, ghg_data, disclosure_date):
    """Generate complete SEDG v2 report PDF with dynamic sizing and all fields."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles for table cells
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )
    
    cell_style_bold = ParagraphStyle(
        'CellStyleBold',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        wordWrap='CJK'
    )
    
    cell_style_right = ParagraphStyle(
        'CellStyleRight',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9,
        alignment=TA_RIGHT,
        wordWrap='CJK'
    )
    
    cell_style_header = ParagraphStyle(
        'CellStyleHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        textColor=colors.white,
        wordWrap='CJK'
    )
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1a1a1a'), spaceAfter=8, alignment=TA_CENTER)
    
    # Title
    elements.append(Paragraph("SIMPLIFIED ESG DISCLOSURE GUIDE (SEDG) VERSION 2", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # General Information
    elements.append(Paragraph("GENERAL INFORMATION", styles['Heading2']))
    
    gen_data = [
        [wrap_text('Name of Organisation', cell_style_bold), wrap_text(company_info['company_name'], cell_style)],
        [wrap_text('Date of Disclosure', cell_style_bold), wrap_text(disclosure_date.strftime('%Y-%m-%d'), cell_style)],
        [wrap_text('Disclosure Period', cell_style_bold), wrap_text(sedg_data.get('period', str(datetime.now().year)), cell_style)],
        [wrap_text('Location of Headquarters', cell_style_bold), wrap_text(company_info.get('address', 'Not specified'), cell_style)],
        [wrap_text('Entities Included', cell_style_bold), wrap_text(safe_str(sedg_data, 'entities_included', 'N/A'), cell_style)],
        [wrap_text('Locations Included', cell_style_bold), wrap_text(safe_str(sedg_data, 'locations_included', 'N/A'), cell_style)],
        [wrap_text('Industry Sector', cell_style_bold), wrap_text(company_info['industry_sector'], cell_style)],
    ]
    
    # Use None for column widths to allow auto-sizing
    gen_table = Table(gen_data, colWidths=[2.3*inch, None])
    gen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(gen_table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(PageBreak())

    # ENVIRONMENTAL DISCLOSURES
    elements.append(Paragraph("ENVIRONMENTAL DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    env_data = [
        [wrap_text('Code', cell_style_header), wrap_text('Description', cell_style_header), 
         wrap_text('Value', cell_style_header), wrap_text('Unit', cell_style_header), 
         wrap_text('Level', cell_style_header)],
        
        # E1 - EMISSIONS
        [wrap_text('E1.1', cell_style), wrap_text('Total Scope 1 GHG emissions', cell_style), 
         wrap_text(f"{ghg_data['scope_1']:.2f}", cell_style_right), wrap_text('tonnes CO2e', cell_style), 
         wrap_text('Basic', cell_style)],
        [wrap_text('E1.2', cell_style), wrap_text('Total Scope 2 GHG emissions', cell_style), 
         wrap_text(f"{ghg_data['scope_2']:.2f}", cell_style_right), wrap_text('tonnes CO2e', cell_style), 
         wrap_text('Basic', cell_style)],
        [wrap_text('E1.3', cell_style), wrap_text('Scope 1 GHG reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e13_scope1_reduction'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E1.4', cell_style), wrap_text('Scope 2 GHG reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e14_scope2_reduction'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E1.5', cell_style), wrap_text('Total Scope 3 GHG emissions', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e15_scope3_total'):.2f}", cell_style_right), 
         wrap_text('tonnes CO2e', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E1.6', cell_style), wrap_text('Scope 3 GHG reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e16_scope3_reduction'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E1.7', cell_style), wrap_text('Total Scope 1 & 2 intensity', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e17_intensity'):.4f}", cell_style_right), 
         wrap_text('tonnes/unit', cell_style), wrap_text('Advanced', cell_style)],
        
        # E2 - ENERGY CONSUMPTION
        [wrap_text('E2.1', cell_style), wrap_text('Renewable fuel sources', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_renewable'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E2.1', cell_style), wrap_text('Non-renewable fuel sources', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_nonrenewable'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E2.1', cell_style), wrap_text('Electricity', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_electricity'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E2.1', cell_style), wrap_text('Heating (if applicable)', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_heating'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E2.1', cell_style), wrap_text('Cooling (if applicable)', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_cooling'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E2.1', cell_style), wrap_text('Steam (if applicable)', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e21_steam'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Basic', cell_style)],
        
        # E2.2 - ENERGY REDUCTION
        [wrap_text('E2.2', cell_style), wrap_text('Renewable fuel reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_renewable_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E2.2', cell_style), wrap_text('Non-renewable fuel reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_nonrenewable_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E2.2', cell_style), wrap_text('Electricity reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_electricity_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E2.2', cell_style), wrap_text('Heating reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_heating_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E2.2', cell_style), wrap_text('Cooling reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_cooling_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E2.2', cell_style), wrap_text('Steam reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e22_steam_reduction'):.2f}", cell_style_right), 
         wrap_text('J/Wh', cell_style), wrap_text('Intermediate', cell_style)],
        
        # E3 - WATER
        [wrap_text('E3.1', cell_style), wrap_text('Purchased water', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e31_purchased'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E3.1', cell_style), wrap_text('Surface water', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e31_surface'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E3.1', cell_style), wrap_text('Groundwater', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e31_ground'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E3.1', cell_style), wrap_text('Seawater', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e31_sea'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E3.1', cell_style), wrap_text('Produced water', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e31_produced'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E3.2', cell_style), wrap_text('Water reduction', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e32_reduction'):.2f}", cell_style_right), 
         wrap_text('litres', cell_style), wrap_text('Intermediate', cell_style)],
    ]
    
    # Fixed column widths with enough space for wrapping
    env_table = Table(env_data, colWidths=[0.55*inch, 2.8*inch, 0.95*inch, 0.95*inch, 0.95*inch], 
                     repeatRows=1)
    env_table.setStyle(create_table_style(env_data, 'environmental'))
    elements.append(env_table)
    elements.append(PageBreak())
    
    # WASTE SECTION (continuation of Environmental)
    elements.append(Paragraph("ENVIRONMENTAL DISCLOSURES (continued)", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    waste_data = [
        [wrap_text('Code', cell_style_header), wrap_text('Description', cell_style_header), 
         wrap_text('Value', cell_style_header), wrap_text('Unit', cell_style_header), 
         wrap_text('Level', cell_style_header)],
        
        # E4.1 - TOTAL WASTE
        [wrap_text('E4.1', cell_style), wrap_text('Total waste generated', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e41_generated'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E4.1', cell_style), wrap_text('Diverted from disposal', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e41_diverted'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E4.1', cell_style), wrap_text('Directed to disposal', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e41_disposed'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Basic', cell_style)],
        
        # E4.2 - WASTE BREAKDOWN
        [wrap_text('E4.2', cell_style), wrap_text('Hazardous - generated', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_haz_gen'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Hazardous - diverted', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_haz_div'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Hazardous - disposed', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_haz_disp'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Non-hazardous - generated', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_nonhaz_gen'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Non-hazardous - diverted', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_nonhaz_div'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Non-hazardous - disposed', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_nonhaz_disp'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Sector-specific - generated', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_sector_gen'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Sector-specific - diverted', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_sector_div'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Sector-specific - disposed', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_sector_disp'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Material composition - generated', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_material_gen'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Material composition - diverted', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_material_div'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('E4.2', cell_style), wrap_text('Material composition - disposed', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e42_material_disp'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Intermediate', cell_style)],
        
        # E4.3 - DIVERSION METHODS
        [wrap_text('E4.3', cell_style), wrap_text('Haz - prep for reuse', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_haz_reuse'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.3', cell_style), wrap_text('Haz - recycling', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_haz_recycle'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.3', cell_style), wrap_text('Haz - other recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_haz_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.3', cell_style), wrap_text('Non-haz - prep for reuse', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_nonhaz_reuse'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.3', cell_style), wrap_text('Non-haz - recycling', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_nonhaz_recycle'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.3', cell_style), wrap_text('Non-haz - other recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e43_nonhaz_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        
        # E4.4 - DISPOSAL METHODS
        [wrap_text('E4.4', cell_style), wrap_text('Haz - incin w/ recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_haz_incin_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Haz - incin w/o recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_haz_incin_no_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Haz - landfilling', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_haz_landfill'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Haz - other disposal', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_haz_other'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Non-haz - incin w/ recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_nonhaz_incin_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Non-haz - incin w/o recovery', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_nonhaz_incin_no_recovery'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Non-haz - landfilling', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_nonhaz_landfill'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        [wrap_text('E4.4', cell_style), wrap_text('Non-haz - other disposal', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e44_nonhaz_other'):.2f}", cell_style_right), 
         wrap_text('tonnes', cell_style), wrap_text('Advanced', cell_style)],
        
        # E5 - MATERIALS (Note: wider column for long text)
        [wrap_text('E5.1', cell_style), wrap_text('Key materials list', cell_style), 
         wrap_text(safe_str(sedg_data, 'e51_materials', 'N/A'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('E5.2', cell_style), wrap_text('Recycled input materials', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'e52_recycled_pct'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Advanced', cell_style)],
    ]
    
    waste_table = Table(waste_data, colWidths=[0.55*inch, 2.8*inch, 0.95*inch, 0.95*inch, 0.95*inch],
                       repeatRows=1)
    waste_table.setStyle(create_table_style(waste_data, 'environmental'))
    elements.append(waste_table)
    elements.append(PageBreak())
    
    # SOCIAL DISCLOSURES
    elements.append(Paragraph("SOCIAL DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    soc_data = [
        [wrap_text('Code', cell_style_header), wrap_text('Description', cell_style_header), 
         wrap_text('Value', cell_style_header), wrap_text('Unit', cell_style_header), 
         wrap_text('Level', cell_style_header)],
        
        # S1 - HUMAN RIGHTS & LABOUR
        [wrap_text('S1.1', cell_style), wrap_text('Child labour incidents', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's11_child_incidents', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S1.1', cell_style), wrap_text('Nature of child labour', cell_style), 
         wrap_text(safe_str(sedg_data, 's11_child_nature', 'None'), cell_style), 
         wrap_text('description', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S1.1', cell_style), wrap_text('Forced labour incidents', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's11_forced_incidents', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S1.1', cell_style), wrap_text('Nature of forced labour', cell_style), 
         wrap_text(safe_str(sedg_data, 's11_forced_nature', 'None'), cell_style), 
         wrap_text('description', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S1.2', cell_style), wrap_text('Child labour risk ops', cell_style), 
         wrap_text(safe_str(sedg_data, 's12_child_risk_ops', 'None'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('S1.2', cell_style), wrap_text('Forced labour risk ops', cell_style), 
         wrap_text(safe_str(sedg_data, 's12_forced_risk_ops', 'None'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Intermediate', cell_style)],
        
        # S2 - EMPLOYEE MANAGEMENT
        [wrap_text('S2.1', cell_style), wrap_text('Training hours/employee', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's21_training_hours'):.1f}", cell_style_right), 
         wrap_text('hours', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S2.2', cell_style), wrap_text('Number of employees', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's22_num_employees', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('S2.2', cell_style), wrap_text('Turnover rate', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's22_turnover'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('S2.3', cell_style), wrap_text('Meeting minimum wage', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's23_min_wage_pct'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Basic', cell_style)],
        
        # S3 - DIVERSITY
        [wrap_text('S3.1', cell_style), wrap_text('Employees - Female', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's31_emp_female'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S3.1', cell_style), wrap_text('Employees by age', cell_style), 
         wrap_text(safe_str(sedg_data, 's31_emp_age', 'N/A'), cell_style), 
         wrap_text('%', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S3.2', cell_style), wrap_text('Directors - Female', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's32_dir_female'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('S3.2', cell_style), wrap_text('Directors by age', cell_style), 
         wrap_text(safe_str(sedg_data, 's32_dir_age', 'N/A'), cell_style), 
         wrap_text('%', cell_style), wrap_text('Intermediate', cell_style)],
        
        # S4 - OCCUPATIONAL HEALTH & SAFETY
        [wrap_text('S4.1', cell_style), wrap_text('Fatalities', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's41_fatalities', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S4.1', cell_style), wrap_text('Injuries', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's41_injuries', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S4.2', cell_style), wrap_text('H&S trained employees (num)', cell_style), 
         wrap_text(str(safe_get(sedg_data, 's42_hs_trained_num', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('S4.2', cell_style), wrap_text('H&S trained employees (%)', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's42_hs_trained_pct'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Intermediate', cell_style)],
        
        # S5 - COMMUNITY ENGAGEMENT
        [wrap_text('S5.1', cell_style), wrap_text('Community investment', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 's51_community_invest'):.2f}", cell_style_right), 
         wrap_text('MYR', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('S5.2', cell_style), wrap_text('Negative community impact', cell_style), 
         wrap_text(safe_str(sedg_data, 's52_negative_impact', 'None'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Advanced', cell_style)],
    ]
    
    soc_table = Table(soc_data, colWidths=[0.55*inch, 2.8*inch, 0.95*inch, 0.95*inch, 0.95*inch],
                     repeatRows=1)
    soc_table.setStyle(create_table_style(soc_data, 'social'))
    elements.append(soc_table)
    elements.append(PageBreak())
    
    # GOVERNANCE DISCLOSURES
    elements.append(Paragraph("GOVERNANCE DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    gov_data = [
        [wrap_text('Code', cell_style_header), wrap_text('Description', cell_style_header), 
         wrap_text('Value', cell_style_header), wrap_text('Unit', cell_style_header), 
         wrap_text('Level', cell_style_header)],
        
        # G1 - GOVERNANCE STRUCTURE
        [wrap_text('G1.1', cell_style), wrap_text('Number of directors', cell_style), 
         wrap_text(str(safe_get(sedg_data, 'g11_num_directors', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('G1.2', cell_style), wrap_text('Governance structure', cell_style), 
         wrap_text(safe_str(sedg_data, 'g12_structure', 'N/A'), cell_style), 
         wrap_text('description', cell_style), wrap_text('Intermediate', cell_style)],
        
        # G2 - POLICY COMMITMENTS
        [wrap_text('G2.1', cell_style), wrap_text('Company policies', cell_style), 
         wrap_text(safe_str(sedg_data, 'g21_policies', 'N/A'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Basic', cell_style)],
        
        # G3 - RISK MANAGEMENT
        [wrap_text('G3.1', cell_style), wrap_text('Last audit year', cell_style), 
         wrap_text(str(safe_get(sedg_data, 'g31_audit_year', datetime.now().year)), cell_style_right), 
         wrap_text('year', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('G3.2', cell_style), wrap_text('Operations risks', cell_style), 
         wrap_text(safe_str(sedg_data, 'g32_ops_risks', 'N/A'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('G3.3', cell_style), wrap_text('Sustainability risks', cell_style), 
         wrap_text(safe_str(sedg_data, 'g33_sustain_risks', 'N/A'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Advanced', cell_style)],
        
        # G4 - ANTI-CORRUPTION
        [wrap_text('G4.1', cell_style), wrap_text('Corruption incidents', cell_style), 
         wrap_text(str(safe_get(sedg_data, 'g41_corrupt_incidents', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('G4.1', cell_style), wrap_text('Nature of corruption', cell_style), 
         wrap_text(safe_str(sedg_data, 'g41_corrupt_nature', 'None'), cell_style), 
         wrap_text('description', cell_style), wrap_text('Basic', cell_style)],
        [wrap_text('G4.2', cell_style), wrap_text('Anti-corruption trained (num)', cell_style), 
         wrap_text(str(safe_get(sedg_data, 'g42_anticorrupt_num', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('G4.2', cell_style), wrap_text('Anti-corruption trained (%)', cell_style), 
         wrap_text(f"{safe_get(sedg_data, 'g42_anticorrupt_pct'):.1f}", cell_style_right), 
         wrap_text('%', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('G4.3', cell_style), wrap_text('Corruption risks', cell_style), 
         wrap_text(safe_str(sedg_data, 'g43_corrupt_risks', 'N/A'), cell_style), 
         wrap_text('list', cell_style), wrap_text('Advanced', cell_style)],
        
        # G5 - CUSTOMER PRIVACY
        [wrap_text('G5.1', cell_style), wrap_text('Privacy complaints', cell_style), 
         wrap_text(str(safe_get(sedg_data, 'g51_privacy_complaints', 0)), cell_style_right), 
         wrap_text('number', cell_style), wrap_text('Intermediate', cell_style)],
        [wrap_text('G5.1', cell_style), wrap_text('Nature of privacy complaints', cell_style), 
         wrap_text(safe_str(sedg_data, 'g51_privacy_nature', 'None'), cell_style), 
         wrap_text('description', cell_style), wrap_text('Intermediate', cell_style)],
    ]
    
    gov_table = Table(gov_data, colWidths=[0.55*inch, 2.8*inch, 0.95*inch, 0.95*inch, 0.95*inch],
                     repeatRows=1)
    gov_table.setStyle(create_table_style(gov_data, 'governance'))
    elements.append(gov_table)
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                 textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_table_style(data, category):
    """Create consistent table style with color coding and dynamic row heights."""
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    
    # Color code by level
    for i, row in enumerate(data[1:], start=1):
        # Extract level from the last cell (index 4)
        level_cell = row[4]
        # Get the text from the Paragraph object
        if hasattr(level_cell, 'text'):
            level = level_cell.text.lower()
        else:
            level = str(level_cell).lower()
        
        if level in COLORS[category]:
            color = COLORS[category][level]
            style.append(('BACKGROUND', (4, i), (4, i), color))
            if level in ['basic', 'intermediate']:
                style.append(('TEXTCOLOR', (4, i), (4, i), colors.white))
    
    return TableStyle(style)
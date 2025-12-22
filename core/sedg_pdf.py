"""
SEDG PDF Generator with color-coded sections
Complete implementation matching SEDG v2 template with ALL fields
Requires: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

def generate_sedg_pdf(company_info, sedg_data, ghg_data, disclosure_date):
    """Generate complete SEDG v2 report PDF with color coding and all fields."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1a1a1a'), spaceAfter=8, alignment=TA_CENTER)
    
    # Title
    elements.append(Paragraph("SIMPLIFIED ESG DISCLOSURE GUIDE (SEDG) VERSION 2", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # General Information
    elements.append(Paragraph("GENERAL INFORMATION", styles['Heading2']))
    
    gen_data = [
        ['Name of Organisation', company_info['company_name']],
        ['Date of Disclosure', disclosure_date.strftime('%Y-%m-%d')],
        ['Disclosure Period', sedg_data.get('period', str(datetime.now().year))],
        ['Location of Headquarters', company_info.get('address', 'Not specified')],
        ['Entities Included', safe_str(sedg_data, 'entities_included', 'N/A')],
        ['Locations Included', safe_str(sedg_data, 'locations_included', 'N/A')],
        ['Industry Sector', company_info['industry_sector']],
    ]
    
    gen_table = Table(gen_data, colWidths=[2.5*inch, 4.5*inch])
    gen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(gen_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ENVIRONMENTAL DISCLOSURES
    elements.append(Paragraph("ENVIRONMENTAL DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    env_data = [
        ['Code', 'Description', 'Value', 'Unit', 'Level'],
        
        # E1 - EMISSIONS
        ['E1.1', 'Total Scope 1 GHG emissions', f"{ghg_data['scope_1']:.2f}", 'tonnes CO2e', 'Basic'],
        ['E1.2', 'Total Scope 2 GHG emissions', f"{ghg_data['scope_2']:.2f}", 'tonnes CO2e', 'Basic'],
        ['E1.3', 'Scope 1 GHG reduction', f"{safe_get(sedg_data, 'e13_scope1_reduction'):.2f}", 'tonnes', 'Intermediate'],
        ['E1.4', 'Scope 2 GHG reduction', f"{safe_get(sedg_data, 'e14_scope2_reduction'):.2f}", 'tonnes', 'Intermediate'],
        ['E1.5', 'Total Scope 3 GHG emissions', f"{safe_get(sedg_data, 'e15_scope3_total'):.2f}", 'tonnes CO2e', 'Advanced'],
        ['E1.6', 'Scope 3 GHG reduction', f"{safe_get(sedg_data, 'e16_scope3_reduction'):.2f}", 'tonnes', 'Advanced'],
        ['E1.7', 'Total Scope 1 & 2 intensity', f"{safe_get(sedg_data, 'e17_intensity'):.4f}", 'tonnes/unit', 'Advanced'],
        
        # E2 - ENERGY CONSUMPTION
        ['E2.1', 'Renewable fuel sources', f"{safe_get(sedg_data, 'e21_renewable'):.2f}", 'J/Wh', 'Basic'],
        ['E2.1', 'Non-renewable fuel sources', f"{safe_get(sedg_data, 'e21_nonrenewable'):.2f}", 'J/Wh', 'Basic'],
        ['E2.1', 'Electricity', f"{safe_get(sedg_data, 'e21_electricity'):.2f}", 'J/Wh', 'Basic'],
        ['E2.1', 'Heating (if applicable)', f"{safe_get(sedg_data, 'e21_heating'):.2f}", 'J/Wh', 'Basic'],
        ['E2.1', 'Cooling (if applicable)', f"{safe_get(sedg_data, 'e21_cooling'):.2f}", 'J/Wh', 'Basic'],
        ['E2.1', 'Steam (if applicable)', f"{safe_get(sedg_data, 'e21_steam'):.2f}", 'J/Wh', 'Basic'],
        
        # E2.2 - ENERGY REDUCTION
        ['E2.2', 'Renewable fuel reduction', f"{safe_get(sedg_data, 'e22_renewable_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        ['E2.2', 'Non-renewable fuel reduction', f"{safe_get(sedg_data, 'e22_nonrenewable_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        ['E2.2', 'Electricity reduction', f"{safe_get(sedg_data, 'e22_electricity_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        ['E2.2', 'Heating reduction', f"{safe_get(sedg_data, 'e22_heating_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        ['E2.2', 'Cooling reduction', f"{safe_get(sedg_data, 'e22_cooling_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        ['E2.2', 'Steam reduction', f"{safe_get(sedg_data, 'e22_steam_reduction'):.2f}", 'J/Wh', 'Intermediate'],
        
        # E3 - WATER
        ['E3.1', 'Purchased water', f"{safe_get(sedg_data, 'e31_purchased'):.2f}", 'litres', 'Basic'],
        ['E3.1', 'Surface water', f"{safe_get(sedg_data, 'e31_surface'):.2f}", 'litres', 'Basic'],
        ['E3.1', 'Groundwater', f"{safe_get(sedg_data, 'e31_ground'):.2f}", 'litres', 'Basic'],
        ['E3.1', 'Seawater', f"{safe_get(sedg_data, 'e31_sea'):.2f}", 'litres', 'Basic'],
        ['E3.1', 'Produced water', f"{safe_get(sedg_data, 'e31_produced'):.2f}", 'litres', 'Basic'],
        ['E3.2', 'Water reduction', f"{safe_get(sedg_data, 'e32_reduction'):.2f}", 'litres', 'Intermediate'],
    ]
    
    # Continue on next page for waste
    env_table = Table(env_data, colWidths=[0.6*inch, 2.6*inch, 1*inch, 0.9*inch, 0.9*inch])
    env_table.setStyle(create_table_style(env_data, 'environmental'))
    elements.append(env_table)
    elements.append(PageBreak())
    
    # WASTE SECTION (continuation of Environmental)
    elements.append(Paragraph("ENVIRONMENTAL DISCLOSURES (continued)", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    waste_data = [
        ['Code', 'Description', 'Value', 'Unit', 'Level'],
        
        # E4.1 - TOTAL WASTE
        ['E4.1', 'Total waste generated', f"{safe_get(sedg_data, 'e41_generated'):.2f}", 'tonnes', 'Basic'],
        ['E4.1', 'Diverted from disposal', f"{safe_get(sedg_data, 'e41_diverted'):.2f}", 'tonnes', 'Basic'],
        ['E4.1', 'Directed to disposal', f"{safe_get(sedg_data, 'e41_disposed'):.2f}", 'tonnes', 'Basic'],
        
        # E4.2 - WASTE BREAKDOWN
        ['E4.2', 'Hazardous - generated', f"{safe_get(sedg_data, 'e42_haz_gen'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Hazardous - diverted', f"{safe_get(sedg_data, 'e42_haz_div'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Hazardous - disposed', f"{safe_get(sedg_data, 'e42_haz_disp'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Non-hazardous - generated', f"{safe_get(sedg_data, 'e42_nonhaz_gen'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Non-hazardous - diverted', f"{safe_get(sedg_data, 'e42_nonhaz_div'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Non-hazardous - disposed', f"{safe_get(sedg_data, 'e42_nonhaz_disp'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Sector-specific - generated', f"{safe_get(sedg_data, 'e42_sector_gen'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Sector-specific - diverted', f"{safe_get(sedg_data, 'e42_sector_div'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Sector-specific - disposed', f"{safe_get(sedg_data, 'e42_sector_disp'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Material composition - generated', f"{safe_get(sedg_data, 'e42_material_gen'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Material composition - diverted', f"{safe_get(sedg_data, 'e42_material_div'):.2f}", 'tonnes', 'Intermediate'],
        ['E4.2', 'Material composition - disposed', f"{safe_get(sedg_data, 'e42_material_disp'):.2f}", 'tonnes', 'Intermediate'],
        
        # E4.3 - DIVERSION METHODS
        ['E4.3', 'Haz - prep for reuse', f"{safe_get(sedg_data, 'e43_haz_reuse'):.2f}", 'tonnes', 'Advanced'],
        ['E4.3', 'Haz - recycling', f"{safe_get(sedg_data, 'e43_haz_recycle'):.2f}", 'tonnes', 'Advanced'],
        ['E4.3', 'Haz - other recovery', f"{safe_get(sedg_data, 'e43_haz_recovery'):.2f}", 'tonnes', 'Advanced'],
        ['E4.3', 'Non-haz - prep for reuse', f"{safe_get(sedg_data, 'e43_nonhaz_reuse'):.2f}", 'tonnes', 'Advanced'],
        ['E4.3', 'Non-haz - recycling', f"{safe_get(sedg_data, 'e43_nonhaz_recycle'):.2f}", 'tonnes', 'Advanced'],
        ['E4.3', 'Non-haz - other recovery', f"{safe_get(sedg_data, 'e43_nonhaz_recovery'):.2f}", 'tonnes', 'Advanced'],
        
        # E4.4 - DISPOSAL METHODS
        ['E4.4', 'Haz - incin w/ recovery', f"{safe_get(sedg_data, 'e44_haz_incin_recovery'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Haz - incin w/o recovery', f"{safe_get(sedg_data, 'e44_haz_incin_no_recovery'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Haz - landfilling', f"{safe_get(sedg_data, 'e44_haz_landfill'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Haz - other disposal', f"{safe_get(sedg_data, 'e44_haz_other'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Non-haz - incin w/ recovery', f"{safe_get(sedg_data, 'e44_nonhaz_incin_recovery'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Non-haz - incin w/o recovery', f"{safe_get(sedg_data, 'e44_nonhaz_incin_no_recovery'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Non-haz - landfilling', f"{safe_get(sedg_data, 'e44_nonhaz_landfill'):.2f}", 'tonnes', 'Advanced'],
        ['E4.4', 'Non-haz - other disposal', f"{safe_get(sedg_data, 'e44_nonhaz_other'):.2f}", 'tonnes', 'Advanced'],
        
        # E5 - MATERIALS
        ['E5.1', 'Key materials list', safe_str(sedg_data, 'e51_materials', 'N/A')[:30], 'list', 'Basic'],
        ['E5.2', 'Recycled input materials', f"{safe_get(sedg_data, 'e52_recycled_pct'):.1f}", '%', 'Advanced'],
    ]
    
    waste_table = Table(waste_data, colWidths=[0.6*inch, 2.6*inch, 1*inch, 0.9*inch, 0.9*inch])
    waste_table.setStyle(create_table_style(waste_data, 'environmental'))
    elements.append(waste_table)
    elements.append(PageBreak())
    
    # SOCIAL DISCLOSURES
    elements.append(Paragraph("SOCIAL DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    soc_data = [
        ['Code', 'Description', 'Value', 'Unit', 'Level'],
        
        # S1 - HUMAN RIGHTS & LABOUR
        ['S1.1', 'Child labour incidents', str(safe_get(sedg_data, 's11_child_incidents', 0)), 'number', 'Basic'],
        ['S1.1', 'Nature of child labour', safe_str(sedg_data, 's11_child_nature', 'None')[:25], 'description', 'Basic'],
        ['S1.1', 'Forced labour incidents', str(safe_get(sedg_data, 's11_forced_incidents', 0)), 'number', 'Basic'],
        ['S1.1', 'Nature of forced labour', safe_str(sedg_data, 's11_forced_nature', 'None')[:25], 'description', 'Basic'],
        ['S1.2', 'Child labour risk ops', safe_str(sedg_data, 's12_child_risk_ops', 'None')[:25], 'list', 'Intermediate'],
        ['S1.2', 'Forced labour risk ops', safe_str(sedg_data, 's12_forced_risk_ops', 'None')[:25], 'list', 'Intermediate'],
        
        # S2 - EMPLOYEE MANAGEMENT
        ['S2.1', 'Training hours/employee', f"{safe_get(sedg_data, 's21_training_hours'):.1f}", 'hours', 'Basic'],
        ['S2.2', 'Number of employees', str(safe_get(sedg_data, 's22_num_employees', 0)), 'number', 'Intermediate'],
        ['S2.2', 'Turnover rate', f"{safe_get(sedg_data, 's22_turnover'):.1f}", '%', 'Intermediate'],
        ['S2.3', 'Meeting minimum wage', f"{safe_get(sedg_data, 's23_min_wage_pct'):.1f}", '%', 'Basic'],
        
        # S3 - DIVERSITY
        ['S3.1', 'Employees - Female', f"{safe_get(sedg_data, 's31_emp_female'):.1f}", '%', 'Basic'],
        ['S3.1', 'Employees by age', safe_str(sedg_data, 's31_emp_age', 'N/A')[:25], '%', 'Basic'],
        ['S3.2', 'Directors - Female', f"{safe_get(sedg_data, 's32_dir_female'):.1f}", '%', 'Intermediate'],
        ['S3.2', 'Directors by age', safe_str(sedg_data, 's32_dir_age', 'N/A')[:25], '%', 'Intermediate'],
        
        # S4 - OCCUPATIONAL HEALTH & SAFETY
        ['S4.1', 'Fatalities', str(safe_get(sedg_data, 's41_fatalities', 0)), 'number', 'Basic'],
        ['S4.1', 'Injuries', str(safe_get(sedg_data, 's41_injuries', 0)), 'number', 'Basic'],
        ['S4.2', 'H&S trained employees (num)', str(safe_get(sedg_data, 's42_hs_trained_num', 0)), 'number', 'Intermediate'],
        ['S4.2', 'H&S trained employees (%)', f"{safe_get(sedg_data, 's42_hs_trained_pct'):.1f}", '%', 'Intermediate'],
        
        # S5 - COMMUNITY ENGAGEMENT
        ['S5.1', 'Community investment', f"{safe_get(sedg_data, 's51_community_invest'):.2f}", 'MYR', 'Basic'],
        ['S5.2', 'Negative community impact', safe_str(sedg_data, 's52_negative_impact', 'None')[:25], 'list', 'Advanced'],
    ]
    
    soc_table = Table(soc_data, colWidths=[0.6*inch, 2.6*inch, 1*inch, 0.9*inch, 0.9*inch])
    soc_table.setStyle(create_table_style(soc_data, 'social'))
    elements.append(soc_table)
    elements.append(PageBreak())
    
    # GOVERNANCE DISCLOSURES
    elements.append(Paragraph("GOVERNANCE DISCLOSURES", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    gov_data = [
        ['Code', 'Description', 'Value', 'Unit', 'Level'],
        
        # G1 - GOVERNANCE STRUCTURE
        ['G1.1', 'Number of directors', str(safe_get(sedg_data, 'g11_num_directors', 0)), 'number', 'Basic'],
        ['G1.2', 'Governance structure', safe_str(sedg_data, 'g12_structure', 'N/A')[:30], 'description', 'Intermediate'],
        
        # G2 - POLICY COMMITMENTS
        ['G2.1', 'Company policies', safe_str(sedg_data, 'g21_policies', 'N/A')[:30], 'list', 'Basic'],
        
        # G3 - RISK MANAGEMENT
        ['G3.1', 'Last audit year', str(safe_get(sedg_data, 'g31_audit_year', datetime.now().year)), 'year', 'Basic'],
        ['G3.2', 'Operations risks', safe_str(sedg_data, 'g32_ops_risks', 'N/A')[:30], 'list', 'Intermediate'],
        ['G3.3', 'Sustainability risks', safe_str(sedg_data, 'g33_sustain_risks', 'N/A')[:30], 'list', 'Advanced'],
        
        # G4 - ANTI-CORRUPTION
        ['G4.1', 'Corruption incidents', str(safe_get(sedg_data, 'g41_corrupt_incidents', 0)), 'number', 'Basic'],
        ['G4.1', 'Nature of corruption', safe_str(sedg_data, 'g41_corrupt_nature', 'None')[:30], 'description', 'Basic'],
        ['G4.2', 'Anti-corruption trained (num)', str(safe_get(sedg_data, 'g42_anticorrupt_num', 0)), 'number', 'Intermediate'],
        ['G4.2', 'Anti-corruption trained (%)', f"{safe_get(sedg_data, 'g42_anticorrupt_pct'):.1f}", '%', 'Intermediate'],
        ['G4.3', 'Corruption risks', safe_str(sedg_data, 'g43_corrupt_risks', 'N/A')[:30], 'list', 'Advanced'],
        
        # G5 - CUSTOMER PRIVACY
        ['G5.1', 'Privacy complaints', str(safe_get(sedg_data, 'g51_privacy_complaints', 0)), 'number', 'Intermediate'],
        ['G5.1', 'Nature of privacy complaints', safe_str(sedg_data, 'g51_privacy_nature', 'None')[:30], 'description', 'Intermediate'],
    ]
    
    gov_table = Table(gov_data, colWidths=[0.6*inch, 2.6*inch, 1*inch, 0.9*inch, 0.9*inch])
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
    """Create consistent table style with color coding."""
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    
    # Color code by level
    for i, row in enumerate(data[1:], start=1):
        level = row[4].lower()
        if level in COLORS[category]:
            color = COLORS[category][level]
            style.append(('BACKGROUND', (4, i), (4, i), color))
            if level in ['basic', 'intermediate']:
                style.append(('TEXTCOLOR', (4, i), (4, i), colors.white))
    
    return TableStyle(style)
from datetime import datetime
from io import BytesIO
from typing import Mapping, Any, List


def generate_iesg_pdf(state: Mapping[str, Any]) -> BytesIO:
    """Generate a professional ESG Ready Questionnaire PDF.

    Expects keys prefixed with 'iesg_' as used in the Streamlit session_state.
    Returns a BytesIO positioned at start, ready to be served as a file.
    """
    # Lazy import to avoid hard dependency unless invoked
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    
    # Professional color scheme
    primary_color = colors.HexColor('#1f4788')
    secondary_color = colors.HexColor('#2d5f8b')
    accent_color = colors.HexColor('#4a90e2')
    text_gray = colors.HexColor('#333333')
    light_gray = colors.HexColor('#f5f5f5')
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=secondary_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.white,
        spaceAfter=16,
        spaceBefore=20,
        fontName='Helvetica-Bold',
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=text_gray,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        leftIndent=10,
    )
    
    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=text_gray,
        spaceAfter=14,
        leftIndent=20,
        fontName='Helvetica',
        alignment=TA_JUSTIFY,
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
    )

    def add_section_header(title: str, content_list: List[Any]):
        """Add a styled section header with background"""
        header_table = Table(
            [[Paragraph(title, heading_style)]],
            colWidths=[6.5*inch]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content_list.append(header_table)
        content_list.append(Spacer(1, 0.15*inch))

    def escape_html(text: str) -> str:
        """Escape special HTML characters to prevent XML parsing errors"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    def add_qa(question: str, answer: Any, content_list: List[Any]):
        """Add a question-answer pair with professional styling"""
        # Escape question text
        safe_question = escape_html(question)
        content_list.append(Paragraph(f"• {safe_question}", question_style))
        
        if isinstance(answer, list):
            if answer:
                # Escape each item in the list
                safe_items = [escape_html(item) for item in answer]
                answer_text = ", ".join(safe_items)
            else:
                answer_text = "<i>Not specified</i>"
        else:
            if answer not in (None, ""):
                answer_text = escape_html(str(answer))
            else:
                answer_text = "<i>Not specified</i>"
        
        content_list.append(Paragraph(answer_text, answer_style))

    content: List[Any] = []

    # Cover page
    content.append(Spacer(1, 1.5*inch))
    content.append(Paragraph("ESG Ready Questionnaire", title_style))
    content.append(Paragraph("ESG Readiness Self-Assessment Report", subtitle_style))
    content.append(Spacer(1, 0.5*inch))

    # Score display with visual box
    if 'iesg_score' in state and 'iesg_max_score' in state and 'iesg_percentage' in state:
        pct = float(state['iesg_percentage'])
        
        # Determine color based on score
        if pct >= 80:
            score_color = colors.HexColor('#2e7d32')  # Green
            interpretation = "Excellent - Strong ESG readiness and maturity"
        elif pct >= 60:
            score_color = colors.HexColor('#1976d2')  # Blue
            interpretation = "Good Progress - On the right track with room for improvement"
        elif pct >= 40:
            score_color = colors.HexColor('#f57c00')  # Orange
            interpretation = "Developing - Started ESG journey, needs more comprehensive implementation"
        else:
            score_color = colors.HexColor('#c62828')  # Red
            interpretation = "Getting Started - Early stages of ESG implementation"
        
        score_data = [
            [Paragraph(f"<font size=18><b>{state['iesg_score']}/{state['iesg_max_score']}</b></font>", 
                      ParagraphStyle('ScoreNum', alignment=TA_CENTER, textColor=score_color))],
            [Paragraph(f"<font size=14><b>{state['iesg_percentage']:.1f}%</b></font>", 
                      ParagraphStyle('ScorePct', alignment=TA_CENTER, textColor=score_color))],
            [Spacer(1, 0.1*inch)],
            [Paragraph(f"<b>{interpretation}</b>", 
                      ParagraphStyle('ScoreInt', alignment=TA_CENTER, fontSize=11, textColor=text_gray))]
        ]
        
        score_table = Table(score_data, colWidths=[5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('BOX', (0, 0), (-1, -1), 2, score_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        content.append(score_table)
        content.append(Spacer(1, 0.5*inch))

    # Meta information
    content.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", meta_style))
    content.append(Paragraph(f"Company: {state.get('iesg_company_name', 'N/A')}", meta_style))
    
    content.append(PageBreak())

    # Section A - Company Information
    add_section_header("Section A: About The Company", content)
    
    add_qa("Company Name", state.get('iesg_company_name'), content)
    add_qa("Email Address", state.get('iesg_email'), content)
    add_qa("Phone Number", state.get('iesg_phone'), content)
    add_qa("Location", state.get('iesg_location'), content)
    add_qa("Sub-sector", state.get('iesg_subsector'), content)
    
    if state.get('iesg_subsector') == "Other (please specify)":
        add_qa("Sub-sector (Other)", state.get('iesg_subsector_other'), content)
    
    add_qa("Company Size", state.get('iesg_company_size'), content)
    add_qa("Company Type", state.get('iesg_company_type'), content)
    add_qa("Sustainability Reporting Standards", state.get('iesg_reporting_standard', []), content)
    
    if "None of the above" in state.get('iesg_reporting_standard', []):
        add_qa("Reason for No Standard", state.get('iesg_none_reason', []), content)

    content.append(PageBreak())

    # Section B - General Understanding
    add_section_header("Section B: General Understanding of ESG", content)
    
    add_qa("Q8. ESG Maturity Level", state.get('iesg_q8_maturity'), content)
    add_qa("Q9. Stakeholder Engagements", state.get('iesg_q9_stakeholders', []), content)
    add_qa("Q10. Business Case Elements", state.get('iesg_q10_business_case'), content)
    add_qa("Q11. ESG Goals and Targets", state.get('iesg_q11_esg_goals'), content)
    add_qa("Q12. ESG Leadership and Responsibility", state.get('iesg_q12_esg_leadership'), content)
    add_qa("Q13. ESG Reporting Standards Familiarity", state.get('iesg_q13_esg_reporting'), content)
    add_qa("Q14. ESG Data Understanding", state.get('iesg_q14_data_understanding'), content)
    add_qa("Q15. Understanding of ESG Elements", state.get('iesg_q15_esg_elements'), content)
    add_qa("Q16. Third-Party Validation", state.get('iesg_q16_validation'), content)

    content.append(PageBreak())

    # Section C - Environment
    add_section_header("Section C: Environmental Practices", content)
    
    add_qa("Q17. Carbon Footprint Reduction Initiatives", state.get('iesg_q17_carbon'), content)
    add_qa("Q18. GHG Emissions Tracking", state.get('iesg_q18_ghg'), content)
    add_qa("Q19. Water Efficiency Measures", state.get('iesg_q19_water'), content)
    add_qa("Q20. Material, Waste and Effluent Management", state.get('iesg_q20_waste'), content)
    add_qa("Q21. Waste-Water Management System", state.get('iesg_q21_wastewater'), content)
    add_qa("Q22. Energy Consumption Monitoring", state.get('iesg_q22_energy'), content)
    add_qa("Q23. Biodiversity Protection", state.get('iesg_q23_biodiversity'), content)
    add_qa("Q24. Eco-Friendly Raw Materials Usage", state.get('iesg_q24_eco_materials'), content)
    add_qa("Q25. Reforestation and Afforestation Programs", state.get('iesg_q25_reforestation'), content)

    content.append(PageBreak())

    # Section D - Social
    add_section_header("Section D: Social Responsibility", content)
    
    add_qa("Q26. Employee Involvement in ESG", state.get('iesg_q26_employee_involvement'), content)
    add_qa("Q27. Compliance with Domestic Labour Laws", state.get('iesg_q27_domestic_labour'), content)
    add_qa("Q28. Compliance with International Labour Laws", state.get('iesg_q28_intl_labour'), content)
    add_qa("Q29. Equal Employment Opportunities", state.get('iesg_q29_equal_employment'), content)
    add_qa("Q30. Minimum Wage Compliance", state.get('iesg_q30_min_wage'), content)
    add_qa("Q31. Occupational Health & Safety Programs", state.get('iesg_q31_health_safety'), content)
    add_qa("Q32. Grievance Handling Mechanism", state.get('iesg_q32_grievance'), content)
    add_qa("Q33. Employee Upskilling Programmes", state.get('iesg_q33_upskilling'), content)
    add_qa("Q34. Community Engagement and Development", state.get('iesg_q34_community'), content)

    content.append(PageBreak())

    # Section E - Governance
    add_section_header("Section E: Corporate Governance", content)
    
    add_qa("Q35. Board Leadership Structure", state.get('iesg_q35_board_leadership'), content)
    add_qa("Q36. Board and Management ESG Awareness", state.get('iesg_q36_board_awareness'), content)
    add_qa("Q37. Organizational Strategy Integration", state.get('iesg_q37_strategy'), content)
    add_qa("Q38. Code of Conduct Implementation", state.get('iesg_q38_code_conduct'), content)
    add_qa("Q39. Anti-Corruption Management System", state.get('iesg_q39_anti_corruption'), content)
    add_qa("Q40. Whistleblower Protection Program", state.get('iesg_q40_whistleblower'), content)
    add_qa("Q41. Financial Accounting System", state.get('iesg_q41_accounting'), content)
    add_qa("Q42. Data Privacy and Security System", state.get('iesg_q42_data_privacy'), content)

    # Footer
    content.append(Spacer(1, 0.5*inch))
    footer_table = Table(
        [[Paragraph("End of ESG Ready Questionnaire Report", meta_style)]],
        colWidths=[6.5*inch]
    )
    footer_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    content.append(footer_table)

    doc.build(content)
    buffer.seek(0)
    return buffer
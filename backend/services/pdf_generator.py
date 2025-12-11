"""
PDF Report Generator - Creates learning progress reports
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from typing import Dict, List, Any
import io


class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle('CustomTitle', parent=self.styles['Heading1'],
            fontSize=24, spaceAfter=30, textColor=colors.HexColor('#667eea'))
        self.heading_style = ParagraphStyle('CustomHeading', parent=self.styles['Heading2'],
            fontSize=16, spaceAfter=12, textColor=colors.HexColor('#333333'))
    
    def generate_progress_report(self, user_data: Dict, progress_data: List[Dict],
                                  quiz_results: List[Dict], output_path: str = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        story = []
        
        story.append(Paragraph("📚 Learning Progress Report", self.title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # User Summary
        story.append(Paragraph("👤 Learner Profile", self.heading_style))
        user_info = [[f"Name: {user_data.get('username', 'N/A')}", f"Level: {user_data.get('current_level', 'N/A')}"],
                     [f"Goal: {user_data.get('learning_goal', 'N/A')}", f"Speed: {user_data.get('learning_speed', 'N/A')}"]]
        story.append(Table(user_info, colWidths=[250, 250]))
        story.append(Spacer(1, 20))
        
        # Progress Summary
        if progress_data:
            story.append(Paragraph("📈 Topic Progress", self.heading_style))
            table_data = [["Topic", "Mastery", "Time Spent", "Status"]]
            for p in progress_data[:10]:
                mastery = f"{p.get('mastery_level', 0):.0f}%"
                time_spent = f"{p.get('time_spent_minutes', 0)} min"
                status = "✅" if p.get('mastery_level', 0) >= 70 else "📖"
                table_data.append([p.get('topic_name', 'N/A'), mastery, time_spent, status])
            t = Table(table_data, colWidths=[180, 80, 100, 60])
            t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 1, colors.grey)]))
            story.append(t)
        
        story.append(Spacer(1, 20))
        
        # Quiz Performance
        if quiz_results:
            story.append(Paragraph("📝 Recent Quiz Performance", self.heading_style))
            avg_score = sum(q.get('score', 0) for q in quiz_results) / len(quiz_results)
            story.append(Paragraph(f"Average Score: {avg_score:.1f}%", self.styles['Normal']))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        return pdf_bytes

"""
Report Generation Utilities for MODIS Vegetation Analysis
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF report generation will be disabled.")


class ReportGenerator:
    """Generate comprehensive PDF reports from MODIS analysis results"""
    
    def __init__(self, output_dir: Path):
        """
        Initialize report generator
        
        Args:
            output_dir: Base output directory containing analysis results
        """
        self.output_dir = Path(output_dir)
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        
        if REPORTLAB_AVAILABLE:
            # Custom styles
            self.title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            self.heading_style = ParagraphStyle(
                'CustomHeading',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#34495E'),
                spaceAfter=12,
                spaceBefore=12
            )
    
    def create_comprehensive_report(self, year: int) -> Optional[str]:
        """
        Create a comprehensive PDF report
        
        Args:
            year: Analysis year
            
        Returns:
            Path to generated PDF or None if reportlab not available
        """
        if not REPORTLAB_AVAILABLE:
            print("Cannot generate PDF report: reportlab not installed")
            return None
        
        pdf_path = self.output_dir / f"MODIS_Comprehensive_Report_{year}.pdf"
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        elements = []
        
        # Cover Page
        elements.extend(self._create_cover_page(year))
        elements.append(PageBreak())
        
        # Executive Summary
        elements.extend(self._create_executive_summary(year))
        elements.append(PageBreak())
        
        # AOI Information
        elements.extend(self._create_aoi_section())
        elements.append(PageBreak())
        
        # Monthly Composites Section
        elements.extend(self._create_composites_section(year))
        
        # Trend Analysis Section
        elements.extend(self._create_trends_section(year))
        elements.append(PageBreak())
        
        # Statistics Section
        elements.extend(self._create_statistics_section(year))
        
        # Build PDF
        doc.build(elements)
        print(f"📘 Comprehensive PDF report generated: {pdf_path}")
        
        return str(pdf_path)
    
    def _create_cover_page(self, year: int) -> List:
        """Create cover page elements"""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(
            f"MODIS Vegetation Analysis Report",
            self.title_style
        ))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Analysis Year: {year}",
            ParagraphStyle('Subtitle', 
                          parent=self.styles['Normal'],
                          fontSize=18,
                          alignment=TA_CENTER,
                          textColor=colors.HexColor('#7F8C8D'))
        ))
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            ParagraphStyle('Date',
                          parent=self.styles['Normal'],
                          fontSize=12,
                          alignment=TA_CENTER,
                          textColor=colors.grey)
        ))
        
        return elements
    
    def _create_executive_summary(self, year: int) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.heading_style))
        elements.append(Spacer(1, 12))
        
        # Load metadata
        metadata_path = self.output_dir / "metadata" / "analysis_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            summary_text = f"""
            This report presents a comprehensive vegetation analysis for {year} using MODIS MOD13Q1 data 
            at 250m resolution. The analysis covers {metadata['aoi_info'].get('area_km2', 'N/A'):.2f} km².
            <br/><br/>
            Key vegetation indices analyzed:
            <br/>• NDVI (Normalized Difference Vegetation Index)
            <br/>• EVI (Enhanced Vegetation Index)
            <br/>• VCI (Vegetation Condition Index)
            <br/><br/>
            Analysis includes monthly composites, trend analysis, and statistical summaries.
            """
            
            elements.append(Paragraph(summary_text, self.styles['BodyText']))
        
        return elements
    
    def _create_aoi_section(self) -> List:
        """Create AOI information section"""
        elements = []
        
        elements.append(Paragraph("Study Area (Area of Interest)", self.heading_style))
        elements.append(Spacer(1, 12))
        
        # Add AOI map if available
        aoi_map = self.output_dir / "maps" / "aoi_overview.png"
        if aoi_map.exists():
            elements.append(RLImage(str(aoi_map), width=7*inch, height=5*inch))
            elements.append(Spacer(1, 12))
        
        # Add AOI statistics table
        metadata_path = self.output_dir / "metadata" / "analysis_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            aoi_info = metadata.get('aoi_info', {})
            
            data = [
                ['Property', 'Value'],
                ['Total Area', f"{aoi_info.get('area_km2', 'N/A'):.2f} km²"],
                ['Feature Count', str(aoi_info.get('feature_count', 'N/A'))],
                ['Coordinate System', str(aoi_info.get('crs', 'N/A'))],
            ]
            
            table = Table(data, colWidths=[2.5*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')])
            ]))
            
            elements.append(table)
        
        return elements
    
    def _create_composites_section(self, year: int) -> List:
        """Create monthly composites section"""
        elements = []
        
        elements.append(Paragraph("Monthly Composite Analysis", self.heading_style))
        elements.append(Spacer(1, 12))
        
        composites_dir = self.output_dir / "composites"
        
        if composites_dir.exists():
            # Group by index
            for index in ["NDVI", "EVI", "VCI"]:
                elements.append(Paragraph(f"{index} Composites", self.styles['Heading3']))
                elements.append(Spacer(1, 8))
                
                # Show sample composites (e.g., mean for selected months)
                sample_months = [3, 6, 9, 12]  # Mar, Jun, Sep, Dec
                
                for month in sample_months:
                    img_path = composites_dir / f"{index}_mean_{year}_{month:02d}.png"
                    if img_path.exists():
                        elements.append(Paragraph(
                            f"{index} Mean - {datetime(year, month, 1).strftime('%B')}",
                            self.styles['Normal']
                        ))
                        elements.append(RLImage(str(img_path), width=5*inch, height=3*inch))
                        elements.append(Spacer(1, 8))
                
                elements.append(PageBreak())
        
        return elements
    
    def _create_trends_section(self, year: int) -> List:
        """Create trend analysis section"""
        elements = []
        
        elements.append(Paragraph("Temporal Trend Analysis", self.heading_style))
        elements.append(Spacer(1, 12))
        
        trends_dir = self.output_dir / "trends"
        
        if trends_dir.exists():
            for index in ["NDVI", "EVI", "VCI"]:
                img_path = trends_dir / f"{index}_trend_{year}.png"
                if img_path.exists():
                    elements.append(Paragraph(f"{index} Monthly Trend", self.styles['Heading3']))
                    elements.append(Spacer(1, 8))
                    elements.append(RLImage(str(img_path), width=8*inch, height=4*inch))
                    elements.append(Spacer(1, 16))
        
        return elements
    
    def _create_statistics_section(self, year: int) -> List:
        """Create statistics section"""
        elements = []
        
        elements.append(Paragraph("Statistical Summary", self.heading_style))
        elements.append(Spacer(1, 12))
        
        csv_path = self.output_dir / "statistics" / f"monthly_summary_{year}.csv"
        
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            
            data = [list(df.columns)] + df.values.tolist()
            
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')])
            ]))
            
            elements.append(table)
        
        return elements


def generate_markdown_report(output_dir: Path, year: int) -> str:
    """
    Generate a markdown summary report
    
    Args:
        output_dir: Output directory
        year: Analysis year
        
    Returns:
        Path to generated markdown file
    """
    md_path = output_dir / f"MODIS_Report_{year}.md"
    
    with open(md_path, 'w') as f:
        f.write(f"# MODIS Vegetation Analysis Report - {year}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y %H:%M:%S')}\n\n")
        
        # Load metadata
        metadata_path = output_dir / "metadata" / "analysis_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as mf:
                metadata = json.load(mf)
            
            f.write("## Study Area\n\n")
            aoi_info = metadata.get('aoi_info', {})
            f.write(f"- **Total Area:** {aoi_info.get('area_km2', 'N/A'):.2f} km²\n")
            f.write(f"- **Feature Count:** {aoi_info.get('feature_count', 'N/A')}\n")
            f.write(f"- **CRS:** {aoi_info.get('crs', 'N/A')}\n\n")
        
        f.write("## Analysis Components\n\n")
        f.write("1. Monthly composite imagery (NDVI, EVI, VCI)\n")
        f.write("2. Temporal trend analysis\n")
        f.write("3. Statistical summaries\n\n")
        
        f.write("## Output Structure\n\n")
        f.write("```\n")
        f.write(f"{output_dir.name}/\n")
        f.write("├── composites/       # Monthly composite images\n")
        f.write("├── trends/           # Trend line plots\n")
        f.write("├── statistics/       # CSV statistics files\n")
        f.write("├── maps/             # Maps and visualizations\n")
        f.write("├── metadata/         # Analysis metadata\n")
        f.write("└── exports/          # Exported data products\n")
        f.write("```\n\n")
        
        f.write("## Data Sources\n\n")
        f.write("- **MODIS Collection:** MOD13Q1.061\n")
        f.write("- **Spatial Resolution:** 250m\n")
        f.write("- **Temporal Resolution:** 16-day\n\n")
    
    print(f"📝 Markdown report generated: {md_path}")
    return str(md_path)
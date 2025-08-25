import json
import os
import io
import base64
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import reportlab.lib.pagesizes as pagesizes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import sys
from datetime import datetime

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

def get_action_description(step):
    """Generate a clear description of the action performed."""
    action_type = step.get("action_type", "unknown")
    text = step.get("text", "")
    keys = step.get("keys", "")
    coordinates = step.get("coordinates", [0, 0])
    
    descriptions = {
        "left_click": f"Left click at position ({coordinates[0]}, {coordinates[1]})",
        "right_click": f"Right click at position ({coordinates[0]}, {coordinates[1]})",
        "typing": f"Type text: '{text}'" if text else "Type text",
        "shortcut": f"Press keyboard shortcut: {keys}" if keys else "Press keyboard shortcut",
        "drag": f"Drag from position ({coordinates[0]}, {coordinates[1]})",
        "scroll": f"Scroll at position ({coordinates[0]}, {coordinates[1]})",
        "wait": "Wait/Pause",
        "screenshot": "Take screenshot"
    }
    
    return descriptions.get(action_type, f"{action_type.replace('_', ' ').title()} at ({coordinates[0]}, {coordinates[1]})")

def convert_to_pdf(tutorial_data):
    """
    Converts a tutorial dictionary into a PDF document.
    
    Args:
        tutorial_data (dict): A dictionary containing the tutorial steps and metadata.
    """
    if not tutorial_data:
        messagebox.showerror("Error", "No tutorial has been loaded.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF As"
    )

    if not file_path:
        return

    try:
        pdf = SimpleDocTemplate(file_path, pagesize=pagesizes.letter,
                                leftMargin=25*mm, rightMargin=25*mm,
                                topMargin=25*mm, bottomMargin=25*mm)
        story = []
        styles = getSampleStyleSheet()

        # Create custom styles
        title_style = ParagraphStyle('TitleStyle', 
                                     parent=styles['Title'],
                                     fontSize=24,
                                     alignment=TA_CENTER,
                                     spaceAfter=20,
                                     textColor=colors.darkblue)
        
        step_header_style = ParagraphStyle('StepHeaderStyle',
                                           parent=styles['Heading2'],
                                           fontSize=16,
                                           spaceAfter=10,
                                           spaceBefore=15,
                                           textColor=colors.darkblue,
                                           borderWidth=1,
                                           borderColor=colors.lightgrey,
                                           borderPadding=5,
                                           backColor=colors.lightgrey)
        
        info_style = ParagraphStyle('InfoStyle',
                                    parent=styles['Normal'],
                                    fontSize=10,
                                    spaceAfter=6)

        # Title page with name from JSON
        tutorial_name = tutorial_data.get("name", "Untitled Tutorial")
        story.append(Paragraph(tutorial_name, title_style))
        story.append(Spacer(1, 20))
        
        # Create info table
        version = tutorial_data.get('version', 'N/A')
        total_steps = len(tutorial_data.get('steps', []))
        
        info_data = [
            ['Version:', version],
            ['Total Steps:', str(total_steps)]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        story.append(PageBreak())

        # Load font for annotations
        try:
            font_path = os.path.join(get_base_path(), "arial.ttf")
            if not os.path.exists(font_path):
                font_path = "C:\\Windows\\Fonts\\Arial.ttf"
                if not os.path.exists(font_path):
                    font_path = "/Library/Fonts/Arial.ttf"
            
            font = ImageFont.truetype(font_path, 36)
        except IOError:
            print("Font file not found. Using default font.")
            font = ImageFont.load_default()
        
        # Process each step
        for i, step in enumerate(tutorial_data.get("steps", [])):
            step_number = step.get("step_number", i + 1)
            action_description = get_action_description(step)
            
            # Step header with action
            story.append(Paragraph(f"Step {step_number}: {action_description}", step_header_style))
            
            # Add notes if available
            notes = step.get("notes", "").strip()
            if notes:
                story.append(Paragraph(f"<b>Notes:</b> {notes}", styles['Normal']))
            
            story.append(Spacer(1, 10))

            # Process screenshot if available
            screenshot_data = step.get("screenshot")
            if screenshot_data and screenshot_data != "--image data--":
                try:
                    full_data = base64.b64decode(screenshot_data)
                    full_image = Image.open(io.BytesIO(full_data))
                    
                    coordinates = step.get("coordinates", [0, 0])
                    if coordinates != [0, 0]:
                        x, y = coordinates
                        draw = ImageDraw.Draw(full_image)
                        
                        radius = 30
                        draw.ellipse((x - radius, y - radius, x + radius, y + radius), 
                                     outline=(255, 0, 0), width=4)
                        
                        text_to_draw = action_description
                        bbox = draw.textbbox((0, 0), text_to_draw, font=font)
                        text_width = bbox[2] - bbox[0]

                        image_width, image_height = full_image.size
                        
                        if x + radius + 10 + text_width < image_width:
                            text_x = x + radius + 10
                        else:
                            text_x = x - radius - 10 - text_width
                        
                        text_y = y - 10
                        
                        draw.text((text_x, text_y), text_to_draw, fill=(255, 0, 0), font=font)
                    
                    full_img_stream = io.BytesIO()
                    full_image.save(full_img_stream, format="PNG")
                    full_img_stream.seek(0)
                    
                    max_width = 6.5 * inch
                    max_height = 4.5 * inch
                    image_width, image_height = full_image.size
                    
                    width_scale = max_width / image_width
                    height_scale = max_height / image_height
                    scale_factor = min(width_scale, height_scale)
                    
                    final_width = image_width * scale_factor
                    final_height = image_height * scale_factor
                    
                    story.append(Paragraph("<b>Screenshot:</b>", styles['Normal']))
                    full_img = ReportlabImage(full_img_stream, width=final_width, height=final_height)
                    story.append(full_img)
                    
                except Exception as e:
                    story.append(Paragraph(f"<i>Screenshot could not be processed: {str(e)}</i>", 
                                           styles['Italic']))
            else:
                story.append(Paragraph("<i>No screenshot available for this step.</i>", 
                                       styles['Italic']))

            story.append(Spacer(1, 20))
            
            if i < len(tutorial_data.get("steps", [])) - 1:
                story.append(PageBreak())

        pdf.build(story)
        messagebox.showinfo("Success", f"PDF created successfully at:\n{file_path}")

    except Exception as e:
        print(f"Error details: {str(e)}")
        messagebox.showerror("Conversion Error", f"An error occurred during PDF conversion:\n{e}")
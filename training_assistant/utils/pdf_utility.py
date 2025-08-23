import json
import os
import io
import base64
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw
import reportlab.lib.pagesizes as pagesizes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm

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
        title="Save Tutorial as PDF"
    )
    
    if not file_path:
        return

    try:
        pdf = SimpleDocTemplate(file_path, pagesize=pagesizes.letter,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], spaceAfter=10, fontSize=18, alignment=1)
        story.append(Paragraph(tutorial_data.get("name", "Tutorial"), title_style))
        story.append(Spacer(1, 12))
        
        info_style = styles['Normal']
        story.append(Paragraph(f"<b>Created:</b> {tutorial_data.get('created', 'N/A')}", info_style))
        story.append(Paragraph(f"<b>Total Steps:</b> {len(tutorial_data['steps'])}", info_style))
        story.append(Spacer(1, 12))

        for i, step in enumerate(tutorial_data["steps"]):
            step_heading = ParagraphStyle('StepHeading', parent=styles['Heading2'], spaceAfter=6, fontSize=14)
            story.append(Paragraph(f"<b>Step {i + 1}:</b>", step_heading))
            if step.get("notes"):
                story.append(Paragraph(f"{step['notes']}", styles['Normal']))
            story.append(Spacer(1, 10))

            if step.get("screenshot"): 
                full_data = base64.b64decode(step["screenshot"])
                full_image = Image.open(io.BytesIO(full_data))
                x, y = step["coordinates"]
                draw = ImageDraw.Draw(full_image)
                radius = 30
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=(255, 0, 0), width=4)
                
                full_img_stream = io.BytesIO()
                full_image.save(full_img_stream, format="PNG")
                full_img_stream.seek(0)
                scaler = 8
                
                story.append(Paragraph("<b>Full Screen:</b>", styles['Normal']))
                full_img = ReportlabImage(full_img_stream, width=scaler * inch, height=full_image.height * scaler * inch / full_image.width)
                story.append(full_img)
                story.append(Spacer(1, 10))
            else:
                story.append(Paragraph("<i>Full screen image not available for this step.</i>", styles['Normal']))

        pdf.build(story)
        messagebox.showinfo("Success", f"PDF created successfully at:\n{file_path}")

    except Exception as e:
        messagebox.showerror("Conversion Error", f"An error occurred during PDF conversion:\n{e}")
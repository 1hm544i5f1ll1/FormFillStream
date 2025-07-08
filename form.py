# generate_form.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.acroform import AcroForm

def create_form(path):
    c = canvas.Canvas(path, pagesize=letter)
    form = c.acroForm

    c.drawString( 50, 700, "First Name:")
    form.textfield(name="first_name", x=150, y=685, width=300, height=20)

    c.drawString( 50, 650, "Last Name:")
    form.textfield(name="last_name", x=150, y=635, width=300, height=20)

    c.drawString( 50, 600, "Email:")
    form.textfield(name="email", x=150, y=585, width=300, height=20)

    c.save()

if __name__ == "__main__":
    create_form("demo_form.pdf")
    print("demo_form.pdf created.")

Full Architecture:
Frontend (React)
        │
        ▼
FastAPI API
        │
        ▼
ConversionService
        │
        ▼
Pipeline
  ├─ PdfToSvg
  ├─ SvgToGCode
  └─ MultiColourManager
        │
        ▼
Generated Files

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Backend process
Frontend
   │
   ▼
POST /convert
   │
   ▼
ConvertRequest (model validates input)
   │
   ▼
convert() endpoint
   │
   ▼
ConversionService
   │
   ▼
Pipeline (PDF → SVG → GCODE)
   │
   ▼
Response sent back

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Frontend Process
Upload PDF
      │
      ▼
POST /analyze
      │
      ▼
Frontend decides:
   rotate?
   scale?
   docks?
      │
      ▼
POST /convert
      │
      ▼
Download GCODE

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Frontend design
Home
Mode Select (Google docs/goodnotes - where split compound paths is defined)
Printer
Upload PDF + line segments detail
transformation (scaling, rotating)
dock select for multicolour
Output

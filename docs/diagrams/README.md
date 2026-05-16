# Project Diagrams

## Files

- `erd.mmd` - Database ERD (Mermaid)
- `overall_functional_flow.mmd` - Application functional flow
- `view_diagrams.html` - Open in browser to view diagrams
- `images/erd_diagram.png` - ERD image
- `images/overall_functional_flow.png` - Flow image

## View

Open `view_diagrams.html` in your browser.

## Regenerate PNG

```powershell
cd "e:\Python Project\CanteenManagementSystem\docs\diagrams"
npx -y @mermaid-js/mermaid-cli -i erd.mmd -o images/erd_diagram.png -b white
npx -y @mermaid-js/mermaid-cli -i overall_functional_flow.mmd -o images/overall_functional_flow.png -b white
```

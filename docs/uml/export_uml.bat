@echo off
REM Export all Mermaid .mmd files in this directory to PNG using mermaid-cli (mmdc)
for %%f in (*.mmd) do (
  echo Exporting %%f ...
  mmdc -i "%%f" -o "%%~nf.png"
)
echo Done.


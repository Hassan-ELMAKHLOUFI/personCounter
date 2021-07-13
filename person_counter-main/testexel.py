from openpyxl import load_workbook

# Start by opening the spreadsheet and selecting the main sheet
workbook = load_workbook(filename="demo.xlsx")
sheet = workbook.active

# Write what you want into a specific cell
column ="e"+str(1);
sheet[column] = "writing ;)"
sheet["D1"] = "ecrire )"
# Save the spreadsheet
workbook.save(filename="demo.xlsx")
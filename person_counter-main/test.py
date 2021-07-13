import openpyxl

wb_obj = openpyxl.load_workbook("demo.xlsx")

sheet_obj = wb_obj.active

cell_obj = sheet_obj.cell(row = 1, column = 1)

print(cell_obj.value)

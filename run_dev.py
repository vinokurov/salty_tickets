import sys
path = '/salty_tickets/'
if path not in sys.path:
   sys.path.append(path)

from salty_tickets import app
print(app.static_folder)
app.static_folder = r'c:\dev\satlty\salty_tickets\salty_tickets\static'
app.template_folder = r'c:\dev\satlty\salty_tickets\salty_tickets\templates'
print(app.static_folder)
app.run(debug=True)

import sys
path = '/salty_tickets/'
if path not in sys.path:
   sys.path.append(path)

from salty_tickets import tickets_app
print(tickets_app.static_folder)
tickets_app.static_folder = r'c:\dev\satlty\salty_tickets\salty_tickets\static'
tickets_app.template_folder = r'c:\dev\satlty\salty_tickets\salty_tickets\templates'
print(tickets_app.static_folder)
tickets_app.run(debug=True)

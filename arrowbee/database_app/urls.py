from django.urls import path
from .views import * 

urlpatterns = [
    path("diagram_editor/<str:diagram_id>", diagram_editor, name="diagram_editor"),
    path("save_diagram/<str:diagram_id>", save_diagram_to_database, name="save_diagram"),
    path("load_diagram/<str:diagram_id>", load_diagram_from_database, name="load_diagram"),
    path("new_diagram", create_new_diagram, name="new_diagram"),
    #path("messages", MessagesView.as_view(), name='messages'),    # TODO: Do we need this?; also enable in views
    path("my_diagram_list/<str:order_by>/<str:order_dir>/<int:page_num>", my_diagram_list, name='my_diagram_list'),
    path("embed_diagram/<str:diagram_id>", embed_diagram, name="embed_diagram"),
    path("functor_diagram/<str:diagram_id>", functor_diagram, name="functor_diagram"),
    path("rename_diagram/<str:diagram_id>", rename_diagram, name="rename_diagram"),
    path("rename_rule/<str:rule_id>", rename_rule, name="rename_rule"),   #change by dev    
    path("reassign_category/<str:diagram_id>", reassign_category, name="reassign_category"),
    path('new_rule', create_new_rule, name='new_rule'),
    path('rule_editor/<str:rule_id>', rule_editor, name='rule_editor'),
    path('add_assumption/<str:rule_id>', add_assumption, name='add_assumption'),  
    path('add_conclusion/<str:rule_id>', add_conclusion, name='add_conclusion'),
    path('add_diagram_to_rule/<str:diagram_id>', add_diagram_to_rule, name='add_diagram_to_rule'),
    path('delete_assumption/<str:assumption_id>/<str:rule_id>', delete_assumption, name='delete_assumption'),
    path('delete_conclusion/<str:conclusion_id>/<str:rule_id>', delete_conclusion, name='delete_conclusion'),
    path('set_assumption_avatar/<str:assumption_id>/<str:rule_id>', set_assumption_avatar,
         name='set_assumption_avatar'),      
    path('my_rule_list/<str:order_by>/<str:order_dir>/<int:page_num>', my_rule_list, name='my_rule_list'),
    path('delete_diagram/<str:diagram_id>', delete_diagram, name='delete_diagram'),    
    path('diagram_search/<str:diagram_id>/<str:order_by>/<str:order_dir>/<int:page_num>', diagram_search, name='diagram_search'),    
]


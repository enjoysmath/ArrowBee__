from neomodel import *
from django_neomodel import DjangoNode
from django.db import models
from arrowbee.settings import MAX_TEXT_LENGTH
from django.core.exceptions import ObjectDoesNotExist
from neomodel import db
from arrowbee.python_tools import deep_get, deep_set
from arrowbee.variable import Variable
from arrowbee.keyword import Keyword
from datetime import datetime
import json
import base64

# Create your models here.

class Model:
    @staticmethod
    def our_create(**kwargs):
        raise NotImplementedError
    
    
class Morphism(StructuredRel):
    #uid = StringProperty(default=Morphism.get_unique_id())
    name = StringProperty(max_length=MAX_TEXT_LENGTH)
    diagram_index = IntegerProperty(requied=True)   # Diagram code needs to keep this updated
    
    # RE-DESIGN: TODO - these need to be independent of style and settable in an accompanying
    # panel to the editor.
    # These are the mathematical properties, that you can search by:
    #epic = BooleanProperty(default=False)
    #monic = BooleanProperty(default=False)
    #inclusion = BooleanProperty(default=False)
    
    # Strictly style below this line:   
    NUM_LINES = { 1: 'one', 2: 'two', 3: 'three' }
    num_lines = IntegerProperty(choices=NUM_LINES, default=1)

    LeftAlign, CenterAlign, RightAlign, OverAlign = range(4)
    DefaultAlignment = LeftAlign    
     
    ALIGNMENT = { 0:LeftAlign,  1:RightAlign, 2:CenterAlign, 3:OverAlign}
    alignment = IntegerProperty(choices=ALIGNMENT, default=DefaultAlignment)
    
    label_position = IntegerProperty(default=50)
    offset = IntegerProperty(default=0)
    curve = IntegerProperty(default=0)
    tail_shorten = IntegerProperty(default=0)
    head_shorten = IntegerProperty(default=0)
    
    TAIL_STYLE = {0:'none', 1:'mono', 2:'hook', 3:'arrowhead', 4:'maps_to'}
    tail_style = IntegerProperty(choices=TAIL_STYLE, default=0)
        
    SIDE = {0:'none', 1:'top', 2:'bottom'}
    hook_tail_side = IntegerProperty(choices=SIDE, default=0)    
    
    HEAD_STYLE = {0:'none', 1:'arrowhead', 2:'epi', 3:'harpoon'}
    head_style = IntegerProperty(choices=HEAD_STYLE, default=1)
    harpoon_head_side = IntegerProperty(choices=SIDE, default=0)
    
    BODY_STYLE = {0:'solid', 1:'none', 2:'dashed', 3:'dotted', 4:'squiggly', 5:'barred'}
    body_style = IntegerProperty(choices=BODY_STYLE, default=0)
    
    color_hue = IntegerProperty(default=0)
    color_sat = IntegerProperty(default=0)   # BUGFIX: default (black) is 0,0,0 in hsl, not 0,100,0
    color_lum = IntegerProperty(default=0)
    color_alph = FloatProperty(default=1.0)
    
    def copy_properties_from(self, f, nodes_memo):
        self.name = f.name
        self.diagram_index = f.diagram_index
        self.num_lines = f.num_lines
        self.alignment = f.alignment
        self.label_position = f.label_position
        self.offset = f.offset
        self.curve = f.curve
        self.tail_shorten = f.tail_shorten
        self.head_shorten = f.head_shorten
        self.tail_style = f.tail_style
        self.hook_tail_side = f.hook_tail_side
        self.head_style = f.head_style
        self.harpoon_head_side = f.harpoon_head_side
        self.body_style = f.body_style
        self.color_hue = f.color_hue
        self.color_sat = f.color_sat
        self.color_lum = f.color_lum
        self.color_alph = f.color_alph
        self.save()
    
    def load_from_editor(self, format):         
        if len(format) > 2:
            self.name = format[2]
        else:
            self.name = ''   # BUGFIX: need this
        
        if len(format) > 3:
            self.alignment = format[3]
        
        if len(format) > 4:                
            options = format[4]            
            self.label_position = options.get('label_position', 50)
            self.offset = options.get('offset', 0)
            self.curve = options.get('curve', 0)
            shorten = options.get('shorten', {'source': 0, 'target': 0})
            self.tail_shorten = shorten.get('source', 0)
            self.head_shorten = shorten.get('target', 0)
            self.num_lines = options.get('level', 1)
            
            self.body_style = next(x for x,y in self.BODY_STYLE.items() \
                                   if y == deep_get(options, ('style', 'body', 'name'), 'solid'))
            
            self.tail_style = next(x for x,y in self.TAIL_STYLE.items() \
                                   if y == deep_get(options, ('style', 'tail', 'name'), 'none' ))
            
            side = deep_get(options, ('style', 'tail', 'side'), 'none')
            
            if isinstance(side, int):
                self.hook_tail_side = side
            else:
                self.hook_tail_side = next(x for x,y in self.SIDE.items() if y == side)
            
            self.head_style = next(x for x,y in self.HEAD_STYLE.items() \
                                   if y == deep_get(options, ('style', 'head', 'name'), 'arrowhead'))
            
            side = deep_get(options, ('style', 'head', 'side'), 'none')
            
            if isinstance(side, int):
                self.harpoon_head_side = side
            else:
                self.harpoon_head_side = next(x for x,y in self.SIDE.items() if y == side)
                
            if len(format) > 5:
                color = format[5]
            elif 'colour' in options:
                color = options['colour']
            else:
                color = [0, 0, 0, 1.0]  # BUGFIX: black is hsl:  0,0,0 not 0,100,0
                
            self.color_hue = color[0]
            self.color_sat = color[1]
            self.color_lum = color[2]
            
            if len(color) > 3:
                self.color_alph = color[3]            
        
        self.save()
        
    def quiver_format(self):
        format = [self.start_node().diagram_index, self.end_node().diagram_index]
        format.append(self.name if self.name is not None else '')
        format.append(self.alignment)
        options = {
            #'colour' : [self.color_hue, self.color_sat, self.color_lum, self.color_alph],
            'label_position': self.label_position,
            'offset' : self.offset,
            'curve' : self.curve,
            'shorten' : {
                'source' : self.tail_shorten,
                'target' : self.head_shorten,
            },
            'level' : self.num_lines,
            'style' : {
                'tail': {
                    'name' : self.TAIL_STYLE[self.tail_style],
                    'side' : self.SIDE[self.hook_tail_side],
                },
                'head': {
                    'name' : self.HEAD_STYLE[self.head_style],
                    'side' : self.SIDE[self.harpoon_head_side],
                },
                'body': {
                    'name' : self.BODY_STYLE[self.body_style],
                }                    
            },
            'colour' : [self.color_hue, self.color_sat, self.color_lum, self.color_alph],
        }
        format.append(options)
        format.append([self.color_hue, self.color_sat, self.color_lum, self.color_alph])
        return format
    
            
class Object(StructuredNode, Model):
    uid = UniqueIdProperty()
    name = StringProperty(max_length=MAX_TEXT_LENGTH)
    morphisms = RelationshipTo('Object', 'MAPS_TO', model=Morphism)   
        
    diagram_index = IntegerProperty(required=True)

    # Position & Color:
    x = IntegerProperty(default=0)
    y = IntegerProperty(default=0) 
    
    color_hue = IntegerProperty(default=0)
    color_sat = IntegerProperty(default=0)
    color_lum = IntegerProperty(default=0)
    color_alph = FloatProperty(default=1.0) 
    
    @staticmethod
    def our_create(**kwargs):
        ob = Object(**kwargs).save()
        return ob
    
    def copy(self, nodes_memo, **kwargs):
        copy = Object.our_create(**kwargs, diagram_index=self.diagram_index)
        nodes_memo[copy.diagram_index] = copy
        copy.name = self.name
        copy.x = self.x
        copy.y = self.y
        copy.color_hue = self.color_hue
        copy.color_sat = self.color_sat
        copy.color_lum = self.color_lum
        copy.alph = self.color_alph
                
        for f in self.all_morphisms():
            x = f.end_node()
            if x.diagram_index not in nodes_memo:
                x.copy(nodes_memo)
            y = nodes_memo[x.diagram_index]
            f1 = copy.morphisms.connect(y)
            f1.copy_properties_from(f, nodes_memo)  # Calls save()
            
        copy.save()
        
        return copy    
    
    def __repr__(self):
        return f'Object("{self.name}")'
    
    def all_morphisms(self):
        results, meta = db.cypher_query(
            f'MATCH (x:Object)-[f:MAPS_TO]->(y:Object) WHERE x.uid="{self.uid}" RETURN f')
        return [Morphism.inflate(row[0]) for row in results]
                    
    def delete(self):
        # Delete all the outgoing morphisms first:
        db.cypher_query(f'MATCH (o:Object)-[f:MAPS_TO]-(p:Object) WHERE o.uid="{self.uid}" DELETE f')       
        super().delete()
           
    @staticmethod
    def create_from_editor(format, index:int):
        o = Object(diagram_index=index)
        o.init_from_editor(format, index)
        return o
        
    def init_from_editor(self, format, index):
        o = self
        o.x = format[0]
        o.y = format[1]
        
        if len(format) > 2:
            o.name = format[2]
            
        if len(format) > 3:
            color = format[3]
            o.color_hue = color[0]
            o.color_sat = color[1]
            o.color_lum = color[2]
            o.color_alph = color[3]
        
        o.save()   
        return o
    
    def quiver_format(self):
        return [self.x, self.y, self.name, 
                [self.color_hue, self.color_sat, self.color_lum, self.color_alph]]
   
        
        
class Category(StructuredNode, Model):
    unique_fields = ['name']
    uid = UniqueIdProperty()
    name = StringProperty(max_length=MAX_TEXT_LENGTH, required=True)
    
    @staticmethod
    def our_create(**kwargs):
        category = Category(**kwargs).save()
        return category
    
        
class Diagram(StructuredNode, Model):  
    """
    Models should be decouple (inheritance rarely used)
    Otherwise basic seeming queries return all types in the hierarchy.
    Hence just StructuredNode here.
    """
    uid = UniqueIdProperty()
    name = StringProperty(max_length=MAX_TEXT_LENGTH, required=True)
    objects = RelationshipTo('Object', 'CONTAINS')    
    category = RelationshipTo('Category', 'IN_CATEGORY', cardinality=One)
    COMMUTES = { 'C' : 'Commutes', 'NC' : 'Noncommutative' }
    commutes = StringProperty(choices=COMMUTES, default='C')
    author = StringProperty(max_length=MAX_TEXT_LENGTH)
    date_modified = DateTimeProperty()
    date_created = DateTimeProperty()
    object_count = IntegerProperty(required=True)
    morphism_count = IntegerProperty(required=True)
    
    #def morphism_count(self):
        #count = 0
        #for x in self.all_objects():
            #count += len(x.morphisms)
        #return count
    
    def copy(self, **kwargs):
        copy = Diagram.our_create(**kwargs)
        
        nodes_memo = {}
        
        for x in self.all_objects():
            if x.diagram_index not in nodes_memo:
                x.copy(nodes_memo)
        
        for x in nodes_memo.values():  # BUGFIX: need to consider all nodes added in subcalls, secondly
            copy.objects.connect(x)
            
        copy.save()                    
        return copy
                
    @property
    def commutes_text(self):
        return self.COMMUTES[self.commutes]
    
    #@property
    #def commutes(self):
        #return self.COMMUTES[self.commutative]
    
    #@commutes.setter
    #def commutes(self, text):
        #for key, val in self.COMMUTES.items():
            #if text == val:
                #self.commutative = key
                #break
        #else:
            #raise ValueError(f'There are only {len(self.COMMUTES)} possible options for Diagram.commutes')
    
    @staticmethod
    def our_create(**kwargs):
        diagram = Diagram(**kwargs).save()
        category = get_unique(Category, name='Any category')
        diagram.category.connect(category)
        diagram.date_modified = diagram.date_created = datetime.now()
        diagram.save()  
        return diagram
        
    def quiver_format(self):
        edges = []
        vertices = []
        
        objects = list(self.all_objects())
        objects.sort(key=lambda x: x.diagram_index)        
        
        for o in objects:
            vertices.append(o.quiver_format())
            for f in o.all_morphisms():
                edges.append(f.quiver_format())
                    
        format = [0, len(vertices)]
        format += vertices
        format += edges
        
        return format
    
    @property
    def embed_data(self):
        data = self.quiver_format()
        data = json.dumps(data)
        data = base64.b64encode(data.encode('utf-8')) 
        return data.decode()
    
    def load_from_editor(self, format):
        obs = []
        vertices = format[2:2 + format[1]]
        
        for k,v in enumerate(vertices):
            o = Object.create_from_editor(v, k)
            obs.append(o)
        
        edges = format[2 + format[1]:]
        self.morphism_count = len(edges)
                    
        for k,e in enumerate(edges):
            A = obs[e[0]]
            B = obs[e[1]]
            f = A.morphisms.connect(B, {'diagram_index':k})
            f.load_from_editor(e)
            f.save()
            A.save()    
            
        self.date_modified = datetime.now()
        self.add_objects(obs)               
    
    def all_objects(self):
        results, meta = db.cypher_query(
            f'MATCH (D:Diagram)-[:CONTAINS]->(x:Object) WHERE D.uid="{self.uid}" RETURN x')
        return [Object.inflate(row[0]) for row in results]
        
    def delete_objects(self):
        for o in self.all_objects():
            o.delete()
        self.object_count = 0
        self.morphism_count = 0
        self.save()
        
    def add_objects(self, obs):
        for o in obs:
            self.objects.connect(o)
        self.object_count += len(obs)
        self.save()
        
    @staticmethod
    def get_paths_by_length(diagram_id):
        paths_by_length = \
            f"MATCH (D:Diagram)-[:CONTAINS]->(X:Object), " \
            f"p=(X)-[:MAPS_TO*]->(:Object) " \
            f"WHERE D.uid='{diagram_id}' " \
            f"RETURN p " \
            f"ORDER BY length(p) DESC" 
                
        paths_by_length, meta = db.cypher_query(paths_by_length)        
        return paths_by_length
                          
        ## TODO: test code with doublequote in template_regex ^^^        
        
    @staticmethod
    def build_query_from_paths(paths, query_diagram):
        nodes = {
            # Keyed by Object.diagram_index, value is Object
        }
        rels = {
            # Keyed by Morphism.diagram_index, value is Morphism
        }

        search_query = ''
        
        if paths:                  
            for path in paths:
                path = path[0]   # [0] is definitely needed here
                node = Object.inflate(path.start_node)
                
                search_query += f"(n{node.diagram_index}:Object)"
                
                if node.diagram_index not in nodes:
                    nodes[node.diagram_index] = node
                
                add_query = ''
                
                for rel in path.relationships:
                    rel = Morphism.inflate(rel)
                    
                    if rel.diagram_index not in rels:
                        rels[rel.diagram_index] = rel
                        
                        add_query += f"-[r{rel.diagram_index}:MAPS_TO]->"
                        next_node = rel.end_node()  # BUGFIX: no need to inflate here
                        add_query += f"(n{next_node.diagram_index}:Object)"
                        
                        # BUGFIX: don't forget to add the next node into nodes:
                        if next_node.diagram_index not in nodes:
                            nodes[next_node.diagram_index] = next_node
                
                if add_query:      
                    search_query += add_query
                    
                search_query += ', '
            
            if search_query:
                search_query = search_query[:-2]
                
        else:
            objects = query_diagram.all_objects()
            
            for node in objects:
                if search_query:
                    search_query += ','
                    
                search_query += f"(n{node.diagram_index}:Object)"
                
                if node.diagram_index not in nodes:
                    nodes[node.diagram_index] = node         
            
        return search_query, nodes, rels
    
    @staticmethod
    def build_match_query(query, nodes, rels, template_regexes:dict=None):
        query = "MATCH (D:Diagram)-[:CONTAINS]->(n0:Object)," + query            
        
        if template_regexes is None:
            template_regexes = {
                # Keyed by node or relationship .name property, values are 
                # (template, neo4j regex)
            }

        query += f" WHERE D.object_count={len(nodes)} AND " \
            f"D.morphism_count={len(rels)} AND "
            
        for index, node in nodes.items():
            if node.name not in template_regexes:
                template = tuple(Variable.parse_into_template_gen(node.name))
                regex = Variable.neo4j_regex_from_template(template)
                template_regexes[node.name] = (template, regex)
            else:
                template, regex = template_regexes[node.name]
                
            query += f"n{index}.name =~ '{regex}' AND "
            
        if rels:
            for index, rel in rels.items():
                if rel.name not in template_regexes:
                    template = tuple(Variable.parse_into_template_gen(rel.name))
                    regex = Variable.neo4j_regex_from_template(template)                
                    template_regexes[rel.name] = (template, regex)
                else:
                    template, regex = template_regexes[rel.name]
                    
                query += f"r{index}.name =~ '{regex}' AND "
            
        if nodes or rels:
            query = query[:-5]   # Remove AND      
        
        return query
    
    @property
    def category_name(self):
        return self.category.get().name
    
    @property
    def is_diagram(self):
        return True    
    
    def delete(self):
        # Delete all the outgoing morphisms first:
        self.delete_objects()
        super().delete()    
    


class LogicalRule(StructuredNode, Model):
    uid = UniqueIdProperty()
    name = StringProperty(max_length=MAX_TEXT_LENGTH, required=True)
    author = StringProperty(max_length=MAX_TEXT_LENGTH)
    date_modified = DateTimeProperty()
    date_created = DateTimeProperty()    
    
    diagram_assumptions = RelationshipTo('Diagram', 'ASSUMES_DIAGRAM', cardinality=ZeroOrMore)
    diagram_conclusions = RelationshipTo('Diagram', 'CONCLUDES_DIAGRAM', cardinality=ZeroOrMore)    
    rule_assumptions = RelationshipTo('LogicalRule', 'ASSUMES_RULE', cardinality=ZeroOrMore)
    rule_conclusions = RelationshipTo('LogicalRule', 'CONCLUDES_RULE', cardinality=ZeroOrMore)
    
    assumption_avatar_id = StringProperty()
    conclusion_avatar_id = StringProperty()
    
    @staticmethod
    def our_create(**kwargs):
        rule = LogicalRule(**kwargs)
        rule.save()
        rule.save()
        return rule
    
    @property
    def assumption_embed_data(self):
        if self.assumption_avatar_id is None:
            avatar_diagram = self.diagram_assumptions.all()
        
            if avatar_diagram:
                avatar_diagram = avatar_diagram[0]
                self.assumption_avatar_id = avatar_diagram.uid
                self.save()
            else:
                return ''
            
        avatar_diagram = get_model_by_uid(Diagram, uid=self.assumption_avatar_id)
        
        if avatar_diagram:
            return avatar_diagram.embed_data
        return ''
        
    @property
    def conclusion_embed_data(self):
        if self.conclusion_avatar_id is None:
            avatar_diagram = self.diagram_conclusions.get_or_none()
            if avatar_diagram:
                self.conclusion_avatar_id = avatar_diagram.uid
            else:
                return ''
        avatar_diagram = get_model_by_uid(Diagram, uid=self.conclusion_avatar_id)
        if avatar_diagram:
            return avatar_diagram.embed_data
        return ''

    @property
    def is_diagram(self):
        return False


model_str_to_class = {
    'Category' : Category,
    'Object' : Object,
    'Diagram' : Diagram,
    'LogicalRule' : LogicalRule,
}

MAX_MODEL_CLASS_NAME_LENGTH = max([len(x) for x in model_str_to_class.keys()])

def get_model_class(Model:str):
    if len(Model) > MAX_MODEL_CLASS_NAME_LENGTH:
        return ValueError("You're passing in an unimplemented Model string.")        
    
    if Model not in model_str_to_class:
        raise NotImplementedError(f'Model {Model} has no entry in a certain table.')
    
    Model = model_str_to_class[Model]    
    return Model


def get_model_by_uid(Model, uid:str):
    if len(uid) > 36:
        raise ValueError('That id is longer than a UUID4 is supposed to be.')
    
    if isinstance(Model, str):
        Model = get_model_class(Model)
        
    model = Model.nodes.get_or_none(uid=uid)    
    
    if model is None:
        raise ObjectDoesNotExist(f'An instance of the model {Model} with uid "{uid}" does not exist.')
    
    return model
                    
                    
def get_unique(Model, **kwargs):
    model = Model.nodes.get_or_none(**kwargs)
    
    if model is None:
        model = Model.our_create(**kwargs)
        model.save()
        
    return model
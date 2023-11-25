from django.shortcuts import render, redirect, HttpResponse, \
     HttpResponseRedirect
from .models import Object, Morphism, Category, Diagram, \
     get_model_by_uid, get_unique, LogicalRule
from django.http import JsonResponse
from arrowbee.python_tools import full_qualname
from django.db import OperationalError
from django.core.exceptions import ObjectDoesNotExist
from arrowbee.settings import DEBUG, \
     MAX_USER_EDIT_DIAGRAMS, MAX_DIAGRAMS_PER_PAGE, MAX_TEXT_LENGTH
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static
import base64
import json
import re
from datetime import datetime
from neomodel import db
from arrowbee.variable import Variable

# Create your views here.

def embed_diagram(request, diagram_id):
    if request.method == 'GET':
        diagram = get_model_by_uid(Diagram, uid=diagram_id)
        data = diagram.quiver_format()
        data = json.dumps(data)
        data = base64.b64encode(data.encode('utf-8'))         
        diagram.embed_data = f'{static("")}/quiver/src/index.html?q={data.decode()}&embed'

        context = {
          'diagram' : diagram
      }

        return render(request, 'database_app/embed_diagram.html', context)   


def load_diagram_from_database(request, diagram_id):
    try:
        if request.method == 'GET':
            diagram = get_model_by_uid(Diagram, uid=diagram_id)
            json_str = json.dumps(diagram.quiver_format())

            return HttpResponse(json_str, content_type='text/plain; charset=utf8')

    except Exception as e:
        return redirect('error', f'{full_qualname(e)}: {str(e)}')


@login_required   
def save_diagram_to_database(request, diagram_id:str):
    try:
        if request.method != 'POST': #or not request.headers.get("contentType", "application/json; charset=utf-8"):
            raise OperationalError('You can only use the POST method to save to the database.')            
        user = request.user.username

        diagram = get_model_by_uid(Diagram, uid=diagram_id)

        if diagram is None:
            raise ObjectDoesNotExist(f'There exists no diagram with uid "{diagram_id}".') 

        if diagram.author != user:
            raise OperationalError(
             f'The diagram with id "{diagram_id}" is already checked out by {diagram.author}')                

        body = request.body.decode('utf-8')

        if body:
            try:
                data = json.loads(body)                
            except json.decoder.JSONDecodeError:
                # For some reason, empty diagrams are resulting in the body as a URL str (not JSON)
                data = [0, 0]               
        else:
            data = [0, 0]

        diagram.delete_objects()
        diagram.load_from_editor(data)        

        messages.success(request, f'🌩️ Successfully saved diagram (id={diagram.uid}) to the database!')

        return JsonResponse(
          'Wrote the following data to the database:\n' + str(data), safe=False)

    except Exception as e:
        #if DEBUG:
            #raise e
        return JsonResponse({'error_msg' : f'{full_qualname(e)}: {str(e)}'})


def test(request):
    return render(request, 'test.html')


@login_required
def rule_editor(request, rule_id:str):
    try:
        session = request.session      
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, uid=rule_id)

        if rule:
            if rule.name == '':
                raise ValueError('Diagram name must not be empty.')

            if not rule.author:
                rule.author = user
                session.save()
            else:
                if rule.author != user:
                    raise OperationalError(
                   f'The rule with id "{rule_id}" is already checked out by {rule.author}')         
        else:
            raise ObjectDoesNotExist(f'There exists no rule with uid "{rule_id}".')

        context = {
          'rule_name' : rule.name,
         'rule_id' : rule.uid,
         'assumptions' : list(rule.diagram_assumptions.all()) + list(rule.rule_assumptions.all()),  # TODO can we take out the list() ctor here?
         'conclusions' : list(rule.diagram_conclusions.all()) + list(rule.rule_conclusions.all()), 
         'after_delete' : request.path,
      }

        messages.success(request, f'🌩️ Successfully loaded logical rule (id={rule.uid}) from the database!')
        return render(request, 'database_app/rule_editor.html', context)  

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')   
        return redirect('home')


RuleID, IsAssumption = range(2)

@login_required
def diagram_editor(request, diagram_id:str):
    try:
        session = request.session
        user = request.user.username

        if 'diagram ids' not in session:
            session['diagram ids'] = []
        else:
            if diagram_id not in session['diagram ids'] and \
            len(session['diagram ids']) == MAX_USER_EDIT_DIAGRAMS:
                raise OperationalError(f"You can't have more than {MAX_USER_EDIT_DIAGRAMS} diagrams checked out.")

        if 'adding to rule' in session:
            include_add_to_rule = True
            rule_id = session['adding to rule'][RuleID]
        else:
            include_add_to_rule = False
            rule_id = None

        diagram = get_model_by_uid(Diagram, uid=diagram_id)

        if diagram:
            if not diagram.author:
                diagram.author = user
                session['diagram ids'].append(diagram_id)
                session.save()
            else:
                if diagram.author != user:
                    raise OperationalError(
                   f'The diagram with id "{diagram_id}" is already checked out by {diagram.author}')
        else:
            raise ObjectDoesNotExist(f'There exists no diagram with uid "{diagram_id}".')                

        category = diagram.category.single()

        context = {
          'diagram_name' : diagram.name,
         'category_name' : category.name,
         'diagram_id' : diagram.uid,
         'include_add_to_rule' : include_add_to_rule,
         'rule_id' : rule_id,
      }

        messages.success(request, f'🌩️ Successfully loaded diagram (id={diagram.uid}) from the database!')
        return render(request, 'database_app/diagram_editor.html', context)  

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')   
        return redirect('home')


@login_required
def create_new_rule(request):   
    rule = LogicalRule.our_create(name="Untitled Rule")
    rule.author = request.user.username
    rule.save()
    return redirect('rule_editor', rule.uid)   

@login_required
def create_new_diagram(request):   
    diagram = Diagram.our_create(name="Untitled Diagram", object_count=0, morphism_count=0)
    diagram.author = request.user.username
    diagram.save()
    return redirect('diagram_editor', diagram.uid)

identity_regex = re.compile(r'\\text{id}_\{(?P<subscr>.+)\}|\\text\{id\}_(?P<subscr1>.)|\\text\{id\}')


@login_required
def rename_diagram(request, diagram_id):
    try:
        diagram = get_model_by_uid(Diagram, diagram_id)

        if diagram is None:
            raise ObjectDoesNotExist(f'There exists no diagram with uid "{diagram_id}".') 

        if diagram.author != request.user.username:
            raise OperationalError(
             f'The diagram with id "{diagram_id}" is already checked out by {diagram.author}')                

        new_name = request.body.decode('utf-8')
        new_name = new_name[1:-1]        # Remove weirdly appearing quotes 
        new_name = new_name.replace('\\\\', '\\')

        if len(new_name) > MAX_TEXT_LENGTH:
            raise OperationalError(f'Length of string, {len(new_name)} is greater than {MAX_TEXT_LENGTH}')

        diagram.name = new_name
        diagram.save()

        messages.success(request, f'🤓️ Successfully renamed diagram in the database!')
        response = { 'success' : True }

    except Exception as e:
        messages.error(request, f'😢 {full_qualname(e)}: {str(e)}')
        response = { 'success': False }

    return JsonResponse(response)



@login_required #Dev Change Starts Here
def rename_rule(request, rule_id):
    try:
        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with id "{rule_id}".') 

        if rule.author != request.user.username:
            raise OperationalError(
             f'The rule with id "{rule_id}" is already checked out by {rule.author}')                

        new_name = request.body.decode('utf-8')
        new_name = new_name[1:-1]        # Remove weirdly appearing quotes 
        new_name = new_name.replace('\\\\', '\\')

        if len(new_name) > MAX_TEXT_LENGTH:
            raise OperationalError(f'Length of string, {len(new_name)} is greater than {MAX_TEXT_LENGTH}')

        rule.name = new_name
        rule.date_modified = datetime.now()
        rule.save()

        messages.success(request, f'🤓️ Successfully renamed rule in the database!')
        response = { 'success' : True }

    except Exception as e:
        messages.error(request, f'😢 {full_qualname(e)}: {str(e)}')
        response = { 'success': False }

        # TODO DEBUG REMOVE
        raise e

    return JsonResponse(response) #DevChange Ends here




@login_required
def reassign_category(request, diagram_id):
    try:
        diagram = get_model_by_uid(Diagram, diagram_id)

        if diagram is None:
            raise ObjectDoesNotExist(f'There exists no diagram with uid "{diagram_id}".') 

        if diagram.author != request.user.username:
            raise OperationalError(
             f'The diagram with id "{diagram_id}" is already checked out by {diagram.author}')                

        new_category = request.body.decode('utf-8')
        new_category = new_category[1:-1]      
        new_category = new_category.replace('\\\\', '\\')

        if len(new_category) > MAX_TEXT_LENGTH:
            raise OperationalError(f'Length of string, {len(new_category)} is greater than {MAX_TEXT_LENGTH}')

        old_category = diagram.category.get()
        new_category = get_unique(Category, name=new_category)
        diagram.category.reconnect(old_category, new_category)
        diagram.save()

        messages.success(request, f'🌌️ Successfully re-assigned the category of this diagram in the database!')
        response = { 'success' : True }

    except Exception as e:
        messages.error(request, f'😢 {full_qualname(e)}: {str(e)}')
        response = { 'success': False }

    return JsonResponse(response)


@login_required
def functor_diagram(request, diagram_id=None):
    try:
        notation = request.POST.get('functor_notation')
        codomain_category = request.POST.get('functor_codomain')

        if len(notation) > MAX_TEXT_LENGTH:
            raise OperationalError(f'Notation string is too long.')

        if len(codomain_category) > MAX_TEXT_LENGTH:
            raise OperationalError(f'Codomain category string is too long.')

        diagram = get_model_by_uid(Diagram, uid=diagram_id)

        diagram_name = f'Functorial image of diagram "{diagram.name}" under {notation}'
        image_diagram = diagram.copy(name=diagram_name)
        image_diagram.author = request.user.username

        for X in image_diagram.all_objects():
            if X.name: 
                parts = []

                for name in X.name.split("="):
                    parts.append(notation.replace(r'\cdot', name))

                X.name = "=".join(parts)
                X.save()

            for f in X.all_morphisms():
                if f.name:
                    parts = []

                    for name in f.name.split("="):

                        id_match = identity_regex.match(name)

                        if id_match:
                            subscr1 = id_match.group('subscr1')

                            if subscr1:
                                subscr1 = notation.replace(r'\cdot', subscr1)
                                parts.append(f"\\text{{id}}_{{{subscr1}}}")

                            else:
                                subscr = id_match.group('subscr')

                                if subscr:
                                    subscr = notation.replace(r'\cdot', subscr1)                     
                                    parts.append(f"\\text{{id}}_{{{subscr}}}")

                        else:
                            parts.append(notation.replace(r'\cdot', name))

                        f.name = "=".join(parts)
                        f.save() 

        image_diagram.save()

        return redirect('diagram_editor', image_diagram.uid)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')


@login_required
def add_assumption(request, rule_id:str):
    try:         
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with id="{rule_id}".') 

        if user != rule.author:
            raise PermissionError(f'You are not the author of this rule.  Contact {rule.author}.')

        request.session['adding to rule'] = (rule_id, True)

        next_page = request.GET.get('next', None)

        if next_page:
            return HttpResponseRedirect(next_page)
        else:
            return redirect('home')
    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')      


@login_required
def add_conclusion(request, rule_id:str):
    try:      
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with id="{rule_id}"')

        if user != rule.author:
            raise PermissionError(f'Yo are not the author of this rule. Contact {rule.author}.')

        request.session['adding to rule'] = (rule_id, False)

        next_page = request.GET.get('next', None)

        if next_page:
            return HttpResponseRedirect(next_page)
        else:
            return redirect('home')
    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {stre(e)}')
        return redirect('home')

@login_required
def delete_assumption(request, assumption_id:str, rule_id:str):
    try:         
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with uid "{rule_id}".')

        if user != rule.author:
            raise PermissionError(f'You are not the author of this rule.  Contact {rule.author}.')

        assumption = rule.diagram_assumptions.get(uid=assumption_id)

        if assumption:
            rule.diagram_assumptions.disconnect(assumption)
        else:
            assumption = rule.rule_assumptions.get(uid=assumption_id)

            if assumption:
                rule.rule_assumptions.disconnect(assumption)
            else:
                raise ObjectDoesNotExist(f'The assumption with id="{assumption_id}" is not part of rule with id="{rule_id}".')

        rule.date_modified = datetime.now()   
        rule.save()

        return redirect('rule_editor', rule_id)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')      

@login_required
def delete_conclusion(request, conclusion_id:str, rule_id:str):
    try:         
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with uid "{rule_id}".')

        if user != rule.author:
            raise PermissionError(f'You are not the author of this rule.  Contact {rule.author}.')

        conclusion = rule.diagram_conclusions.get(uid=conclusion_id)

        if conclusion:
            rule.diagram_conclusions.disconnect(conclusion)
        else:
            conclusion = rule.rule_conclusions.get(uid=conclusion_id)

            if conclusion:
                rule.rule_assumptions.disconnect(conclusion)
            else:
                raise ObjectDoesNotExist(f'The conclusion with id="{conclusion_id}" is not part of rule with id="{rule_id}".')

        rule.date_modified = datetime.now()   
        rule.save()

        return redirect('rule_editor', rule_id)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')            


@login_required   
def add_diagram_to_rule(request, diagram_id:str):
    try:         
        rule_info = request.session.get('adding to rule', None)

        if rule_info:
            rule_id, is_assumption = rule_info      
            rule = get_model_by_uid(LogicalRule, uid=rule_id)

            if rule:
                diagram = get_model_by_uid(Diagram, uid=diagram_id)

                if diagram == None:
                    raise ObjectDoesNotExist(f'There exists no diagram with uid "{diagram_id}".')

                if is_assumption:
                    rule.diagram_assumptions.connect(diagram)
                else:
                    rule.diagram_conclusions.connect(diagram)

                rule.date_modified = datetime.now()
                rule.save()     

                messages.success(request, 'Successfully added a diagram to this rule.')            
                del request.session['adding to rule']        # BUGFIX: don't set to None here, delete instead

                return redirect('rule_editor', rule_id)

        else:
            raise OperationalError("You are not currently editing a rule.")

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')      


@login_required
def set_assumption_avatar(request, assumption_id:str, rule_id:str):
    try:         
        user = request.user.username

        rule = get_model_by_uid(LogicalRule, rule_id)

        if rule is None:
            raise ObjectDoesNotExist(f'There exists no rule with uid "{rule_id}".')

        if user != rule.author:
            raise PermissionError(f'You are not the author of this rule.  Contact {rule.author}.')

        assumption = rule.diagram_assumptions.get(uid=assumption_id)

        if assumption:
            rule.assumption_avatar_id = assumption_id
        else:
            assumption = rule.rule_assumptions.get(uid=assumption_id)

            if assumption:
                rule.assumption_avatar_id = assumption_id
            else:
                raise ObjectDoesNotExist(f'The assumption with id="{assumption_id}" is not part of rule with id="{rule_id}".')

        rule.date_modified = datetime.now()   
        rule.save()

        messages.success(request, f'Successfully set the assumption avatar of this rule to the given diagram.')

        return redirect('rule_editor', rule_id)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')       


order_by_text_map = {
    'name' : 'name',
   'modified' : 'date modified',
   'created' : 'date created',
}

order_dir_text_map = {
    'asc' : 'Ascending',
   'desc' : 'Descending',
}

@login_required
def my_diagram_list(request, order_by, order_dir, page_num):   
    if order_by not in order_by_text_map or order_dir not in order_dir_text_map:
        return

    diagrams = Diagram.nodes

    sign = '-' if order_dir == 'desc' else ''

    if order_by == 'created':
        diagrams = diagrams.order_by(sign + 'date_created') 
    elif order_by == 'modified':
        diagrams = diagrams.order_by(sign + 'date_modified')
    elif order_by == 'name':
        diagrams = diagrams.order_by(sign + 'name')

    diagrams = diagrams.filter(author=request.user.username)

    diagrams = list(diagrams)  
    num_diagrams = len(diagrams)

    N = MAX_DIAGRAMS_PER_PAGE
    num_pages = int(num_diagrams / N) + (1 if num_diagrams % N != 0 else 0)

    if num_pages != 0:
        page_num %= num_pages

        if page_num < num_pages - 1 or num_diagrams % N == 0:
            diagrams = diagrams[N*page_num : N*(page_num + 1)]
        else:
            diagrams = diagrams[N*page_num : N*page_num + num_diagrams % N]

    else:
        page_num = 0 

    context = {
       'diagrams': diagrams,
      'num_pages': num_pages,
      'page_num': page_num,
      'next_page' : page_num + 1,
      'prev_page' : page_num - 1,
      'order_by' : order_by,
      'order_dir' : order_dir,
      'order_by_text' : order_by_text_map[order_by],
      'order_dir_text' : order_dir_text_map[order_dir],
   }

    return render(request, "database_app/my_diagram_list.html", context)


@login_required
def my_rule_list(request, order_by:str, order_dir:str, page_num:int):   
    if order_by not in order_by_text_map or order_dir not in order_dir_text_map:
        return

    rules = LogicalRule.nodes

    sign = '-' if order_dir == 'desc' else ''

    if order_by == 'created':
        rules = rules.order_by(sign + 'date_created') 
    elif order_by == 'modified':
        rules = rules.order_by(sign + 'date_modified')
    elif order_by == 'name':
        rules = rules.order_by(sign + 'name')

    rules = rules.filter(author=request.user.username)

    num_rules = len(rules)

    N = MAX_DIAGRAMS_PER_PAGE
    num_pages = int(num_rules / N) + (1 if num_rules % N != 0 else 0)

    if num_pages != 0:
        page_num %= num_pages

        if page_num == num_pages - 1:
            rules = rules[N*page_num:N*page_num + num_rules % N]
        else:
            rules = rules[N*page_num : N*(page_num + 1)]

    else:
        page_num = 0 

    context = {
       'rules': rules,
      'num_pages': num_pages,
      'page_num': page_num,
      'next_page' : page_num + 1,
      'prev_page' : page_num - 1,
      'order_by' : order_by,
      'order_dir' : order_dir,
      'order_by_text' : order_by_text_map[order_by],
      'order_dir_text' : order_dir_text_map[order_dir],
   }

    return render(request, "database_app/my_rule_list.html", context)         


@login_required
def delete_diagram(request, diagram_id:str):   
    try:         
        user = request.user.username

        diagram = get_model_by_uid(Diagram, diagram_id)

        if diagram is None:
            raise ObjectDoesNotExist(f'There exists no diagram with id "{diagram_id}".')

        if user != diagram.author:
            raise PermissionError(f'You are not the author of this diagram.  Contact {diagram.author}.')

        diagram.delete()

        messages.success(request, f'Successfully deleted diagram from the database.')       
        return redirect('my_diagram_list', 'created', 'asc', 0)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        return redirect('home')         


@login_required
def diagram_search(request, diagram_id:str, 
                   order_by:str, order_dir:str, page_num:int):
    try:
        query_diagram:Diagram = get_model_by_uid(Diagram, uid=diagram_id)
        num_objs = query_diagram.object_count
        num_arrows = query_diagram.morphism_count      

        if query_diagram is None:
            raise ObjectDoesNotExist(f'There exists no diagram with id "{diagram_id}".')

        paths = Diagram.get_paths_by_length(diagram_id)
        query, nodes, rels = Diagram.build_query_from_paths(paths, query_diagram)
        query = Diagram.build_match_query(query, nodes, rels)

        return_list = ','.join(f'n{i}.name' for i in range(len(nodes)))
        if rels:
            return_list += ','
            return_list += ','.join(f'r{i}.name' for i in range(len(rels)))
        return_list += ',n0.uid'

        query += f' RETURN {return_list}'
        results, meta = db.cypher_query(query)

        #results = [Object.inflate(row[0]) for row in results]

        # Cypher query that gets the diagram that "owns" this Object n0.

        base_query = \
          f"MATCH (D:Diagram)-[:CONTAINS]->(X:Object) " \
         f"WHERE X.uid='"    

        diagrams = []
        N = len(nodes)

        for result in results:
            # Check all results that are actually variable-isomorphic with a more restrictive
            # but more exact (and much longer regex contained in Variable class).

            var_memo = {}

            for k in range(len(nodes)):            
                target = result[k]  
                source = nodes[k].name  

                if not Variable.consistent_mapping_exists(source, target, var_memo):
                    break
            else:
                for k in range(N, N + len(rels)):
                    target = result[k]
                    source = rels[k - N].name

                    if not Variable.consistent_mapping_exists(source, target, var_memo):
                        break
                else:
                    query = base_query + f"{result[-1]}' RETURN D"
                    diagram, _ = db.cypher_query(query)
                    if diagram:
                        diagram = Diagram.inflate(diagram[0][0])
                        diagrams.append(diagram)

        N = MAX_DIAGRAMS_PER_PAGE
        num_diagrams = len(diagrams)      
        num_pages = int(num_diagrams / N) + 1  
        page_num %= num_pages

        # TODO limit in first results query and pagination properly

        context = {
          'diagram_id': diagram_id,        # Of the query diagram
         'diagrams': diagrams,
         'num_pages': num_pages,
         'page_num': page_num,
         'next_page' : page_num + 1,
         'prev_page' : page_num - 1,
         'order_by' : order_by,
         'order_dir' : order_dir,
         'order_by_text' : order_by_text_map[order_by],
         'order_dir_text' : order_dir_text_map[order_dir],
      }

        return render(request, "database_app/diagram_search.html", context)

    except Exception as e:
        messages.error(request, f'{full_qualname(e)}: {str(e)}')
        raise e

    #return redirect('home')               

from .atomic_symbol import AtomicSymbol as Atom
import re
from .keyword import Keyword, greek_variable_regex

class Variable:
    base_parser = Atom.alphabet_parser
    subscript_parser = re.compile(r"\{-?[0-9]+\}|[0-9]")  # Put longest alternative first
    prime_parser = re.compile(r"'+")
    # Couldn't get longest match to work when using {0, 2} in a regex, so had to split up into
    # multiple regexes and somewhat manually parse.    
    complete_variable_parser = re.compile(f"(?P<base>\\({greek_variable_regex})|[a-zA-Z])(_(?P<sub>\{{-?\d\}}|\d))?(?P<prime>'*)")   
    neo4j_variable_match_regex = "(\\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\\'*"
    
    def __init__(self, base=None, prime=None, sub=None):
        self.base = base
        self.prime = prime
        self.sub = sub
                
    def __repr__(self):
        return 'Variable("' + str(self) + '")'
    
    def __str__(self):
        res = self.base
        if self.prime:
            res += self.prime
        if self.sub:
            res += '_'
            if len(self.sub) > 1:
                res += '{' + self.sub + '}'
            else:
                res += self.sub
        return res
    
    def __hash__(self):
        return hash(repr(self))
    
    def __eq__(self, x):
        if isinstance(x, Variable):
            return self.base == x.base and self.sub == x.sub and self.prime == x.prime
        return False
        
    # Returns template as a list of Keywords, literal str's, and Variable.
    @staticmethod
    def parse_into_template_gen(text:str):
        #
        def parse_text_region(start, end):
            var_match = None
            
            for var_match in Variable.complete_variable_parser.finditer(text, pos=start, endpos=end):
                end1 = var_match.start()
                
                if end1 > start:
                    yield text[start : end1]
                
                yield Variable(base=var_match.group('base'), sub=var_match.group('sub'), prime=var_match.group('prime'))      
                
                start = var_match.end()
                
            if var_match is not None:
                start = var_match.end()
                
                if start < end:
                    yield text[start:end]
            else:
                yield text            
        
        if text == '\\cdots':
            
            DEBUG_ME = True
            
        start = 0
        end = None
        keyword_match = None
        
        for keyword_match in Keyword.regex.finditer(text):
            text_len = keyword_match.start() - start
            end = start + text_len
            
            if text_len:
                yield from parse_text_region(start, end)
                    
            yield Keyword(keyword_match.group())
            start = keyword_match.end()    
            
        if keyword_match is None:   # Probably just a single variable
            yield from parse_text_region(0, len(text))
            
        else:            
            start = keyword_match.end()
            
            if len(text) - start > 0:
                yield from parse_text_region(start, len(text))                
                    
    @staticmethod
    def longest_match(text, pos):
        """
        Find the longest variable starting from pos, within text
        """        
        match = Variable.complete_variable_parser.match(text, pos=pos)
        
        if match:
            return match.group(), match.end()
        
        return None, pos                       
    
    @staticmethod
    def flatten_template(template):
        for i in range(len(template)):
            piece = template[i]
            
            if isinstance(piece, (Variable, Keyword)):
                template[i] = str(piece)
                
        return ''.join(template)
    
    @staticmethod
    def subst_vars_into_template(template, var_map):
        for i in range(len(template)):
            piece = template[i]
            if isinstance(piece, Keyword):
                piece = str(piece)
            elif isinstance(piece, Variable):
                if piece in var_map:        # Some variable may not be matched and they're treated as literals
                    template[i] = str(var_map[piece])
        
        return template

    @staticmethod 
    def variable_match_regex(template):
        regex = ''
        var_count = 0    # variables are thus indexed left-to-right within a single name template
        for piece in template:
            if isinstance(piece, (Keyword, str)):
                regex += escape_regex_str(str(piece))
            elif isinstance(piece, Variable):
                regex += f"(?P<V{var_count}>.+)"    # Use Vi here to not confuse with ni, ri used in querying code
                var_count += 1
            elif isinstance(piece, str):
                regex += escape_regex_str(piece)
            else:
                assert(0)
        # Exact match desired hence ^ $:
        #return re.compile('^' + regex + '$'), var_count
        return re.compile(regex), var_count
    
    @staticmethod
    def consistent_mapping_exists(source:str, target:str, var_memo:dict) -> bool:  
        target_template = Variable.parse_into_template_gen(target)
        
        for piece in Variable.parse_into_template_gen(source):
            try:
                target_piece = next(target_template)
            except StopIteration:
                return False
            
            if isinstance(piece, Variable):
                if not isinstance(target_piece, Variable):
                    return False
            elif piece != target_piece:         # Raw text & Keyword type pieces
                return False                
            
        try:
            piece = next(target_template)
            return False
        except StopIteration:
            return True
    
        
        
        ##
        #def match_var_regions(pos, tpos, kw_start):           
            #for match in Variable.complete_variable_parser.finditer(source, pos=pos, endpos=kw_start):
                #source_var = match.group()
                #var_start = match.start()
                #text_len = var_start - pos
                #target_var_start = tpos + text_len
                
                #if source[pos:var_start] != target[tpos:target_var_start]:
                    #return False
                
                #target_match = Variable.complete_variable_parser.match(target[target_var_start:])
                
                #if target_match:
                    #target_var = target_match.group()                  
                
                    #if not target_match:
                        #return False
                    
                    #if source_var in var_memo:
                        #if var_memo[source_var] != target_var:
                            #return False
                    #else:
                        #var_memo[source_var] = target_var               
                #else:
                    #return False
                
                #pos = match.end()
                #tpos = target_match.end()
                
            #return True
        
        #keyword_match = None        
        #pos = 0
        #tpos = 0
        
        #for keyword_match in Keyword.regex.finditer(source):            
            #keyword_start = keyword_match.start()
            #length = keyword_start - pos   # Length of prefix variable region
            
            #if length:
                ## Var region comes before keyword_match.group() in source string
                #if not match_var_regions(pos, tpos, keyword_start):
                    #return False
            
            #target_match = Keyword.regex.match(target, pos=tpos + length)
            
            #if target_match is None:
                #return False
            
            #if target_match.group() != keyword_match.group():
                #return False
            
            #pos = keyword_match.end()
            #tpos = target_match.end()
                                
        #if keyword_match is None:
            #if not match_var_regions(pos, tpos, len(source)):
                #return False            
        #else:
            #length = len(source) - keyword_match.end()
        
            #if length > 0:
                #if not match_var_regions(pos, tpos, kw_start=len(source)):
                    #return False
        
        ## Made it through the isomorphism gauntlet        
            
        #return True        

    @staticmethod
    def neo4j_regex_from_template(template:tuple) -> str:
        regex = ""
        k = 0
        
        while k < len(template):
            piece = template[k]
            
            if isinstance(piece, Variable):
                j = None
                
                for j in range(k + 1, len(template)):
                    if not isinstance(template[j], Variable):
                        break
                    
                piece = Variable.neo4j_variable_match_regex  
                
                if j is None:                         
                    k += 1
                else:
                    var_seq_length = j - k 
                    
                    if var_seq_length > 1:
                        piece = f'({piece}){{{var_seq_length}}}'                        
                    k = j
                    
                regex += piece
                    
            elif isinstance(piece, Keyword):
                regex += Variable.neo4j_escape_regex(str(piece))
                k += 1
            else:  # str
                regex += Variable.neo4j_escape_regex(piece)
                k +=1 
                
        return regex   
    
    @staticmethod
    def neo4j_escape_regex(string:str) -> str:
        return string.replace('\\', r'\\\\')    
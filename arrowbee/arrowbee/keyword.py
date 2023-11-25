import re

greek_variable_regex = "partial|Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega|varGamma|varDelta|varTheta|var(Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega)|alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|var(epsilon|kappa|theta|pi|rho|sigma|phi"


class Keyword:
    regex = re.compile(r'(\\text|\\textbf|\\rm|\\bf)\{[^\}]+\}|\\\(?!' + greek_variable_regex + ')[a-zA-Z]+')
    
    def __init__(self, keyword:str):
        self._string = keyword
        
    def __repr__(self):
        return 'Keyword("' + str(self) + '")'
    
    def __str__(self):
        return self._string
    
    def __eq__(self, x) -> bool:
        if isinstance(x, Keyword):
            return self._string == x._string
        return False
        
    


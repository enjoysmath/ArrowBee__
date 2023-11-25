## Arrow Bee

A community of creators of arrow-based mathematics (Category Theory, Homological Algebra, Topos theory).  In arrow-based mathematics,
we usually do not take elements or do heavy analysis on polynomial expressions, for example.   Although, there is a notion of [generalized element](https://en.wikipedia.org/wiki/Element_(category_theory))
in a category.

---

### Developer Setup

1. #### Download and setup [Neo4j Desktop](https://neo4j.com/download/):
      * Make sure to copy the license key given after you enter in your name, email, etc.
      * Specify location `C:\Neo4jDesktop` during install.  
      * Select "Run Neo4j" and finish.
      * Click thorugh the defaults.  
      * On "Software registration" page paste in the license key your copied previously.  
      * Click the "next" button and wait for Neo4j to setup itself in the background.
      * Delete the "Example Project" and wait a while.
      * Install any updates if a dialog should pop up.
      * Click "+ New Project".
      * Add a "Local DBMS" and name it _ArrowBee_.
      * Set the password to _ArrowBee_ as well for convenience and since this isn't the secure live site.
      * Make sure "Version" is set to the latest version listed.
      * Click "Create" and let it run a while in the background.
      * Hover over the newly created "ArrowBee" DB and click the "Start" that appears.  Wait.
      * Now that it's running hover over "ArrowBee" DB and click "Open (in Neo4j browser)".
      * Here you can experiement with Cypher queries and see the query result graph visually or textually.

2. Clone this repository with your local git / TortoiseGit.
     * Open a command line in the project's directory.
     * On the command line type `pip install -r requirements.txt`.
     * Let it finish installing all the Python library prequisites in the background.
4.

_Notes: 
In step 1 you set up a local database on your machine, but represents the actual Neo4j database that will be either on AuraDB (Neo4j company itself) or GrapheneDB.  Another option is self-hosting, but it's lacking managaged mode & auto-scalability etc._


### Critical

1. Restyle these pages (using BSS):
      http://127.0.0.1:8000/accounts/social/signup/

2. Thum.io integration for screenshots.

3. Finish a component with EnjoysMath such as the LogicalRule editor.  This is fullstack I mean.  Learn how to do this from me for this project.

4. Finish your own component start to finish that is critical to the site.

5. Fix bugs when deploying to Heroku.

6. Base diagram edit permissions of of User instance id not username!!! Because there could be several users with same name.

7. Single node diagram causes crash in diagram search. 

8.  Move these Morphism properties all into a "blob" or a single string in the Neo4j database.
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


###  Logical Rule Editor 
1. Allows the user to specify a collection of assumptions as well as a collection of conclusions.   
2. The logic here is that all the assumptions logically AND'd together logically IMPLY the conclusions (AND'd together).
3. If the implication is supposed to be bidirectional (" if and only if "), then that is taken care of prior to entering the editor.  
    If the user clicked "New Bidirectional Rule" then the enter will show a LaTeX-rendered $\iff$ to be clear.
4. So the user can add / delete from the two lists.  These buttons actually change things on the database and then reload the page.
5. The rule's name at the top (largest heading) needs to be editable when you hover it (an button appears).   
    I will show you how to re-use the same dialog and hover button as we did in the diagram editor.
6.  A user will also be able to add a rule to either list above (Rules containing Rules as well as Diagrams).


### Diagram Search 
1. User clicks a button (Magnifying glass) after drawing and saving a diagram.
2. The view searches the database for any Diagrams that are precisely isomorphic to this diagram in an exact way.
3. Got it working mostly.
4. Debug it.

### Rule Search
1. This one is more tricky.  Its like a union of the above (Diagram Search) except assumptions can be either a LogicalRule or a Diagram and so on recursively.
2. Try to get it done in as few db queries as possible - in other words fastest running code is best.


---

### Not Critical

1. Get twitter running - once the website is live
2. Also get working with SE sites (stack exchange) OAuth services
3. Center buttons on the home screen.  Hard to do with our current layout.
4. Use local KaTeX for page content math rendering not CDN.
5. Shorten / Optimize these queries:
  "MATCH (n1:Object)-[r3:MAPS_TO]->(n0:Object)-[r0:MAPS_TO]->(n2:Object)-[r1:MAPS_TO]->(n3:Object)-[r2:MAPS_TO]->(n4:Object), (n1:Object), (n0:Object), (n2:Object), (n1:Object), (n0:Object), (n3:Object), (n2:Object), (n1:Object), (n0:Object) WHERE n1.name =~ '\cdots' AND n0.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND n2.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND n3.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND n4.name =~ '\cdots' AND r3.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND r0.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND r1.name =~ '(\[a-zA-Z]+|[a-zA-Z])(_(\{-?\d\}|\d))?\'*' AND r2.name =~ '' RETURN n0.name,n1.name,n2.name,n3.name,n4.name,r0.name,r1.name,r2.name,r3.name,n0.uid"
  
  for example, the isolated node paths are redundant here because they already occur in the first listed path cypher (before first comma).
  
  

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

import networkx as nx
import srsly
import matplotlib.pyplot as plt
from pyvis.network import Network
from IPython.display import HTML, display
from tqdm import tqdm
import pandas as pd
from math import log

st.set_page_config(layout="wide")

# =========== SETTING UP ==================
db = list(srsly.read_jsonl('data/snomed_db.jsonl'))
ids = [c['conceptId'] for c in db]

def getConceptById(id):
    for c in db:
        if c['conceptId'] == id:
            return c

def getConceptByName(name):
    for c in db:
        if c['fsn']['term'] == name:
            return c
        
def coloring(node_list, color, g):
    node_list_out = node_list.copy()

    for n in node_list:    
        node_list_out.extend([i for i in list(g.neighbors(n)) if i not in node_list_out])

    for n in node_list_out:
        g.get_node(n)['color'] = color

@st.cache
def load_data():
	df_freq = pd.read_csv('data/snomed_id2name.csv') # frequency
	df_freq['fullname'] = None
	for i in range(len(df_freq)):
		id = df_freq.loc[i, 'smid']
		c = getConceptById(str(id))
		if c:
			df_freq.loc[i, 'fullname'] = c['fsn']['term']

	df_wc = pd.read_csv('data/snomed_mean_word_count.csv', names=['fullname', 'wc'], header=0) # word count

	# find mutual terms
	freq = list(df_freq.fullname)
	tinas = list(df_wc.fullname)
	df_rm = df_freq[df_freq['freq'] > 1 ] # filter out disease that has only 1 letter
	inter = set(df_rm.fullname).intersection(set(tinas))
	return df_freq, df_wc, inter

df_freq, df_wc, inter = load_data()

def construct_graph(ids, inter, df_wc, scale):
	G1 = nx.Graph()
	for id in tqdm(ids):
		node = getConceptById(str(id)) # get a concept by its id
		root = node['fsn']['term']
		if root not in list(inter):
			continue
			
		G1.add_node(root, label=node['pt']['term'], title=node['pt']['term'], 
					size=df_wc.loc[df_wc.fullname==root, 'wc'].values[0]*scale)
		
		for i, r in enumerate(node['relationships']):
			if r['characteristicType'] == 'STATED_RELATIONSHIP':
				child = r['target']
				child_id = child['id']
				child_name = child['fsn']['term']

				# Construct graph
				if child_name in list(inter):
					G1.add_node(child_name, label=child['pt']['term'], title=child['pt']['term'],
								size=df_wc.loc[df_wc.fullname==child_name, 'wc'].values[0]*scale)
					G1.add_edge(root,child_name)
	return G1


# ============== GRAPH ==================
G = construct_graph(ids, inter, df_wc, scale=1/4)
g = Network(height='1000px', width='100%', notebook=True)
g.from_nx(G)

# --- coloring ---

# IRDs
rare = {
    'diseases':[
		'Hereditary macular dystrophy (disorder)',
		'Hereditary retinal dystrophy (disorder)',
		'X-linked retinitis pigmentosa (disorder)',
		'Retinitis pigmentosa (disorder)',
		"Oguchi's disease (disorder)",
		'Congenital hereditary endothelial dystrophy (disorder)', 
		'Dominant hereditary optic atrophy (disorder)'
  	],
    'color': '#dd4b39' # red
}

# Cataract
cata = {
    'diseases': [
		'Cataract (disorder)', 'Congenital cataract (disorder)',
		'Subcapsular cataract (disorder)'
	],
    'color': '#eb34bd' # magneta
}

# Glaucoma
glau = {
	'diseases': [
    'Glaucoma (disorder)', 'Secondary glaucoma (disorder)',
    'Open-angle glaucoma (disorder)', 'Primary angle-closure glaucoma (disorder)'
    ],
	'color': '#00ff1e' # green
}
    
# Infectious
infe = {
    'diseases': [
    'Uveitis (disorder)',
    'Conjunctivitis (disorder)', 'Viral conjunctivitis (disorder)',
    'Keratitis (disorder)', 'Scleritis (disorder)', 'Keratoconjunctivitis (disorder)', 'Varicella (disorder)',
    'Chorioretinitis (disorder)', 'Retinitis (disorder)', 'Iritis (disorder)',
    'Endophthalmitis (disorder)', 'Anterior uveitis (disorder)'
    ], # and anything with `uveitis` in the name
	'color': '#162347'
}

coloring(rare['diseases'], rare['color'], g)
coloring(cata['diseases'], cata['color'], g) 
coloring(glau['diseases'], glau['color'], g) 
coloring(infe['diseases'], infe['color'], g) 

# --- Show and save graph visualizer ---
g.show('snomed_wc.html')


# ============ APP ============
st.title("MEH SNOMED Knowledge Graph")

with st.sidebar:
    st.selectbox(
        'Graph type by:', 
        ('Letter length', 'Node connectivity'))
    
    scale = st.slider(
		label='Select scale (node size/scale)',
     	min_value=1, max_value=10, 
      	value=4, step=1)
    
st.write('Number of nodes: ', G.number_of_nodes())
st.write('Number of edges: ', G.number_of_edges())

# Graph
HtmlFile = open("snomed_wc.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
components.html(source_code, height=1000)


'''TODO
	degree of neigbors
 	filter nodes based on frequency
  	label having freq and wc info 
   	interact with disease group (disease list, color, etc.)
    plot according to freq or wc
    search nodes --> show in graph
'''
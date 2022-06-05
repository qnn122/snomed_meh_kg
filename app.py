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
import altair as alt

st.set_page_config(layout="wide")


# =========== SETTING UP ==================
db = list(srsly.read_jsonl('data/snomed_db.jsonl'))
ids = [c['conceptId'] for c in db]
df_freq = pd.read_csv('data/snomed_id2name.csv') # frequency
df_wc = pd.read_csv('data/snomed_mean_word_count.csv', 
                    names=['fullname', 'wc'], header=0).sort_values(by='wc', ascending=False) # word count

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
		try:
			node_list_out.extend([i for i in list(g.neighbors(n)) if i not in node_list_out])
		except:
			continue

	for n in node_list_out:
		try:
			g.get_node(n)['color'] = color
		except:
			continue

def load_data(df_freq, T_freq):
	df_freq['fullname'] = None
	for i in range(len(df_freq)):
		id = df_freq.loc[i, 'smid']
		c = getConceptById(str(id))
		if c:
			df_freq.loc[i, 'fullname'] = c['fsn']['term']

	# find mutual terms
	freq = list(df_freq.fullname)
	tinas = list(df_wc.fullname)
	df_rm = df_freq[df_freq['freq'] > T_freq] # filter out disease that has only 1 letter
	inter = set(df_rm.fullname).intersection(set(tinas))
	return df_freq, df_wc, inter

def construct_graph(ids, inter, df_wc, scale):
	G = nx.Graph()
	for id in tqdm(ids):
		node = getConceptById(str(id)) # get a concept by its id
		root = node['fsn']['term']
		if root not in list(inter):
			continue
		
		root_wc = df_wc.loc[df_wc.fullname==root, 'wc'].values[0]
		G.add_node(root, label=node['pt']['term'], 
             		title=f"{node['pt']['term']}\n{int(root_wc)}", 
					size=root_wc*scale)
		
		for i, r in enumerate(node['relationships']):
			if r['characteristicType'] == 'STATED_RELATIONSHIP':
				child = r['target']
				child_id = child['id']
				child_name = child['fsn']['term']

				# Construct graph
				if child_name in list(inter):
					child_wc = df_wc.loc[df_wc.fullname==child_name, 'wc'].values[0]
					G.add_node(child_name, label=child['pt']['term'], 
                				title=f"{child['pt']['term']}\n{int(child_wc)}",
								size=child_wc*scale)
					G.add_edge(root,child_name)
	return G

def update_size(g, scale):
    for node in g.nodes:
        g.get_node(node['id'])['size'] /= scale
        
    
# ============== GRAPH ==================
def make_graph_visualiser():
	G = construct_graph(ids, inter, df_wc, scale=1)
	g = Network(height='1000px', width='100%')
	g.from_nx(G)
	#g.show('snomed_wc.html')
	return g, G

def coloring_all(g):
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
	return g


# ============ APP ============
st.title("MEH SNOMED Knowledge Graph")

with st.sidebar:
    #st.selectbox(
    #    'Graph type by:', 
    #    ('Letter length', 'Node connectivity'))
    
    min_freq = int(min(list(df_freq.freq.values)))
    max_freq = int(max(list(df_freq.freq.values))/10)
    T_freq = st.slider(
		label='Select the frequency cutoff',
     	min_value=min_freq, max_value=1000, 
      	value=500, step=1)
    
    scale = st.slider(
		label='Select scale (node size/scale)',
     	min_value=1, max_value=10, 
      	value=4, step=1)
    
    
# -----------
st.markdown("### **About**")
st.write("This knowledge graph illustrates the average length of clinical letters associated with "\
    	"some of the most common eye diseases found in Moorfields Eye Hospital database. "\
        "The diseases are connected by their semantic relationship defined in SNOMED CT. "\
        "A larger node means that the disease was often described in more detailed in the clinical letters. "\
        "A subset of four disease groups was highlighted: `Cataract` (magneta), `Glaucoma` (green), `Infectious` (black), "\
        "and `Hereditary` (red, you might need to lower the frequency cutoff to see this group)")


# ------------
st.markdown('### **The Graph**')

# load data, change color and update size
df_freq, df_wc, inter = load_data(df_freq, T_freq)
g, G = make_graph_visualiser()
g = coloring_all(g)
update_size(g, scale)

# Show graph
components.html(g.generate_html(), height=1000)

st.write('Number of nodes: ', G.number_of_nodes())
st.write('Number of edges: ', G.number_of_edges())


# ------------
st.markdown("### **Statistics**")
# info

# chart and stuff
col1, col2,  = st.columns(2)

with col1:
	freq_chart = alt.Chart(df_freq[:20]).mark_bar().encode(
		y=alt.Y('smname', sort='-x'),
		x='freq'
	).properties(height=400)
	st.write('Distribution of disease clinical letters')
	st.altair_chart(freq_chart, use_container_width=True)

with col2:
	wc_chart = alt.Chart(df_wc[:20]).mark_bar().encode(
		y=alt.Y('fullname', sort='-x'),
		x='wc'
	).properties(height=400)
	st.write('Distribution of average length of clinical letters')
	st.altair_chart(wc_chart, use_container_width=True)


# ------------
st.markdown('### **Contact**')
st.write('Please send your feedback to: quang.nguyen.21@ucl.ac.uk (Quang Nguyen). Your comments are highly appreciated.')

# TODO
# 	degree of neigbors
#  	filter nodes based on frequency
#   label having freq and wc info 
#  	interact with disease group (disease list, color, etc.)
#  	plot according to freq or wc
#   search nodes --> show in graph

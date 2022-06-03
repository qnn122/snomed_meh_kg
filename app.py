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

# =============================
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
        
# =============================
df = pd.read_csv('data/snomed_id2name.csv') # frequency
df['fullname'] = None
for i in range(len(df)):
    id = df.loc[i, 'smid']
    c = getConceptById(str(id))
    if c:
        df.loc[i, 'fullname'] = c['fsn']['term']

df2 = pd.read_csv('data/snomed_mean_word_count.csv', names=['fullname', 'wc'], header=0) # word count

# find mutual terms
freq = list(df.fullname)
tinas = list(df2.fullname)
df_rm = df[df['freq'] > 1 ] # filter out disease that has only 1 letter
inter = set(df_rm.fullname).intersection(set(tinas))


G1 = nx.Graph()
scale = 1/4
for id in tqdm(ids):
    node = getConceptById(str(id)) # get a concept by its id
    root = node['fsn']['term']
    if root not in list(inter):
        continue
        
    G1.add_node(root, label=node['pt']['term'], title=node['pt']['term'], 
                size=df2.loc[df2.fullname==root, 'wc'].values[0]*scale)
    
    for i, r in enumerate(node['relationships']):
        if r['characteristicType'] == 'STATED_RELATIONSHIP':
            child = r['target']
            child_id = child['id']
            #child_name = child['fsn']['term'] # chose 'fsn' or 'pt'
            child_name = child['fsn']['term']

            # print info
            #print(f"{i}\t| {child_id}\t| {child_name}")
            #print(f"\t\t\t  {r['characteristicType']}")
            #print()

            # Construct graph
            if child_name in list(inter):
                G1.add_node(child_name, label=child['pt']['term'], title=child['pt']['term'],
                            size=df2.loc[df2.fullname==child_name, 'wc'].values[0]*scale)
                G1.add_edge(root,child_name)

g1 = Network(height='1500px', width='100%', notebook=True)
g1.from_nx(G1)

# coloring

# ------ rare diseases---------
rare = [
    'Hereditary macular dystrophy (disorder)',
    'Hereditary retinal dystrophy (disorder)',
    'X-linked retinitis pigmentosa (disorder)',
    'Retinitis pigmentosa (disorder)',
    "Oguchi's disease (disorder)",
    'Congenital hereditary endothelial dystrophy (disorder)', 
    'Dominant hereditary optic atrophy (disorder)']
coloring(rare, '#dd4b39', g1) # red

    
# ------- Cataract -----------
cata = [
    'Cataract (disorder)', 'Congenital cataract (disorder)',
    'Subcapsular cataract (disorder)']
coloring(cata, '#eb34bd', g1) # magneta


# ------- glaucoma -----------
glau = [
    'Glaucoma (disorder)', 'Secondary glaucoma (disorder)',
    'Open-angle glaucoma (disorder)', 'Primary angle-closure glaucoma (disorder)']
coloring(glau, '#00ff1e', g1) # green

    
# ------- infect -----------
infe = [
    'Uveitis (disorder)',
    'Conjunctivitis (disorder)', 'Viral conjunctivitis (disorder)',
    'Keratitis (disorder)', 'Scleritis (disorder)', 'Keratoconjunctivitis (disorder)', 'Varicella (disorder)',
    'Chorioretinitis (disorder)', 'Retinitis (disorder)', 'Iritis (disorder)']
coloring(infe, '#162347', g1) # black

g1.show('snomed_wc.html')


# ============ APP ============
st.title("MEH SNOMED Knowledge Graph")

# General info
st.write('Number of nodes: ', G1.number_of_nodes())
st.write('Number of edges: ', G1.number_of_edges())

# Graph
HtmlFile = open("snomed_wc.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
components.html(source_code, height=1200, width=1800)

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

st.title("MEH SNOMED Knowledge Graph")

HtmlFile = open("snomed_wc.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
components.html(source_code, height=2000, width=1000)
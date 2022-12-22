#!/bin/bash
python3 -m pip install networkx
curl -sL https://raw.githubusercontent.com/dchassin/plot_glm/main/src/plot_glm.py -o $(gridlabd --version=install)/share/gridlabd/plot_glm.py

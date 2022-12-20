"""Convert GridLAB-D model to a network plot image

Options:
  -B|--base (float)     Set the power base (default 1kW)
  -i|--input=FILE       Set the input file name (GLM or JSON)
  --install             Install as a GridLAB-D tool (must be used alone)
  -L|--layout (str)     Choose the layout method (default "kamada_kawai")
  -N|--nodeshape (str)  Set the node shape (default "o")
  -Z|--nodesize (int)   Set the node size (default 25)
  -o|--output=FILE      Set the output file name
  -S|--show (bool)      Show the image (default False)
  -t|--timeout (int)    Set the activity timeout in seconds (default None)
  -T|--title (bool or str) Enable or set the image title (default False)
  -W|--workdir (str)    Set the working directory (default ".")

Generate a network plot from a GLM or JSON file.  The 'base' option sets
the power base used to set the width of links, which is logarithmic with
the power base as width 1 and factors of 10 increasing the width by 1.
The layout can be selected from among the layout allowed by the networkx
module.  The nodeshape option specifies the shape of nodes. The nodesize 
is an integer. The show option enables immediately showing a plot. The
workdir option specifies the working folder.

If the input file is not JSON, it is automatically converted to JSON. If
the output file is not specified and the show option is not given, then
the output file is set to the input file with the extension ".png".

If no options are given and the folder "autotest" is found, then the
autotest procedure is run on all the GLM files found in the folder.  The
file "validate.txt" is generated by the procedure.
"""
import os, sys
import subprocess
import json
import math
import networkx
import matplotlib.pyplot as plt
import traceback

BASENAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]
INPUTFILE = None
OUTPUTFILE = None
SHOWPLOT = False
WORKDIR = "."
OUTPUT = ""
ERRORS = ""
BASEPOWER = 1e3
GRAPHLAYOUT = "kamada_kawai"
TIMEOUT = None # TODO
TITLE = False
NODESIZE = 25
NODESHAPE = 'o'

E_OK = 0
E_FAILED = 1
E_SYNTAX = 2

RETURNCODE = 0

class ConverterException(Exception):
    pass

def error(msg,code=None):
    print(f"ERROR [{BASENAME}]: {msg}")
    if type(code) is int:
        exit(code)
    elif type(code) is Exception:
        raise code(msg)

def color(phases):
    r = 255 if "A" in phases else 0
    g = 255 if "B" in phases else 0
    b = 255 if "C" in phases else 0
    if [r,g,b] == [255,255,255]:
        return "black"
    else:
        return f"#{r:02x}{g:02x}{b:02x}"

def shape(phases):
    if "S" in phases:
        return "o" 
    elif "D" in phases:
        return "^"
    else:
        return "v"

def convert(inputfile=None,
        outputfile=None,
        showplot=False,
        jsonfile=None,
        workdir="."):

    if not inputfile:
        inputfile = INPUTFILE

    if not outputfile:
        outputfile = OUTPUTFILE

    if not inputfile.endswith(".json"):
        if not jsonfile:
            jsonfile = os.path.splitext(inputfile)[0] + ".json"
        result = subprocess.run(["gridlabd",
                "-W",workdir,
                "-I",inputfile,
                "-o",jsonfile],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT)
        global OUTPUT
        global ERRORS
        OUTPUT = ""
        ERRORS = ""
        if result.returncode:
            ERRORS = result.stdout.decode()
            return result.returncode
        else:
            OUTPUT = result.stdout.decode()
        inputfile = jsonfile

    if not outputfile and not showplot:
        outputfile = os.path.splitext(inputfile)[0] + ".png"

    # print(f"convert(inputfule={inputfile},ouputfile={outputfile},showplot={showplot},jsonfile={jsonfile},workdir={workdir})")

    with open(f"{workdir}/{inputfile}",'r') as fh:
        
        glm = json.load(fh)
        G = graph(glm,figsize=(10,7))
        if TITLE:
            if TITLE == True:
                title = os.path.splitext(os.path.basename(inputfile))[0]
            else:
                title = TITLE
                print("TITLE =",title)
            plt.suptitle(title)
        if outputfile:
            plt.savefig(outputfile)
        if showplot:
            plt.show()
        return E_OK
    return E_FAILED

def graph(glm,**kwargs):
    G = networkx.Graph()
    link = []
    node = []
    objects = glm['objects']
    idlist = {}
    for name,data in objects.items():
        idlist[name] = data['id']
    for name,data in objects.items():
        if 'from' in data and 'to' in data:
            link.append(idlist[name])
            from_node = idlist[data['from']]
            to_node = idlist[data['to']]
            if from_node not in node:
                node.append(from_node)
                phases = objects[data['from']]['phases']
                G.add_node(from_node,
                    color = color(phases),
                    edge = "black" if "N" in phases else "white",
                    shape = shape(phases))
            if to_node not in node:
                node.append(to_node)
                phases = objects[data['to']]['phases']
                G.add_node(to_node,
                    color = color(phases),
                    edge = "black" if "N" in phases else "white",
                    shape = shape(phases))
            weight = math.log10(abs(complex(data["power_out"]\
                        .split()[0]).real/BASEPOWER)+10)
            if weight <= 0:
                raise ConverterException(f"{name}: weight<=0; power = {data['power_out']}")
            G.add_edge(from_node, to_node,
                    color = color(data["phases"]),
                    weight = weight)

    plt.figure(**kwargs)
    edge_colors = networkx.get_edge_attributes(G,'color').values()
    edge_weights = networkx.get_edge_attributes(G,'weight').values()
    node_colors = networkx.get_node_attributes(G,'color').values()
    node_shapes = networkx.get_node_attributes(G,'shape').values()
    node_edges = networkx.get_node_attributes(G,'edge').values()
    networkx.draw(G,pos=getattr(networkx,GRAPHLAYOUT+"_layout")(G),
        node_color = node_colors,
        node_size = NODESIZE,
        node_shape = NODESHAPE, #['o' for x in node_shapes],#list(node_shapes),
        edge_color = edge_colors,
        width = list(edge_weights))
    return G

def validate():
    tested = 0
    failed = 0
    TESTDIR = WORKDIR + "/autotest"
    with open("validate.txt","w") as fh:
        for file in os.listdir(TESTDIR):
            if not file.endswith(".glm"):
                continue
            outputfile = f"{TESTDIR}/{file.replace('.glm','.png')}"
            print("Testing",file,flush=True,end='... ')
            if os.path.exists(outputfile):
                print("FOUND")
                tested += 1
                continue
            try:
                if convert(file,
                        outputfile=outputfile,
                        workdir=TESTDIR):
                    failed += 1
                    print("*** TEST",file,"FAILED\n" + ERRORS,file=fh,flush=True)
                    print("",file=fh,flush=True)
                    print("FAILED")
                else:
                    print("OK")
                    print("*** TEST",file,"OK\n" + OUTPUT,file=fh,flush=True)
                    print("",file=fh,flush=True)
            except Exception as err:
                print("EXCEPTION")
                print("*** TEST",file,"EXCEPTION\n",file=fh,flush=True)
                traceback.print_exception(err,file=fh)
                print("",file=fh,flush=True)
                failed += 1
            finally:
                tested += 1
    print(tested,"tested")
    print(failed,"failed")
    print(f"{(100-(100*failed)/tested):.0f}% passing")
    return (E_FAILED if failed else E_OK)

def install():
    if os.system(f"cp {sys.argv[0]} $(gridlabd --version=install)/share/gridlabd") != 0:
        error("install failed")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        spec = arg.split("=")
        if len(spec) == 1:
            tag = spec[0]
            value = True
        elif len(spec) == 2:
            tag = spec[0]
            value = spec[1]
        else:
            tag = spec[0]
            value = "=".join(spec[1:])
        if tag in ["--install"]:
            if sys.argv[1] != tag:
                error("--install must be used alone",E_SYNTAX)
            RETURNCODE = install()
            exit(RETURNCODE)
        elif tag in ["-S","--show"]:
            SHOWPLOT = value
        elif tag in ["-W","--workdir"]:
            WORKDIR = value
        elif tag in ["-L","--layout"]:
            GRAPHLAYOUT = value
        elif tag in ["-B","--base"]:
            BASEPOWER = float(value)
        elif tag in ["-t","--timeout"]:
            TIMEOUT = int(value)
        elif tag in ["-T","--title"]:
            TITLE = value            
        elif tag in ["-i","--input"]:
            INPUTFILE = value
        elif tag in ["-o","--output"]:
            OUTPUTFILE = value
        elif tag in ["-N","--nodeshape"]:
            NODESHAPE = value
        elif tag in ["-Z","--nodesize"]:
            NODESIZE = int(value)
        elif tag in ["-h","--help","help"]:
            print(__doc__)
            exit(E_OK)
        else:
            error(f"option '{arg}' is invalid",1)

    if len(sys.argv) == 1 or not INPUTFILE:

        if os.path.exists(WORKDIR+"/autotest"):
        
            print("Validating in folder",WORKDIR+"/autotest")
            RETURNCODE = validate()
        
        else:
        
            print("Syntax:",
                os.path.splitext(os.path.basename(sys.argv[0]))[0],
                "[OPTIONS ...]")
            RETURNCODE = E_SYNTAX

    else:

        RETURNCODE = convert(INPUTFILE,OUTPUTFILE,SHOWPLOT)

    exit(RETURNCODE)
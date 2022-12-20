# plot_glm

This utility may be used standalone or installed as a GridLAB-D tool.

## Quick install

~~~
curl -sL https://raw.githubusercontent.com/dchassin/plot_glm/main/install.sh | bash
~~~

## Standalone use

Run the following command

~~~
bash$ python3 -m plot_glm [OPTIONS...]
~~~

For help, run `python3 -m plot_glm help`.

## GridLAB-D tool

To install as a GridLAB-D tool, run

~~~
bash$ python3 -m plot_glm --install
~~~

To run the tool from GridLAB-D command line:

~~~
bash$ gridlabd plot_glm [OPTIONS...]
~~~

To run the tool from a GLM file

~~~
#plot_glm [OPTIONS...]
~~~

To plot the network as currently loaded in GLM, run

~~~
#write "my_file.json"
#plot_glm -i=my_file.json -o=my_file.png
~~~

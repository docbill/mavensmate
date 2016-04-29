# docbill/mavensmate
A docker container to run mavensmate in sublime-text-3 with the specified workspace.

## Overview

This is just a container to avoid the pains of installing mavensmate 
natively.
 
## Quick Start

 
If you have already have docker working you can start mavensmate as easily as:

	[ -d ~/workspace ] || mkdir ~/workspace
	xhost local:root
	docker run -i --net=host --rm -e "DISPLAY=$DISPLAY" -e "HOME=$HOME" -v $HOME:$HOME:z docbill/mavensmate

-or- If you wish to restrict mavensmate to a particular workspace:

	[ -d ~/workspace ] || mkdir ~/workspace
	xhost local:root
	docker run -i --net=host --rm -e "DISPLAY=$DISPLAY" -v "$HOME/workspace/:/workspace/:z" docbill/mavensmate

Please note: Mavensmate will not automatically install if you have an existing .config/sublime-text-2 or .config/mavensmate folder.

For windows this was a bit more complicated.  I had to make sure Xwin (from
cygwin) was started with the -listen tcp option, and that security was 
disabled.  Once that was done the following command worked:

	docker run -i --rm -e DISPLAY=172.31.253.119:0 -v /d/cygwin64/home/docbi/workspace/:/workspace/:z docbill/mavensmate

Where my ip address is 172.31.253.119, and the folder I wanted the workspace in
was D:\cygwin64\home\docbi\workspace\



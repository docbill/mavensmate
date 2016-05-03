# docbill/mavensmate
A docker container to run mavensmate in sublime-text-3 with the specified workspace.

## Overview

This is just a container to avoid the pains of installing mavensmate 
natively.
 
## Quick Start

If you have already have docker working you can start sublime-text-3 as easily as:

	[ -d ~/workspace ] || mkdir ~/workspace
	xhost local:root
	docker run -i --net=host --rm -v /var/lib/sss:/var/lib/sss:ro -v /tmp:/tmp:z -p 7777:7777 -e "DISPLAY=$DISPLAY" -e "HOME=$HOME" -v "$HOME:$HOME:z" docbill/mavensmate

-or- If you wish to restrict sublime-text-3 to a particular workspace:

	[ -d ~/workspace ] || mkdir ~/workspace
	xhost local:root
	docker run -i --net=host --rm -v /var/lib/sss:/var/lib/sss:ro -v /tmp:/tmp:z -p 7777:7777 -e "DISPLAY=$DISPLAY" -e /workspace/:/workspace/:z" docbill/mavensmate

Please note: It is recommended that you remove any existing .config/sublime-text-2 or .config/sublime-text-3 folders.

You probably will not be able to use many of the mavens mates features on a host OS such as Windows without "/var/lib/sss".


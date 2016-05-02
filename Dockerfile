FROM docbill/sublime-text-3
MAINTAINER Bill C Riemers https://github.com/docbill

ADD config /opt/sublime_text/config
RUN chmod -R 755 /opt/sublime_text/config && \
	cd /opt/sublime_text/config/sublime-text-3/Packages && \
	git clone https://github.com/joeferraro/MavensMate-SublimeText.git -b v6 'MavensMate'


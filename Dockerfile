FROM docbill/sublime-text-3
MAINTAINER Bill C Riemers https://github.com/docbill

ADD config /opt/sublime_text/config
RUN chmod -R 755 /opt/sublime_text/config



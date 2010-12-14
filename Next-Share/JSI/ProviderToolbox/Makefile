MAKEFILE_VERSION = 0.1
MAKEFILE_DIR = $(shell pwd)
SVN_REPOSITORY = /home/dusan/delo/src/p2p-next-svn/ProviderToolbox

help:
	@echo "***** help "
	@echo "***** Version of the Makefile: $(MAKEFILE_VERSION) *****"
	@echo "Targets: "
	@echo " - help               (default), outputs this help"
	@echo " - svn-diff           see the differences between repositories"
	@echo " - svn-update         copy the differences to svn dir"
	@echo " - clean              removes unnecessary ProviderToolbox files"

svn: 
	@echo "***** svn: valid svn commands - svn-diff and svn-update"

svn-%: clean
	@echo "***** $@: $(subst svn-,,$@) differences between JSI CVS and SVN repository"
	@if test $@ != svn-diff -a $@ != svn-update; then \
		echo "Unknown target $@! Quit."; \
		exit 1; \
	fi
	@SVN_DIR=$(SVN_REPOSITORY); \
	cd $(MAKEFILE_DIR); \
	if test ! -d CVS; then \
		echo "You are not in CVS repository! Quit."; \
	fi; \
	for f in $(shell find . ! \( -name CVS -prune -o -name var -prune \)); do \
		if test -e $$SVN_DIR/$$f; then \
			if test -f $$SVN_DIR/$$f; then \
				diff $$f $$SVN_DIR/$$f > /dev/null; \
				if test $$? -eq 1; then \
					if test $(subst svn-,,$@) = diff; then \
						echo "different: $$f"; \
					else \
						echo "cp: $$f $$SVN_DIR/$$f"; \
						cp $$f $$SVN_DIR/$$f; \
					fi; \
				fi; \
			fi; \
		else \
			if test $(subst svn-,,$@) = diff; then \
				echo "missing: $$f"; \
			else \
				echo "cp missing: $$f $$SVN_DIR/$$f"; \
				cp $$f $$SVN_DIR/$$f; \
			fi; \
		fi; \
	done

clean:
	@echo "***** clean: cleaning stale and python compiled files"
	@find . -name \*~ -exec rm {} \;
	@find . -name \*pyc -exec rm {} \;
	@find . -name \#\*\# -exec rm {} \;
	@find . -name \.\#\* -exec rm {} \;


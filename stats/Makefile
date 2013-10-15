stats: pyformex-stats.png

pyformex-rev.png: pyformex-releases.fdb
	./create_revision_graph # currently broken

pyformex-stats.png: pyformex-releases.fdb
	./sloc.py

pyformex-commits.log:
	git log --pretty=format:'"%H"  "%cd"' > $@

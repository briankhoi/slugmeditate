# slugmeditate

Docker Setup:
1. Run `docker build -t python-env .`
2. docker run -it --rm -v "$(your path to directory):/app" python-env
	- for mac: docker run -it --rm -v "$PWD:/app" python-env
	- windows: docker run -it --rm -v "/$(pwd | sed 's/^C:\\//; s/\\/\//g'):/app" python-env
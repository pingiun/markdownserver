# markdownserver
Markdownserver uses flask to serve .md files. It also supports github webhooks for auto updating, this is what I use it for.

You can use the following lines in nginx for a uwsgi configuration:
```
location / { 
	try_files $uri @markdownserver; 
}
location @markdownserver {
	include uwsgi_params;
	uwsgi_pass unix:///run/uwsgi/app/markdownserver.socket;
}
```

A sample uwsgi configuration file is included in `markdownserver.xml`.

# Fats
A misspelling of FaaS. Should give a pretty good idea of what this project is about.

Except it actually is a PaaS that lets me quickly deploy my small, easy-to-containerize web applications. It's built on top of Docker and uses Railpack to build containers quickly.

```
docker run -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock -v /var/lib/fats:/var/lib/fats -it fats
```

You can push .tar.gz files with Railpack compatible apps to `/tar-upload` and they'll be auto built and deployed. Fats proxies requests to the deployed apps based on the URL path. For example, if you deploy an app named `myapp`, you can access it at `http://localhost:8000/apps/myapp<:version>/whatever`.
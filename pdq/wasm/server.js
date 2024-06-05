// Copyright (c) Meta Platforms, Inc. and affiliates.

var http = require("http"),
    url = require("url"),
    path = require("path"),
    fs = require("fs")
    port = 9095,
    mimeTypes = {
      "html": "text/html",
      "jpeg": "image/jpeg",
      "jpg": "image/jpeg",
      "png": "image/png",
	    "wasm": "application/wasm",
      "svg": "image/svg+xml",
      "json": "application/json",
      "js": "text/javascript",
      "css": "text/css"
    };

 
http.createServer(function(request, response) {
 
  var uri = url.parse(request.url).pathname, 
  filename = path.join(process.cwd(), uri);

  if (path.normalize(decodeURI(uri)) !== decodeURI(uri)) {
    response.statusCode = 403;
	  response.end();
	  return;
  }
  
  fs.exists(filename, function(exists) {
    if(!exists) {
      response.writeHead(404, { "Content-Type": "text/plain" });
      response.write("404 Not Found\n");
      response.end();
      return;
    }
 
    if (fs.statSync(filename).isDirectory()) 
      filename += '/index.html';
 
    fs.readFile(filename, "binary", function(err, file) {
      if(err) {        
        response.writeHead(500, {"Content-Type": "text/plain"});
        response.write(err + "\n");
        response.end();
        return;
      }
      
      var mimeType = mimeTypes[filename.split('.').pop()];
      
      if (!mimeType) {
        mimeType = 'text/plain';
      }
      
      response.writeHead(200, { "Content-Type": mimeType });
      response.write(file, "binary");
      response.end();
    });
  });
}).listen(parseInt(port, 10));



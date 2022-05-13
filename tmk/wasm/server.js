var http = require("http"),
    url = require("url"),
    path = require("path"),
    fs = require("fs")
    port = 9096,
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
      response.setHeader("Cross-Origin-Opener-Policy","same-origin");
	response.setHeader("Cross-Origin-Embedder-Policy","require-corp");
      response.writeHead(200, { "Content-Type": mimeType });
      response.write(file, "binary");
	
      response.end();
    });
  });
}).listen(parseInt(port, 10));



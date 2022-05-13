let ffmpeg = {};

// This method is used for initializing FFMPEG.
export async function initFFMpeg(fname, tmkfname) {
	const { createFFmpeg, fetchFile } = FFmpeg;
	// create the FFmpeg instance and load it
	ffmpeg = createFFmpeg({ log: true });

	const loadFFMpeg = async () => {
		await ffmpeg.load();
		return true;
	}

	return await loadFFMpeg();
}

export async function getTMKHash(fname, tmkfname) {
	// Call the function for running FFMPEG wasm for converting video file to .rgb.
	runFFMpeg(fname, tmkfname);
}

const runFFMpeg = async function (filename, tmkfilename) {

	const rgbFileName = "output.rgb";

	// Read the file whose hash needs to be calculated.     
	let sourceBytes = FS.readFile(filename);

	// write the mp4 to the FFmpeg file system
	ffmpeg.FS(
		"writeFile",
		filename,
		sourceBytes
	);


	// run the FFmpeg command-line tool, converting the MP4 into rgb
	await ffmpeg.run("-nostdin", "-i", filename, "-s", "64:64", "-an", "-f", "rawvideo", "-c:v", "rawvideo", "-pix_fmt", "rgb24", "-r", "15", rgbFileName);
	// Remove the input file saved in ffmpeg memory
	ffmpeg.FS("unlink", filename);

	// read the MP4 file back from the FFmpeg file system
	const output = ffmpeg.FS("readFile", rgbFileName);
	// Save the .rgb file to emscripten file system.		        
	let stream = FS.open(rgbFileName, 'w+');
	FS.write(stream, output, 0, output.length, 0);
	FS.close(stream);

	console.log("calling the get video hash method");
	var result = Module.ccall(
		'getVideoHash',	// name of C function
		'number',	// return type
		['string'],	// argument types
		[tmkfilename]	// arguments
	);

	if (result == 1) {
		saveTMKFile(tmkfilename);
	}
	else {
		alert('Error occured while generating .tmk  files');
	}
}

const saveTMKFile = (function (tmkfilename) {
	var a = document.createElement("a");
	document.body.appendChild(a);
	a.style = "display: none";
	const blob = new Blob([FS.readFile(tmkfilename)]);
	const url = URL.createObjectURL(blob);
	a.href = url;
	a.download = tmkfilename;
	a.click();
	a.class = "download";
	window.URL.revokeObjectURL(url);

	// Remove the file so that we can free some memory.
	FS.unlink(tmkfilename);
});